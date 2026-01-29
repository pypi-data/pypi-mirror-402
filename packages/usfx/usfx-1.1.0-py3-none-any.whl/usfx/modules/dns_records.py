"""
DNS Record Mining Module

Analyzes various DNS record types to discover subdomains:
- MX records (mail servers)
- NS records (nameservers)
- TXT records (SPF, DMARC, DKIM)
- SRV records (services)
- SOA records
- CAA records
"""

import logging
import re
from typing import Dict, Optional, Set, TYPE_CHECKING

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class DNSRecordMiner(BaseModule):
    """DNS record analysis for subdomain discovery"""

    MODULE_NAME = "dns_records"

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        timeout: float = 5.0
    ):
        """
        Initialize DNS record miner.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver
            timeout: DNS query timeout
        """
        super().__init__(domain, resolver, timeout)

    def _extract_domain_from_text(self, text: str) -> Set[str]:
        """
        Extract domain names from text (like SPF records).

        Args:
            text: Text to parse

        Returns:
            Set of discovered domains
        """
        domains = set()

        # Match domain patterns
        domain_pattern = rf'([a-zA-Z0-9][-a-zA-Z0-9]*\.)*{re.escape(self.domain)}'
        matches = re.findall(domain_pattern, text, re.IGNORECASE)

        # Also look for include: and redirect= in SPF
        spf_includes = re.findall(r'include:([^\s]+)', text, re.IGNORECASE)
        spf_redirects = re.findall(r'redirect=([^\s]+)', text, re.IGNORECASE)

        for match in spf_includes + spf_redirects:
            if self.domain in match.lower():
                domains.add(match.lower().rstrip('.'))

        # Look for explicit subdomains
        subdomain_pattern = rf'([a-zA-Z0-9][-a-zA-Z0-9]*\.)+{re.escape(self.domain)}'
        subdomain_matches = re.findall(subdomain_pattern, text, re.IGNORECASE)

        for match in subdomain_matches:
            full_domain = f"{match}{self.domain}".lower().rstrip('.')
            if full_domain != self.domain:
                domains.add(full_domain)

        return domains

    def _query_mx(self) -> Set[str]:
        """Query MX records"""
        discovered = set()

        mx_records = self.resolver.resolve_mx(self.domain)
        for priority, mx_host in mx_records:
            mx_host = mx_host.lower()

            # Check if MX is a subdomain
            if mx_host.endswith(f".{self.domain}"):
                discovered.add(mx_host)
                self._add_discovered(mx_host)
                logger.debug(f"MX record: {mx_host}")

        return discovered

    def _query_ns(self) -> Set[str]:
        """Query NS records"""
        discovered = set()

        ns_records = self.resolver.resolve_ns(self.domain)
        for ns_host in ns_records:
            ns_host = ns_host.lower()

            if ns_host.endswith(f".{self.domain}"):
                discovered.add(ns_host)
                self._add_discovered(ns_host)
                logger.debug(f"NS record: {ns_host}")

        return discovered

    def _query_txt(self) -> Set[str]:
        """Query TXT records for SPF, DMARC, etc."""
        discovered = set()

        # Query main domain TXT
        txt_records = self.resolver.resolve_txt(self.domain)
        for txt_data in txt_records:
            found = self._extract_domain_from_text(txt_data)
            discovered.update(found)
            for d in found:
                self._add_discovered(d)

        # Query _dmarc
        dmarc_domain = f"_dmarc.{self.domain}"
        dmarc_records = self.resolver.resolve_txt(dmarc_domain)
        for txt_data in dmarc_records:
            # Extract rua and ruf email domains
            rua_matches = re.findall(r'rua=mailto:[^@]+@([^\s;]+)', txt_data)
            ruf_matches = re.findall(r'ruf=mailto:[^@]+@([^\s;]+)', txt_data)

            for domain in rua_matches + ruf_matches:
                domain = domain.lower().rstrip('.')
                if domain.endswith(f".{self.domain}") or domain == self.domain:
                    if domain != self.domain:
                        discovered.add(domain)
                        self._add_discovered(domain)

        return discovered

    def _query_srv(self) -> Set[str]:
        """Query common SRV records"""
        discovered = set()

        # Common SRV record prefixes
        srv_prefixes = [
            '_autodiscover._tcp',  # Exchange
            '_sip._tcp', '_sip._udp',  # SIP
            '_xmpp-client._tcp', '_xmpp-server._tcp',  # XMPP
            '_ldap._tcp',  # LDAP
            '_kerberos._tcp', '_kerberos._udp',  # Kerberos
            '_gc._tcp',  # Global Catalog
            '_kpasswd._tcp', '_kpasswd._udp',  # Kerberos password
            '_http._tcp', '_https._tcp',  # HTTP
            '_imaps._tcp', '_imap._tcp',  # IMAP
            '_pop3s._tcp', '_pop3._tcp',  # POP3
            '_smtps._tcp', '_smtp._tcp',  # SMTP
            '_submission._tcp',  # Mail submission
        ]

        for prefix in srv_prefixes:
            srv_name = f"{prefix}.{self.domain}"
            srv_records = self.resolver.resolve_srv(srv_name)

            for priority, weight, port, target in srv_records:
                target = target.lower()
                if target.endswith(f".{self.domain}"):
                    discovered.add(target)
                    self._add_discovered(target)
                    logger.debug(f"SRV record {prefix}: {target}")

        return discovered

    def _query_soa(self) -> Set[str]:
        """Query SOA record for hostnames"""
        discovered = set()

        soa = self.resolver.resolve_soa(self.domain)
        if soa:
            mname = soa['mname'].lower()
            rname = soa['rname'].lower()

            if mname.endswith(f".{self.domain}"):
                discovered.add(mname)
                self._add_discovered(mname)

            # rname is often in email format (hostmaster.domain.com)
            # Convert to actual domain
            if '.' in rname:
                potential_domain = rname
                if potential_domain.endswith(f".{self.domain}"):
                    discovered.add(potential_domain)
                    self._add_discovered(potential_domain)

        return discovered

    def _query_caa(self) -> Set[str]:
        """Query CAA records for domain references"""
        discovered = set()

        caa_records = self.resolver.resolve_any(self.domain, 'CAA')
        for record in caa_records:
            value = str(record).lower()
            if value.endswith(f".{self.domain}"):
                discovered.add(value)
                self._add_discovered(value)

        return discovered

    def enumerate(self) -> Dict[str, Optional[str]]:
        """
        Mine all DNS record types for subdomains.

        Returns:
            Dict of {subdomain: ip_address}
        """
        logger.info(f"Mining DNS records for {self.domain}")

        # Query all record types
        all_discovered = set()
        all_discovered.update(self._query_mx())
        all_discovered.update(self._query_ns())
        all_discovered.update(self._query_txt())
        all_discovered.update(self._query_srv())
        all_discovered.update(self._query_soa())
        all_discovered.update(self._query_caa())

        # Resolve discovered subdomains
        for subdomain in all_discovered:
            if subdomain in self.discovered and self.discovered[subdomain] is None:
                ip = self.resolver.resolve_a(subdomain)
                if ip:
                    self.discovered[subdomain] = ip

        logger.info(f"DNS record mining found {len(self.discovered)} subdomains")
        return self.discovered
