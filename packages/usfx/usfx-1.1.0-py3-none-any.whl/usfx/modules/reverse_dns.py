"""
Reverse DNS Sweep Module

Discovers subdomains by performing PTR lookups on IP ranges
associated with the domain.
"""

import ipaddress
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Optional, Set, TYPE_CHECKING

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class ReverseDNS(BaseModule):
    """Reverse DNS (PTR) enumeration"""

    MODULE_NAME = "reverse_dns"

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        timeout: float = 2.0,
        threads: int = 30
    ):
        """
        Initialize reverse DNS module.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver
            timeout: DNS query timeout
            threads: Number of parallel threads
        """
        super().__init__(domain, resolver, timeout)
        self.threads = threads
        self.known_ips: Set[str] = set()

    def _get_domain_ips(self) -> Set[str]:
        """
        Get IP addresses associated with the domain.

        Returns:
            Set of IP addresses
        """
        ips = set()

        # Get A records for main domain and common subdomains
        for subdomain in ['', 'www', 'mail', 'ns1', 'ns2']:
            fqdn = f"{subdomain}.{self.domain}" if subdomain else self.domain
            ip = self.resolver.resolve_a(fqdn)
            if ip:
                ips.add(ip)

        # Get IPs from MX records
        mx_records = self.resolver.resolve_mx(self.domain)
        for priority, mx_host in mx_records:
            ip = self.resolver.resolve_a(mx_host)
            if ip:
                ips.add(ip)

        # Get IPs from NS records
        ns_records = self.resolver.resolve_ns(self.domain)
        for ns_host in ns_records:
            ip = self.resolver.resolve_a(ns_host)
            if ip:
                ips.add(ip)

        logger.info(f"Found {len(ips)} known IPs for {self.domain}")
        return ips

    def _get_ip_range(self, ip: str) -> List[str]:
        """
        Get IP range to scan (/24 network).

        Args:
            ip: Base IP address

        Returns:
            List of IPs in the range
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            if isinstance(ip_obj, ipaddress.IPv4Address):
                # Get /24 network
                network = ipaddress.ip_network(f"{ip}/24", strict=False)
                return [str(host) for host in network.hosts()]
            else:
                # For IPv6, use /112 (smaller range)
                network = ipaddress.ip_network(f"{ip}/112", strict=False)
                return [str(host) for host in list(network.hosts())[:256]]
        except Exception as e:
            logger.error(f"Error getting IP range for {ip}: {e}")
            return []

    def _scan_ip(self, ip: str) -> tuple[str, Optional[str]]:
        """
        Scan a single IP for PTR record matching our domain.

        Args:
            ip: IP to scan

        Returns:
            Tuple of (ip, hostname) if found
        """
        hostname = self.resolver.resolve_ptr(ip)
        if hostname and hostname.endswith(f".{self.domain}"):
            return ip, hostname
        return ip, None

    def enumerate(
        self,
        additional_ips: Optional[Set[str]] = None,
        ip_ranges: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> Dict[str, Optional[str]]:
        """
        Perform reverse DNS sweep.

        Args:
            additional_ips: Additional IPs to include in sweep
            ip_ranges: CIDR ranges to scan (e.g., ['192.168.0.0/24'])
            progress_callback: Progress callback (current, total, found)

        Returns:
            Dict of {subdomain: ip_address}
        """
        logger.info(f"Starting reverse DNS sweep for {self.domain}")

        # Get known IPs
        self.known_ips = self._get_domain_ips()
        if additional_ips:
            self.known_ips.update(additional_ips)

        # Get all IPs to scan (unique /24 networks)
        networks_scanned = set()
        all_ips = set()

        # Add IPs from discovered domain records
        for ip in self.known_ips:
            try:
                network = ipaddress.ip_network(f"{ip}/24", strict=False)
                network_key = str(network)
                if network_key not in networks_scanned:
                    networks_scanned.add(network_key)
                    all_ips.update(self._get_ip_range(ip))
            except Exception:
                pass

        # Add explicit IP ranges
        if ip_ranges:
            for cidr in ip_ranges:
                try:
                    network = ipaddress.ip_network(cidr, strict=False)
                    all_ips.update(str(host) for host in network.hosts())
                    logger.info(f"Added range {cidr} ({network.num_addresses} IPs)")
                except ValueError as e:
                    logger.warning(f"Invalid CIDR range {cidr}: {e}")

        if not all_ips:
            logger.warning("No IP ranges to scan")
            return {}

        total = len(all_ips)
        logger.info(f"Scanning {total} IPs across {len(networks_scanned)} networks")

        completed = 0
        found = 0

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self._scan_ip, ip): ip for ip in all_ips}

            for future in as_completed(futures):
                try:
                    ip, hostname = future.result()
                    completed += 1

                    if hostname:
                        self._add_discovered(hostname, ip)
                        found += 1
                        logger.debug(f"Found: {hostname} -> {ip}")

                    if progress_callback and completed % 50 == 0:
                        progress_callback(completed, total, found)

                except Exception as e:
                    completed += 1
                    logger.debug(f"Error in PTR lookup: {e}")

        if progress_callback:
            progress_callback(completed, total, found)

        logger.info(f"Reverse DNS sweep found {len(self.discovered)} subdomains")
        return self.discovered

    def add_ips_from_subdomains(self, subdomains: Dict[str, Optional[str]]) -> None:
        """
        Add IPs from discovered subdomains for scanning.

        Args:
            subdomains: Dict of {subdomain: ip_address}
        """
        for subdomain, ip in subdomains.items():
            if ip:
                self.known_ips.add(ip)
