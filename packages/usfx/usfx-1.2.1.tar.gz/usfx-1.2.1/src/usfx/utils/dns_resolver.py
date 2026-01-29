"""
Custom DNS Resolver for Internal Networks

The core utility that enables subdomain enumeration against internal DNS servers.
Supports multiple DNS servers, custom timeouts, and provides a unified interface
for all enumeration modules.
"""

import logging
from typing import List, Optional, Set, Tuple

import dns.resolver
import dns.exception
import dns.rdatatype
import dns.reversename

logger = logging.getLogger(__name__)


class InternalDNSResolver:
    """
    DNS resolver that supports custom internal DNS servers.

    This is the key component that differentiates internal-usf from
    internet-based subdomain finders. By specifying internal DNS servers,
    you can enumerate subdomains that only exist on your internal network.

    Usage:
        # Use custom internal DNS servers
        resolver = InternalDNSResolver(dns_servers=['192.168.1.1', '10.0.0.1'])

        # Use system default DNS
        resolver = InternalDNSResolver()

        # Resolve a subdomain
        ip = resolver.resolve_a('api.corp.local')
    """

    def __init__(
        self,
        dns_servers: Optional[List[str]] = None,
        timeout: float = 3.0,
        lifetime: float = 6.0
    ):
        """
        Initialize the DNS resolver.

        Args:
            dns_servers: List of DNS server IPs. If None, uses system defaults.
            timeout: Timeout for individual DNS queries in seconds.
            lifetime: Total time allowed for a query (including retries).
        """
        self.resolver = dns.resolver.Resolver()
        self.timeout = timeout
        self.lifetime = lifetime

        # Configure resolver
        self.resolver.timeout = timeout
        self.resolver.lifetime = lifetime

        # Set custom DNS servers if provided
        if dns_servers:
            self.dns_servers = dns_servers
            self.resolver.nameservers = dns_servers
            logger.info(f"Using custom DNS servers: {', '.join(dns_servers)}")
        else:
            # Use system default DNS servers
            self.dns_servers = self.resolver.nameservers.copy()
            logger.info(f"Using system DNS servers: {', '.join(self.dns_servers)}")

    def resolve_a(self, hostname: str) -> Optional[str]:
        """
        Resolve hostname to IPv4 address (A record).

        Args:
            hostname: Fully qualified domain name to resolve.

        Returns:
            Primary IP address or None if not found.
        """
        try:
            answers = self.resolver.resolve(hostname, 'A')
            return str(answers[0])
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            return None
        except dns.resolver.NoNameservers:
            logger.debug(f"No nameservers available for {hostname}")
            return None
        except dns.exception.Timeout:
            logger.debug(f"Timeout resolving {hostname}")
            return None
        except Exception as e:
            logger.debug(f"Error resolving {hostname}: {e}")
            return None

    def resolve_a_all(self, hostname: str) -> Set[str]:
        """
        Resolve hostname to all IPv4 addresses.

        Args:
            hostname: Fully qualified domain name to resolve.

        Returns:
            Set of all IP addresses, empty set if not found.
        """
        try:
            answers = self.resolver.resolve(hostname, 'A')
            return {str(rdata) for rdata in answers}
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return set()
        except Exception as e:
            logger.debug(f"Error resolving {hostname}: {e}")
            return set()

    def resolve_aaaa(self, hostname: str) -> Optional[str]:
        """
        Resolve hostname to IPv6 address (AAAA record).

        Args:
            hostname: Fully qualified domain name to resolve.

        Returns:
            Primary IPv6 address or None if not found.
        """
        try:
            answers = self.resolver.resolve(hostname, 'AAAA')
            return str(answers[0])
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return None
        except Exception as e:
            logger.debug(f"Error resolving AAAA for {hostname}: {e}")
            return None

    def resolve_cname(self, hostname: str) -> Optional[str]:
        """
        Resolve CNAME record for hostname.

        Args:
            hostname: Fully qualified domain name.

        Returns:
            CNAME target or None if not found.
        """
        try:
            answers = self.resolver.resolve(hostname, 'CNAME')
            return str(answers[0].target).rstrip('.')
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return None
        except Exception as e:
            logger.debug(f"Error resolving CNAME for {hostname}: {e}")
            return None

    def resolve_mx(self, domain: str) -> List[Tuple[int, str]]:
        """
        Resolve MX records for domain.

        Args:
            domain: Domain to query.

        Returns:
            List of (priority, hostname) tuples.
        """
        try:
            answers = self.resolver.resolve(domain, 'MX')
            return [(rdata.preference, str(rdata.exchange).rstrip('.'))
                    for rdata in answers]
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return []
        except Exception as e:
            logger.debug(f"Error resolving MX for {domain}: {e}")
            return []

    def resolve_ns(self, domain: str) -> List[str]:
        """
        Resolve NS records for domain.

        Args:
            domain: Domain to query.

        Returns:
            List of nameserver hostnames.
        """
        try:
            answers = self.resolver.resolve(domain, 'NS')
            return [str(rdata).rstrip('.') for rdata in answers]
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return []
        except Exception as e:
            logger.debug(f"Error resolving NS for {domain}: {e}")
            return []

    def resolve_txt(self, domain: str) -> List[str]:
        """
        Resolve TXT records for domain.

        Args:
            domain: Domain to query.

        Returns:
            List of TXT record values.
        """
        try:
            answers = self.resolver.resolve(domain, 'TXT')
            return [str(rdata).strip('"') for rdata in answers]
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return []
        except Exception as e:
            logger.debug(f"Error resolving TXT for {domain}: {e}")
            return []

    def resolve_srv(self, name: str) -> List[Tuple[int, int, int, str]]:
        """
        Resolve SRV records.

        Args:
            name: SRV record name (e.g., _ldap._tcp.domain.local)

        Returns:
            List of (priority, weight, port, target) tuples.
        """
        try:
            answers = self.resolver.resolve(name, 'SRV')
            return [(rdata.priority, rdata.weight, rdata.port,
                     str(rdata.target).rstrip('.'))
                    for rdata in answers]
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return []
        except Exception as e:
            logger.debug(f"Error resolving SRV for {name}: {e}")
            return []

    def resolve_soa(self, domain: str) -> Optional[dict]:
        """
        Resolve SOA record for domain.

        Args:
            domain: Domain to query.

        Returns:
            Dict with SOA fields or None.
        """
        try:
            answers = self.resolver.resolve(domain, 'SOA')
            rdata = answers[0]
            return {
                'mname': str(rdata.mname).rstrip('.'),
                'rname': str(rdata.rname).rstrip('.'),
                'serial': rdata.serial,
                'refresh': rdata.refresh,
                'retry': rdata.retry,
                'expire': rdata.expire,
                'minimum': rdata.minimum,
            }
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return None
        except Exception as e:
            logger.debug(f"Error resolving SOA for {domain}: {e}")
            return None

    def resolve_ptr(self, ip: str) -> Optional[str]:
        """
        Resolve PTR (reverse DNS) record for IP address.

        Args:
            ip: IP address to lookup.

        Returns:
            Hostname or None.
        """
        try:
            reverse_name = dns.reversename.from_address(ip)
            answers = self.resolver.resolve(reverse_name, 'PTR')
            return str(answers[0]).rstrip('.').lower()
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return None
        except Exception as e:
            logger.debug(f"Error resolving PTR for {ip}: {e}")
            return None

    def resolve_any(self, hostname: str, record_type: str) -> List[str]:
        """
        Resolve any DNS record type.

        Args:
            hostname: Hostname to query.
            record_type: DNS record type (A, AAAA, MX, NS, TXT, etc.)

        Returns:
            List of string representations of the records.
        """
        try:
            answers = self.resolver.resolve(hostname, record_type)
            return [str(rdata) for rdata in answers]
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return []
        except Exception as e:
            logger.debug(f"Error resolving {record_type} for {hostname}: {e}")
            return []

    def check_exists(self, hostname: str) -> bool:
        """
        Check if a hostname exists (has any DNS record).

        Args:
            hostname: Hostname to check.

        Returns:
            True if hostname exists.
        """
        # Try A record first (most common)
        if self.resolve_a(hostname):
            return True

        # Try CNAME
        if self.resolve_cname(hostname):
            return True

        # Try AAAA
        if self.resolve_aaaa(hostname):
            return True

        return False

    def get_native_resolver(self) -> dns.resolver.Resolver:
        """
        Get the underlying dnspython resolver for advanced operations.

        Returns:
            The configured dns.resolver.Resolver instance.
        """
        return self.resolver

    def create_child_resolver(
        self,
        timeout: Optional[float] = None,
        lifetime: Optional[float] = None
    ) -> 'InternalDNSResolver':
        """
        Create a child resolver with the same DNS servers but different timeouts.

        Useful for modules that need different timeout configurations.

        Args:
            timeout: New timeout value (uses parent's if None)
            lifetime: New lifetime value (uses parent's if None)

        Returns:
            New InternalDNSResolver instance.
        """
        return InternalDNSResolver(
            dns_servers=self.dns_servers,
            timeout=timeout if timeout is not None else self.timeout,
            lifetime=lifetime if lifetime is not None else self.lifetime
        )

    def check_connectivity(self, test_domain: str = "google.com") -> Tuple[bool, Optional[str]]:
        """
        Check if DNS servers are reachable by performing a test query.

        Args:
            test_domain: Domain to use for connectivity test (default: google.com)

        Returns:
            Tuple of (is_reachable, error_message).
            If reachable, returns (True, None).
            If not reachable, returns (False, error_description).
        """
        try:
            # Try a simple A record query
            answers = self.resolver.resolve(test_domain, 'A')
            if answers:
                return (True, None)
            return (False, "No response received")
        except dns.resolver.NoNameservers:
            return (False, f"DNS servers not reachable: {', '.join(self.dns_servers)}")
        except dns.exception.Timeout:
            return (False, f"DNS query timed out (servers: {', '.join(self.dns_servers)})")
        except dns.resolver.NXDOMAIN:
            # Domain doesn't exist, but DNS is working
            return (True, None)
        except dns.resolver.NoAnswer:
            # No answer for this query type, but DNS is working
            return (True, None)
        except Exception as e:
            return (False, f"DNS error: {str(e)}")
