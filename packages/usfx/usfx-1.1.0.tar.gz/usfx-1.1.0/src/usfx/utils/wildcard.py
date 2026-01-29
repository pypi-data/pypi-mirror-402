"""
Wildcard DNS Detection

Detects if a domain uses wildcard DNS records (*.domain.com)
which would return valid responses for any subdomain query.
"""

import random
import string
import logging
from typing import Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class WildcardDetector:
    """Detects wildcard DNS configurations"""

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None
    ):
        """
        Initialize wildcard detector.

        Args:
            domain: Target domain
            resolver: Optional custom DNS resolver (uses internal resolver if None)
        """
        self.domain = domain
        self.wildcard_ips: Set[str] = set()
        self.has_wildcard = False

        if resolver:
            self.resolver = resolver
        else:
            from .dns_resolver import InternalDNSResolver
            self.resolver = InternalDNSResolver()

    def _generate_random_subdomain(self, length: int = 16) -> str:
        """Generate a random subdomain that is unlikely to exist"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def detect(self, num_tests: int = 3) -> Tuple[bool, Set[str]]:
        """
        Detect if domain uses wildcard DNS.

        Args:
            num_tests: Number of random subdomain tests to perform

        Returns:
            Tuple of (has_wildcard, wildcard_ips)
        """
        test_results = []

        for _ in range(num_tests):
            random_sub = self._generate_random_subdomain()
            test_domain = f"{random_sub}.{self.domain}"

            ips = self.resolver.resolve_a_all(test_domain)
            test_results.append(ips)

            if ips:
                logger.debug(f"Wildcard test {test_domain} resolved to {ips}")

        # If all tests returned the same non-empty IP set, we have a wildcard
        non_empty_results = [r for r in test_results if r]

        if len(non_empty_results) >= 2:
            # Check if all non-empty results have overlapping IPs
            common_ips = non_empty_results[0]
            for result in non_empty_results[1:]:
                common_ips = common_ips & result

            if common_ips:
                self.has_wildcard = True
                self.wildcard_ips = common_ips
                logger.info(f"Wildcard detected for {self.domain}: {common_ips}")

        return self.has_wildcard, self.wildcard_ips

    def is_wildcard_result(self, ips: Set[str]) -> bool:
        """
        Check if a set of IPs matches the wildcard IPs.

        Args:
            ips: Set of IP addresses to check

        Returns:
            True if the IPs match the wildcard configuration
        """
        if not self.has_wildcard or not self.wildcard_ips:
            return False

        # If the result IPs are a subset of wildcard IPs, it's likely a wildcard result
        return bool(ips & self.wildcard_ips)

    def filter_wildcards(self, subdomains: dict) -> dict:
        """
        Filter out wildcard results from discovered subdomains.

        Args:
            subdomains: Dict of {subdomain: ip_address}

        Returns:
            Filtered dict without wildcard results
        """
        if not self.has_wildcard:
            return subdomains

        filtered = {}
        for subdomain, ip in subdomains.items():
            if ip and ip not in self.wildcard_ips:
                filtered[subdomain] = ip
            elif ip is None:
                filtered[subdomain] = ip

        filtered_count = len(subdomains) - len(filtered)
        if filtered_count > 0:
            logger.info(f"Filtered {filtered_count} wildcard results")

        return filtered
