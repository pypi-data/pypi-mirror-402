"""
Subdomain Validation

Validates discovered subdomains by checking DNS resolution and HTTP accessibility.
"""

import logging
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional, Set, Tuple, TYPE_CHECKING
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

if TYPE_CHECKING:
    from .dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class SubdomainValidator:
    """Validates discovered subdomains"""

    def __init__(
        self,
        timeout: float = 3.0,
        resolver: Optional['InternalDNSResolver'] = None
    ):
        """
        Initialize validator.

        Args:
            timeout: Timeout for validation operations
            resolver: Optional custom DNS resolver
        """
        self.timeout = timeout

        if resolver:
            self.resolver = resolver
        else:
            from .dns_resolver import InternalDNSResolver
            self.resolver = InternalDNSResolver(timeout=timeout)

    def resolve_subdomain(self, subdomain: str) -> Optional[str]:
        """
        Resolve a subdomain to its IP address.

        Args:
            subdomain: Full subdomain to resolve

        Returns:
            IP address or None if unresolvable
        """
        return self.resolver.resolve_a(subdomain)

    def check_http(self, subdomain: str, https: bool = True) -> Optional[int]:
        """
        Check HTTP(S) accessibility of a subdomain.

        Args:
            subdomain: Full subdomain to check
            https: Whether to use HTTPS (default True)

        Returns:
            HTTP status code or None if inaccessible
        """
        protocol = 'https' if https else 'http'
        url = f"{protocol}://{subdomain}/"

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})

            if https:
                response = urlopen(req, timeout=self.timeout, context=ctx)
            else:
                response = urlopen(req, timeout=self.timeout)

            return response.getcode()
        except HTTPError as e:
            return e.code
        except URLError:
            return None
        except Exception:
            return None

    def validate_single(self, subdomain: str, check_http: bool = False) -> dict:
        """
        Validate a single subdomain.

        Args:
            subdomain: Subdomain to validate
            check_http: Whether to also check HTTP accessibility

        Returns:
            Dict with ip, is_active, http_status, https_status
        """
        ip = self.resolve_subdomain(subdomain)
        result = {
            'ip': ip,
            'is_active': ip is not None,
            'http_status': None,
            'https_status': None
        }

        if check_http and ip:
            result['https_status'] = self.check_http(subdomain, https=True)
            if result['https_status'] is None:
                result['http_status'] = self.check_http(subdomain, https=False)

        return result

    def validate_batch(
        self,
        subdomains: Set[str],
        threads: int = 20,
        check_http: bool = False
    ) -> Dict[str, dict]:
        """
        Validate a batch of subdomains.

        Args:
            subdomains: Set of subdomains to validate
            threads: Number of parallel threads
            check_http: Whether to also check HTTP accessibility

        Returns:
            Dict of {subdomain: {ip, is_active, http_status, https_status}}
        """
        results = {}

        def validate_single_wrapper(subdomain: str) -> Tuple[str, dict]:
            return subdomain, self.validate_single(subdomain, check_http)

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(validate_single_wrapper, sub): sub for sub in subdomains}

            for future in as_completed(futures):
                try:
                    subdomain, result = future.result()
                    results[subdomain] = result
                except Exception as e:
                    subdomain = futures[future]
                    logger.error(f"Error validating {subdomain}: {e}")
                    results[subdomain] = {
                        'ip': None,
                        'is_active': False,
                        'http_status': None,
                        'https_status': None
                    }

        return results

    @staticmethod
    def is_valid_domain(domain: str) -> bool:
        """
        Check if a domain string is valid.

        Args:
            domain: Domain to validate

        Returns:
            True if valid domain format
        """
        if not domain or len(domain) > 253:
            return False

        # Check for valid characters
        allowed = set('abcdefghijklmnopqrstuvwxyz0123456789.-')
        if not set(domain.lower()).issubset(allowed):
            return False

        # Check label lengths
        labels = domain.split('.')
        if len(labels) < 2:
            return False

        for label in labels:
            if not label or len(label) > 63:
                return False
            if label.startswith('-') or label.endswith('-'):
                return False

        return True

    @staticmethod
    def extract_subdomain_from_fqdn(fqdn: str, parent_domain: str) -> Optional[str]:
        """
        Extract subdomain part from a fully qualified domain name.

        Args:
            fqdn: Full domain (e.g., 'api.staging.example.com')
            parent_domain: Parent domain (e.g., 'example.com')

        Returns:
            Subdomain part (e.g., 'api.staging') or None
        """
        fqdn = fqdn.lower().rstrip('.')
        parent_domain = parent_domain.lower().rstrip('.')

        if not fqdn.endswith(f".{parent_domain}") and fqdn != parent_domain:
            return None

        if fqdn == parent_domain:
            return None

        return fqdn[:-len(parent_domain) - 1]
