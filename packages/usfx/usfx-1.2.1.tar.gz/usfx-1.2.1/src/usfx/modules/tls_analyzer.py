"""
TLS Certificate Analysis Module

Extracts subdomains from TLS certificates by connecting to discovered IPs
and parsing the Subject Alternative Names (SANs) field.
"""

import logging
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, TYPE_CHECKING

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtensionOID
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

logger = logging.getLogger(__name__)


class TLSAnalyzer(BaseModule):
    """TLS certificate analysis for subdomain discovery"""

    MODULE_NAME = "tls_analyzer"

    # Common ports that might serve TLS
    COMMON_TLS_PORTS = [443, 8443, 8080, 4443, 9443]

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        timeout: float = 5.0,
        threads: int = 10
    ):
        """
        Initialize TLS analyzer.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver
            timeout: Connection timeout
            threads: Number of parallel threads
        """
        super().__init__(domain, resolver, timeout)
        self.threads = threads
        self.analyzed_hosts: Set[str] = set()

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create an SSL context that accepts all certificates"""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _get_certificate(self, host: str, port: int = 443) -> Optional[bytes]:
        """
        Get the TLS certificate from a host.

        Args:
            host: Hostname or IP
            port: Port number

        Returns:
            DER-encoded certificate or None
        """
        try:
            ctx = self._create_ssl_context()

            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.domain) as ssl_sock:
                    cert_der = ssl_sock.getpeercert(binary_form=True)
                    return cert_der

        except (socket.timeout, socket.error, ssl.SSLError) as e:
            logger.debug(f"Failed to get cert from {host}:{port}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error getting cert from {host}:{port}: {e}")
            return None

    def _extract_sans_cryptography(self, cert_der: bytes) -> Set[str]:
        """
        Extract SANs using cryptography library.

        Args:
            cert_der: DER-encoded certificate

        Returns:
            Set of domain names from SANs
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            return set()

        domains = set()

        try:
            cert = x509.load_der_x509_certificate(cert_der, default_backend())

            # Get Subject Alternative Names
            try:
                san_ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                for name in san_ext.value:
                    if isinstance(name, x509.DNSName):
                        domains.add(name.value.lower())
            except x509.ExtensionNotFound:
                pass

            # Get Common Name
            try:
                for attr in cert.subject:
                    if attr.oid == NameOID.COMMON_NAME:
                        domains.add(attr.value.lower())
            except Exception:
                pass

        except Exception as e:
            logger.debug(f"Error parsing certificate: {e}")

        return domains

    def _extract_sans(self, cert_der: bytes) -> Set[str]:
        """
        Extract SANs from certificate.

        Args:
            cert_der: DER-encoded certificate

        Returns:
            Set of domain names from SANs
        """
        if CRYPTOGRAPHY_AVAILABLE:
            return self._extract_sans_cryptography(cert_der)
        else:
            logger.warning("cryptography library not available - TLS analysis limited")
            return set()

    def _analyze_host(self, host: str, port: int = 443) -> Set[str]:
        """
        Analyze a single host's TLS certificate.

        Args:
            host: Host to analyze
            port: Port number

        Returns:
            Set of discovered subdomains
        """
        discovered = set()
        host_key = f"{host}:{port}"

        if host_key in self.analyzed_hosts:
            return discovered

        self.analyzed_hosts.add(host_key)

        cert_der = self._get_certificate(host, port)
        if not cert_der:
            return discovered

        sans = self._extract_sans(cert_der)

        for name in sans:
            # Remove wildcard prefix
            if name.startswith('*.'):
                name = name[2:]

            # Check if it's a subdomain of our target
            if name.endswith(f".{self.domain}") and name != self.domain:
                discovered.add(name)
                logger.debug(f"Found SAN: {name} from {host}:{port}")

        return discovered

    def _probe_sni(self, ip: str, hostname: str, port: int = 443) -> bool:
        """
        Probe if a specific hostname works via SNI.

        Args:
            ip: IP address to connect to
            hostname: Hostname to send via SNI
            port: Port number

        Returns:
            True if the hostname is served at this IP
        """
        try:
            ctx = self._create_ssl_context()

            with socket.create_connection((ip, port), timeout=self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssl_sock:
                    cert_der = ssl_sock.getpeercert(binary_form=True)
                    if cert_der:
                        sans = self._extract_sans(cert_der)
                        return hostname.lower() in sans or f"*.{'.'.join(hostname.split('.')[1:])}".lower() in sans

        except Exception:
            pass

        return False

    def enumerate(
        self,
        known_hosts: Optional[Dict[str, str]] = None,
        scan_ports: bool = False
    ) -> Dict[str, Optional[str]]:
        """
        Enumerate subdomains from TLS certificates.

        Args:
            known_hosts: Dict of {subdomain: ip} to analyze
            scan_ports: Whether to scan multiple TLS ports

        Returns:
            Dict of {subdomain: ip_address}
        """
        logger.info(f"Starting TLS analysis for {self.domain}")

        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("cryptography library not available - TLS analysis limited")

        # Determine hosts to analyze
        hosts_to_analyze = set()

        if known_hosts:
            for subdomain, ip in known_hosts.items():
                if ip:
                    hosts_to_analyze.add(ip)
                hosts_to_analyze.add(subdomain)

        # Always try the main domain
        hosts_to_analyze.add(self.domain)
        hosts_to_analyze.add(f"www.{self.domain}")

        ports = self.COMMON_TLS_PORTS if scan_ports else [443]
        all_discovered = set()

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for host in hosts_to_analyze:
                for port in ports:
                    futures.append(executor.submit(self._analyze_host, host, port))

            for future in as_completed(futures):
                try:
                    discovered = future.result()
                    all_discovered.update(discovered)
                except Exception as e:
                    logger.debug(f"Error in TLS analysis: {e}")

        # Build result dict
        for subdomain in all_discovered:
            self._add_discovered(subdomain)

        logger.info(f"TLS analysis found {len(self.discovered)} subdomains")
        return self.discovered
