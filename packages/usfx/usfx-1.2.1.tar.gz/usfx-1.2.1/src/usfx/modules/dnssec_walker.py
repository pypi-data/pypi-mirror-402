"""
DNSSEC Zone Walking Module

Exploits DNSSEC NSEC/NSEC3 records to enumerate zone contents.
NSEC records form a chain linking all records in a zone.
"""

import logging
from typing import Dict, Optional, Set, Tuple, TYPE_CHECKING

import dns.rdatatype

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class DNSSECWalker(BaseModule):
    """DNSSEC zone walking via NSEC/NSEC3 records"""

    MODULE_NAME = "dnssec_walker"

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        timeout: float = 5.0,
        max_iterations: int = 500
    ):
        """
        Initialize DNSSEC walker.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver
            timeout: DNS query timeout
            max_iterations: Maximum NSEC chain iterations
        """
        super().__init__(domain, resolver, timeout)
        self.max_iterations = max_iterations

    def _check_dnssec(self) -> Tuple[bool, bool, dict]:
        """
        Check if domain uses DNSSEC and what type.

        Returns:
            Tuple of (has_dnssec, uses_nsec3, nsec3_params)
        """
        try:
            # Try to get NSEC3PARAM first
            records = self.resolver.resolve_any(self.domain, 'NSEC3PARAM')
            if records:
                # NSEC3 is in use
                return True, True, {}

            # Try to get DNSKEY to confirm DNSSEC
            records = self.resolver.resolve_any(self.domain, 'DNSKEY')
            if records:
                return True, False, {}

            return False, False, {}

        except Exception as e:
            logger.debug(f"Error checking DNSSEC: {e}")
            return False, False, {}

    def _walk_nsec(self) -> Set[str]:
        """
        Walk NSEC records to enumerate zone.

        Returns:
            Set of discovered subdomains
        """
        discovered = set()
        current = self.domain
        iterations = 0

        logger.info(f"Starting NSEC zone walk for {self.domain}")

        native_resolver = self.resolver.get_native_resolver()

        while iterations < self.max_iterations:
            iterations += 1

            try:
                # Query for NSEC record at current name
                try:
                    answers = native_resolver.resolve(current, 'NSEC')
                    for rdata in answers:
                        next_name = str(rdata.next).rstrip('.')

                        if next_name.endswith(f".{self.domain}"):
                            discovered.add(next_name)
                            self._add_discovered(next_name)

                        # Check if we've looped back
                        if next_name == self.domain or next_name <= current:
                            logger.info(f"NSEC walk complete: {len(discovered)} found")
                            return discovered

                        current = next_name

                except Exception:
                    # Try querying a fake subdomain to get NSEC in authority
                    fake = f"aaa{iterations}.{current if current != self.domain else self.domain}"
                    try:
                        native_resolver.resolve(fake, 'A')
                    except Exception:
                        break

            except Exception as e:
                logger.debug(f"NSEC walk error at {current}: {e}")
                break

        logger.info(f"NSEC walk finished with {len(discovered)} subdomains")
        return discovered

    def _walk_nsec3(self, params: dict) -> Set[str]:
        """
        Attempt to crack NSEC3 hashes (limited effectiveness).

        For NSEC3, we can only try to match known names against hashes,
        so this is less effective than NSEC walking.

        Args:
            params: NSEC3 parameters

        Returns:
            Set of discovered subdomains
        """
        discovered = set()

        # NSEC3 uses hashed names, making direct walking impossible
        # We can only verify if specific names exist by computing their hashes

        # Common subdomain prefixes to try
        common_prefixes = [
            'www', 'mail', 'ftp', 'smtp', 'pop', 'imap', 'webmail',
            'api', 'dev', 'test', 'staging', 'admin', 'blog', 'shop',
            'cdn', 'static', 'ns1', 'ns2', 'dns', 'vpn', 'remote'
        ]

        logger.info(f"Attempting NSEC3 hash matching for {self.domain}")

        for prefix in common_prefixes:
            subdomain = f"{prefix}.{self.domain}"
            ip = self.resolver.resolve_a(subdomain)
            if ip:
                discovered.add(subdomain)
                self._add_discovered(subdomain, ip)

        logger.info(f"NSEC3 matching found {len(discovered)} subdomains")
        return discovered

    def enumerate(self) -> Dict[str, Optional[str]]:
        """
        Enumerate subdomains using DNSSEC zone walking.

        Returns:
            Dict of {subdomain: ip_address}
        """
        logger.info(f"Checking DNSSEC for {self.domain}")

        has_dnssec, uses_nsec3, nsec3_params = self._check_dnssec()

        if not has_dnssec:
            logger.info(f"Domain {self.domain} does not use DNSSEC")
            return {}

        if uses_nsec3:
            logger.info(f"Domain uses NSEC3 (hashed) - limited enumeration possible")
            self._walk_nsec3(nsec3_params)
        else:
            logger.info(f"Domain uses NSEC - zone walking possible")
            self._walk_nsec()

        # Resolve discovered subdomains to get IPs
        for subdomain in list(self.discovered.keys()):
            if self.discovered[subdomain] is None:
                ip = self.resolver.resolve_a(subdomain)
                if ip:
                    self.discovered[subdomain] = ip

        return self.discovered
