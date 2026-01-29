"""
DNS Zone Transfer (AXFR) Module

Attempts to retrieve full DNS zone data from authoritative nameservers.
About 5-15% of domains still allow zone transfers.
"""

import logging
from typing import Dict, List, Optional, Set, TYPE_CHECKING

import dns.query
import dns.rdataclass
import dns.rdatatype
import dns.zone

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class ZoneTransfer(BaseModule):
    """DNS Zone Transfer (AXFR) enumeration"""

    MODULE_NAME = "zone_transfer"

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        timeout: float = 10.0
    ):
        """
        Initialize zone transfer module.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver
            timeout: Timeout for zone transfer operations
        """
        super().__init__(domain, resolver, timeout)
        self.nameservers: List[str] = []

    def _get_nameservers(self) -> List[str]:
        """
        Get authoritative nameservers for the domain.

        Returns:
            List of nameserver hostnames
        """
        if self.nameservers:
            return self.nameservers

        self.nameservers = self.resolver.resolve_ns(self.domain)

        if self.nameservers:
            logger.info(f"Found {len(self.nameservers)} nameservers for {self.domain}")

        return self.nameservers

    def _resolve_ns_to_ip(self, ns_hostname: str) -> Optional[str]:
        """
        Resolve nameserver hostname to IP address.

        Args:
            ns_hostname: Nameserver hostname

        Returns:
            IP address or None
        """
        return self.resolver.resolve_a(ns_hostname)

    def _attempt_axfr(self, ns_ip: str, ns_hostname: str) -> Set[str]:
        """
        Attempt zone transfer from a specific nameserver.

        Args:
            ns_ip: Nameserver IP address
            ns_hostname: Nameserver hostname for logging

        Returns:
            Set of discovered subdomains
        """
        discovered = set()

        try:
            logger.debug(f"Attempting AXFR from {ns_hostname} ({ns_ip})")

            zone = dns.zone.from_xfr(
                dns.query.xfr(ns_ip, self.domain, timeout=self.timeout)
            )

            for name, node in zone.nodes.items():
                subdomain = str(name)
                if subdomain == '@':
                    continue

                fqdn = f"{subdomain}.{self.domain}"

                # Get A record if available
                ip = None
                try:
                    rdataset = node.find_rdataset(dns.rdataclass.IN, dns.rdatatype.A)
                    if rdataset:
                        ip = str(list(rdataset)[0])
                except KeyError:
                    pass

                discovered.add(fqdn)
                self._add_discovered(fqdn, ip)

            logger.info(f"Zone transfer SUCCESS from {ns_hostname}: {len(discovered)} records")
            return discovered

        except dns.exception.FormError:
            logger.debug(f"Zone transfer REFUSED by {ns_hostname}")
        except dns.query.TransferError as e:
            logger.debug(f"Zone transfer FAILED from {ns_hostname}: {e}")
        except dns.exception.Timeout:
            logger.debug(f"Zone transfer TIMEOUT from {ns_hostname}")
        except Exception as e:
            logger.debug(f"Zone transfer ERROR from {ns_hostname}: {e}")

        return discovered

    def enumerate(self) -> Dict[str, Optional[str]]:
        """
        Attempt zone transfer from all nameservers.

        Returns:
            Dict of {subdomain: ip_address}
        """
        logger.info(f"Attempting zone transfer for {self.domain}")

        nameservers = self._get_nameservers()
        if not nameservers:
            logger.warning(f"No nameservers found for {self.domain}")
            return {}

        all_discovered = set()

        for ns in nameservers:
            ns_ip = self._resolve_ns_to_ip(ns)
            if not ns_ip:
                continue

            discovered = self._attempt_axfr(ns_ip, ns)
            all_discovered.update(discovered)

            if discovered:
                # Zone transfer succeeded, we have complete data
                logger.info(f"Zone transfer succeeded with {len(discovered)} records")
                break

        if not all_discovered:
            logger.info(f"Zone transfer not allowed for {self.domain}")

        return self.discovered

    def is_available(self) -> bool:
        """
        Quick check if zone transfer might be available.

        Returns:
            True if zone transfer appears to be allowed
        """
        nameservers = self._get_nameservers()
        if not nameservers:
            return False

        for ns in nameservers[:2]:  # Only check first 2 NS
            ns_ip = self._resolve_ns_to_ip(ns)
            if not ns_ip:
                continue

            discovered = self._attempt_axfr(ns_ip, ns)
            if discovered:
                return True

        return False
