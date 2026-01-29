"""
Virtual Host Discovery Module

Discovers subdomains by brute-forcing Host headers on known IP addresses.
This technique finds subdomains hosted on the same server that may not
be discoverable through DNS alone.

Note: This module does NOT use external proxy services (unlike the web version).
It connects directly to target IPs, which is suitable for internal network scanning.
"""

import hashlib
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

import requests
from requests.exceptions import RequestException

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class VHostScanner(BaseModule):
    """Discovers virtual hosts through Host header manipulation"""

    MODULE_NAME = "vhost_scanner"

    # Common subdomain prefixes to try
    VHOST_WORDLIST = [
        # Common web apps
        'www', 'app', 'web', 'portal', 'admin', 'panel', 'dashboard',
        'api', 'api2', 'api3', 'rest', 'graphql',
        'blog', 'news', 'cms', 'wordpress', 'wp',
        'shop', 'store', 'cart', 'checkout', 'payment',
        'forum', 'community', 'support', 'help', 'docs', 'documentation',
        'wiki', 'kb', 'knowledgebase',

        # Development
        'dev', 'development', 'staging', 'stage', 'test', 'testing',
        'qa', 'uat', 'sandbox', 'demo', 'preview', 'beta', 'alpha',
        'local', 'localhost', 'debug',

        # Internal
        'internal', 'intranet', 'private', 'corp', 'corporate',
        'employee', 'staff', 'hr', 'finance', 'legal',

        # Security
        'secure', 'login', 'signin', 'auth', 'sso', 'oauth', 'id', 'identity',
        'account', 'accounts', 'my', 'profile', 'user', 'users',

        # Services
        'mail', 'email', 'webmail', 'mx', 'smtp', 'imap', 'pop',
        'ftp', 'sftp', 'files', 'upload', 'download',
        'cdn', 'static', 'assets', 'media', 'img', 'images', 'css', 'js',

        # Infrastructure
        'server', 'host', 'node', 'cluster',
        'db', 'database', 'mysql', 'postgres', 'mongo', 'redis',
        'proxy', 'gateway', 'lb', 'loadbalancer',
        'vpn', 'remote', 'rdp', 'ssh',

        # Monitoring
        'monitor', 'monitoring', 'status', 'health', 'ping',
        'metrics', 'grafana', 'prometheus', 'kibana', 'logs',

        # Geographic/Versioned
        'us', 'eu', 'asia', 'uk',
        'v1', 'v2', 'v3', 'www2', 'www3', 'new', 'old', 'legacy',
    ]

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        threads: int = 10,
        timeout: float = 5.0
    ):
        """
        Initialize vhost scanner.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver
            threads: Number of parallel threads
            timeout: HTTP request timeout
        """
        super().__init__(domain, resolver)
        self.threads = threads
        self.timeout = timeout

        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _get_response_signature(self, response: requests.Response) -> str:
        """Create a signature for a response to detect differences"""
        factors = [
            str(response.status_code),
            str(len(response.content)),
            response.headers.get('Content-Type', ''),
            hashlib.md5(response.content[:1000]).hexdigest(),
        ]
        return '|'.join(factors)

    def _get_baseline(self, ip: str, port: int = 443) -> Tuple[Optional[str], Optional[str]]:
        """Get baseline response for invalid hostname"""
        invalid_host = f'invalid-{hashlib.md5(ip.encode()).hexdigest()[:8]}.{self.domain}'

        try:
            protocol = 'https' if port == 443 else 'http'
            response = requests.get(
                f'{protocol}://{ip}:{port}/',
                headers={'Host': invalid_host},
                timeout=self.timeout,
                allow_redirects=False,
                verify=False
            )
            return self._get_response_signature(response), response.text[:500]
        except:
            return None, None

    def _check_vhost(
        self,
        ip: str,
        hostname: str,
        port: int,
        baseline_sig: Optional[str]
    ) -> Optional[Tuple[str, bool]]:
        """Check if a hostname is a valid virtual host"""
        try:
            protocol = 'https' if port == 443 else 'http'
            response = requests.get(
                f'{protocol}://{ip}:{port}/',
                headers={'Host': hostname},
                timeout=self.timeout,
                allow_redirects=False,
                verify=False
            )

            sig = self._get_response_signature(response)

            # Check if response differs from baseline
            if baseline_sig and sig != baseline_sig:
                is_valid = True

                # Check for generic error pages
                body_lower = response.text.lower()
                error_indicators = [
                    'not found', '404', 'does not exist',
                    'no such', 'invalid host', 'unknown host',
                    'default page', 'welcome to nginx',
                    'apache2 default', 'it works!',
                ]

                for indicator in error_indicators:
                    if indicator in body_lower and response.status_code in [200, 404]:
                        is_valid = False
                        break

                if is_valid and response.status_code in [200, 301, 302, 307, 308, 401, 403]:
                    return hostname, True

            # Even if same as baseline, 200 with good content might be valid
            if response.status_code == 200 and len(response.content) > 1000:
                if '<html' in response.text.lower() or '{' in response.text[:100]:
                    return hostname, True

        except RequestException:
            pass
        except Exception as e:
            logger.debug(f"VHost check error for {hostname}: {e}")

        return None

    def _scan_ip(self, ip: str, ports: List[int] = None) -> Dict[str, Optional[str]]:
        """Scan a single IP for virtual hosts"""
        if ports is None:
            ports = [443, 80]

        discovered = {}

        # Use shortened wordlist for faster scanning
        quick_wordlist = [
            'www', 'app', 'api', 'admin', 'portal', 'dashboard',
            'dev', 'staging', 'test', 'beta', 'demo',
            'mail', 'webmail', 'blog', 'shop', 'store',
            'cdn', 'static', 'assets', 'img', 'media',
            'login', 'auth', 'sso', 'secure',
            'internal', 'intranet', 'vpn', 'remote',
            'db', 'mysql', 'api2', 'v1', 'v2',
        ]

        for port in ports:
            # Get baseline
            baseline_sig, _ = self._get_baseline(ip, port)

            # Test each hostname
            for prefix in quick_wordlist:
                hostname = f'{prefix}.{self.domain}'

                result = self._check_vhost(ip, hostname, port, baseline_sig)
                if result:
                    hostname, _ = result
                    if hostname not in discovered:
                        discovered[hostname] = ip
                        logger.debug(f"VHost discovered: {hostname} on {ip}:{port}")

        return discovered

    def enumerate(
        self,
        known_subdomains: Dict[str, Optional[str]] = None,
        vhost_ips: List[str] = None
    ) -> Dict[str, Optional[str]]:
        """
        Scan known IPs for virtual hosts.

        Args:
            known_subdomains: Dict of subdomains with their IPs
            vhost_ips: Additional IPs to scan for vhosts

        Returns:
            Dict of newly discovered subdomains
        """
        start_time = time.time()
        max_duration = 45  # Maximum 45 seconds for vhost scanning

        if not known_subdomains:
            known_subdomains = {}

        # Extract unique IPs
        unique_ips = set()

        # Add IPs from known subdomains
        for ip in known_subdomains.values():
            if ip and len(unique_ips) < 5:
                unique_ips.add(ip)

        # Add explicitly provided IPs
        if vhost_ips:
            for ip in vhost_ips:
                unique_ips.add(ip)

        if not unique_ips:
            logger.info("No IPs for virtual host scanning")
            return {}

        logger.info(f"Scanning {len(unique_ips)} unique IPs for virtual hosts")

        all_discovered = {}

        # Scan each IP
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self._scan_ip, ip): ip
                for ip in unique_ips
            }

            for future in as_completed(futures, timeout=30):
                if time.time() - start_time > max_duration:
                    logger.info("VHost scanning timeout reached")
                    break

                ip = futures[future]
                try:
                    results = future.result(timeout=10)
                    for hostname, host_ip in results.items():
                        if hostname not in known_subdomains and hostname not in all_discovered:
                            all_discovered[hostname] = host_ip
                            self._add_discovered(hostname, host_ip)
                except Exception as e:
                    logger.debug(f"VHost scan error for {ip}: {e}")

        logger.info(f"Virtual host scanning discovered {len(all_discovered)} new subdomains in {time.time() - start_time:.1f}s")

        return self.discovered

    def brute_force_vhosts(
        self,
        ip: str,
        custom_wordlist: List[str] = None,
        ports: List[int] = None
    ) -> List[str]:
        """
        Brute force virtual hosts on a specific IP.

        Args:
            ip: Target IP address
            custom_wordlist: Optional custom wordlist
            ports: Ports to scan

        Returns:
            List of discovered hostnames
        """
        if ports is None:
            ports = [443, 80]

        wordlist = custom_wordlist or self.VHOST_WORDLIST
        discovered = []

        for port in ports:
            baseline_sig, _ = self._get_baseline(ip, port)

            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {}
                for prefix in wordlist:
                    hostname = f'{prefix}.{self.domain}'
                    futures[executor.submit(
                        self._check_vhost, ip, hostname, port, baseline_sig
                    )] = hostname

                for future in as_completed(futures, timeout=120):
                    try:
                        result = future.result()
                        if result:
                            hostname, _ = result
                            if hostname not in discovered:
                                discovered.append(hostname)
                    except:
                        pass

        return discovered
