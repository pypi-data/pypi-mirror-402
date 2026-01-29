"""
Web Technology Detection Module

Detects web technologies, frameworks, and servers on discovered subdomains
using Wappalyzer fingerprints. Works completely offline - only requires
HTTP access to target servers.
"""

import logging
import socket
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, TYPE_CHECKING
from urllib.error import HTTPError, URLError

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


# Try to import Wappalyzer
try:
    from Wappalyzer import Wappalyzer, WebPage
    WAPPALYZER_AVAILABLE = True
except ImportError:
    WAPPALYZER_AVAILABLE = False
    logger.warning("python-Wappalyzer not installed. Web tech detection will be limited.")


class WebTechDetector(BaseModule):
    """
    Web Technology Detection Module

    Scans discovered subdomains for web services and identifies
    technologies using Wappalyzer fingerprints.

    Works offline - only needs HTTP access to target servers.
    """

    MODULE_NAME = "web_tech"

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        threads: int = 10,
        timeout: float = 5.0,
        ports: List[int] = None,
        **kwargs
    ):
        super().__init__(domain, resolver, timeout=timeout, **kwargs)
        self.threads = threads
        self.ports = ports or [80, 443, 8080, 8443]
        self.web_servers: Dict[str, Dict] = {}  # subdomain -> tech info

        # Initialize Wappalyzer if available
        self.wappalyzer = None
        if WAPPALYZER_AVAILABLE:
            try:
                self.wappalyzer = Wappalyzer.latest()
            except Exception as e:
                logger.warning(f"Failed to initialize Wappalyzer: {e}")

    def _check_http(self, url: str) -> Optional[Dict]:
        """
        Check if URL responds and get basic info

        Returns dict with status, headers, title or None
        """
        try:
            # Create SSL context that doesn't verify certificates
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
            )

            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as response:
                status = response.status
                headers = dict(response.headers)
                content = response.read(50000).decode('utf-8', errors='ignore')

                # Extract title
                title = None
                if '<title>' in content.lower():
                    start = content.lower().find('<title>') + 7
                    end = content.lower().find('</title>')
                    if end > start:
                        title = content[start:end].strip()[:100]

                return {
                    'status': status,
                    'headers': headers,
                    'title': title,
                    'content': content[:10000]  # Limit content for analysis
                }

        except HTTPError as e:
            # Still return info for HTTP errors (403, 404, etc.)
            return {
                'status': e.code,
                'headers': dict(e.headers) if e.headers else {},
                'title': None,
                'content': ''
            }
        except (URLError, socket.timeout, ssl.SSLError, ConnectionError, OSError):
            return None
        except Exception as e:
            logger.debug(f"Error checking {url}: {e}")
            return None

    def _detect_tech_wappalyzer(self, url: str) -> Set[str]:
        """Detect technologies using Wappalyzer"""
        if not self.wappalyzer:
            return set()

        try:
            webpage = WebPage.new_from_url(url, verify=False, timeout=self.timeout)
            results = self.wappalyzer.analyze(webpage)
            return results
        except Exception as e:
            logger.debug(f"Wappalyzer error for {url}: {e}")
            return set()

    def _detect_tech_headers(self, headers: Dict) -> Set[str]:
        """Detect technologies from HTTP headers"""
        technologies = set()

        # Server header
        server = headers.get('Server', headers.get('server', ''))
        if server:
            server_lower = server.lower()
            if 'nginx' in server_lower:
                technologies.add('Nginx')
            if 'apache' in server_lower:
                technologies.add('Apache')
            if 'iis' in server_lower:
                technologies.add('IIS')
            if 'cloudflare' in server_lower:
                technologies.add('Cloudflare')
            if 'gunicorn' in server_lower:
                technologies.add('Gunicorn')
            if 'uvicorn' in server_lower:
                technologies.add('Uvicorn')

        # X-Powered-By
        powered_by = headers.get('X-Powered-By', headers.get('x-powered-by', ''))
        if powered_by:
            powered_lower = powered_by.lower()
            if 'php' in powered_lower:
                technologies.add('PHP')
            if 'asp.net' in powered_lower:
                technologies.add('ASP.NET')
            if 'express' in powered_lower:
                technologies.add('Express')
            if 'next.js' in powered_lower:
                technologies.add('Next.js')

        # Other headers
        if 'X-Drupal' in headers or 'x-drupal' in headers:
            technologies.add('Drupal')
        if 'X-Generator' in headers:
            gen = headers['X-Generator'].lower()
            if 'wordpress' in gen:
                technologies.add('WordPress')
            if 'drupal' in gen:
                technologies.add('Drupal')

        return technologies

    def _detect_tech_content(self, content: str) -> Set[str]:
        """Detect technologies from HTML content"""
        technologies = set()
        content_lower = content.lower()

        # CMS/Frameworks
        patterns = {
            'wp-content': 'WordPress',
            'wp-includes': 'WordPress',
            '/joomla': 'Joomla',
            'drupal.js': 'Drupal',
            'sites/default/files': 'Drupal',
            'magento': 'Magento',
            'shopify': 'Shopify',
            'react': 'React',
            'vue.js': 'Vue.js',
            'angular': 'Angular',
            'jquery': 'jQuery',
            'bootstrap': 'Bootstrap',
            'tailwind': 'Tailwind CSS',
            'laravel': 'Laravel',
            'django': 'Django',
            'flask': 'Flask',
            'spring': 'Spring',
            'rails': 'Ruby on Rails',
            'next.js': 'Next.js',
            'nuxt': 'Nuxt.js',
            'gatsby': 'Gatsby',
        }

        for pattern, tech in patterns.items():
            if pattern in content_lower:
                technologies.add(tech)

        return technologies

    def _scan_subdomain(self, subdomain: str, ip: Optional[str]) -> Optional[Dict]:
        """Scan a single subdomain for web technologies"""
        if self.is_cancelled():
            return None

        result = {
            'subdomain': subdomain,
            'ip': ip,
            'web_servers': [],
            'technologies': set(),
        }

        # Try different ports and protocols
        for port in self.ports:
            if self.is_cancelled():
                break

            protocol = 'https' if port in [443, 8443] else 'http'
            if port in [80, 443]:
                url = f"{protocol}://{subdomain}"
            else:
                url = f"{protocol}://{subdomain}:{port}"

            http_result = self._check_http(url)
            if http_result:
                server_info = {
                    'url': url,
                    'port': port,
                    'status': http_result['status'],
                    'title': http_result.get('title'),
                    'server': http_result['headers'].get('Server', http_result['headers'].get('server')),
                }
                result['web_servers'].append(server_info)

                # Detect technologies
                result['technologies'].update(
                    self._detect_tech_headers(http_result['headers'])
                )
                if http_result.get('content'):
                    result['technologies'].update(
                        self._detect_tech_content(http_result['content'])
                    )

                # Try Wappalyzer for more accurate detection
                if self.wappalyzer:
                    result['technologies'].update(
                        self._detect_tech_wappalyzer(url)
                    )

        if result['web_servers']:
            return result
        return None

    def enumerate(self, known_subs: Dict[str, Optional[str]] = None, **kwargs) -> Dict[str, Optional[str]]:
        """
        Scan subdomains for web technologies

        Args:
            known_subs: Dict of known subdomains to scan

        Returns:
            Dict of subdomains with web services
        """
        if not known_subs:
            logger.info("No subdomains provided for web tech detection")
            return {}

        logger.info(f"Scanning {len(known_subs)} subdomains for web technologies")

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self._scan_subdomain, sub, ip): sub
                for sub, ip in known_subs.items()
            }

            for future in as_completed(futures):
                if self.is_cancelled():
                    break

                result = future.result()
                if result:
                    self.web_servers[result['subdomain']] = result
                    self._add_discovered(result['subdomain'], result.get('ip'))

        logger.info(f"Web tech scan complete: {len(self.web_servers)} web servers found")

        return self.discovered

    def get_web_servers(self) -> Dict[str, Dict]:
        """Get detailed web server information"""
        return self.web_servers

    def get_technologies_summary(self) -> Dict[str, int]:
        """Get summary of detected technologies"""
        tech_count = {}
        for info in self.web_servers.values():
            for tech in info.get('technologies', []):
                tech_count[tech] = tech_count.get(tech, 0) + 1
        return dict(sorted(tech_count.items(), key=lambda x: x[1], reverse=True))

    def format_results(self) -> str:
        """Format results for display"""
        lines = []
        for subdomain, info in sorted(self.web_servers.items()):
            techs = ', '.join(sorted(info.get('technologies', []))) or 'Unknown'
            for server in info.get('web_servers', []):
                lines.append(f"{server['url']} [{server['status']}] - {techs}")
        return '\n'.join(lines)
