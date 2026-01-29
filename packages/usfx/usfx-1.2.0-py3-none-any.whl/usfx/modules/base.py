"""
Base Module Class

Abstract base class for all subdomain enumeration modules.
Provides common functionality and interface contract.
"""

import logging
import threading
from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class BaseModule(ABC):
    """
    Abstract base class for subdomain enumeration modules.

    All modules must implement the enumerate() method and provide
    a MODULE_NAME class attribute.

    Attributes:
        MODULE_NAME: Unique identifier for the module
        domain: Target domain
        resolver: DNS resolver for lookups
        discovered: Dict of discovered {subdomain: ip}
    """

    MODULE_NAME: str = "base"

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        timeout: float = 3.0,
        cancel_check: Optional[Callable[[], bool]] = None
    ):
        """
        Initialize the module.

        Args:
            domain: Target domain (e.g., 'corp.local')
            resolver: Optional custom DNS resolver
            timeout: Default timeout for operations
            cancel_check: Optional function that returns True if cancelled
        """
        self.domain = domain.lower().strip('.')
        self.timeout = timeout
        self.discovered: Dict[str, Optional[str]] = {}
        self._cancel_check = cancel_check
        self._cancelled = False

        # Use provided resolver or create a new one
        if resolver:
            self.resolver = resolver
        else:
            from ..utils.dns_resolver import InternalDNSResolver
            self.resolver = InternalDNSResolver(timeout=timeout)

    def is_cancelled(self) -> bool:
        """Check if the module should stop"""
        if self._cancelled:
            return True
        if self._cancel_check and self._cancel_check():
            self._cancelled = True
            return True
        return False

    def cancel(self):
        """Cancel the module"""
        self._cancelled = True

    @abstractmethod
    def enumerate(self, **kwargs) -> Dict[str, Optional[str]]:
        """
        Perform subdomain enumeration.

        This method must be implemented by all modules.

        Returns:
            Dict of {subdomain: ip_address}
            IP address may be None if not resolved.
        """
        pass

    def _is_valid_subdomain(self, subdomain: str) -> bool:
        """
        Check if a discovered subdomain is valid for the target domain.

        Args:
            subdomain: Subdomain to validate

        Returns:
            True if valid subdomain of target domain
        """
        subdomain = subdomain.lower().rstrip('.')

        # Must end with .domain
        if not subdomain.endswith(f".{self.domain}"):
            return False

        # Must not be exactly the domain
        if subdomain == self.domain:
            return False

        # Check for empty labels
        labels = subdomain.split('.')
        for label in labels:
            if not label:
                return False

        return True

    def _add_discovered(self, subdomain: str, ip: Optional[str] = None) -> bool:
        """
        Add a discovered subdomain to results.

        Args:
            subdomain: Discovered subdomain
            ip: Optional IP address

        Returns:
            True if added (new), False if already existed
        """
        subdomain = subdomain.lower().rstrip('.')

        if not self._is_valid_subdomain(subdomain):
            return False

        if subdomain not in self.discovered:
            self.discovered[subdomain] = ip
            logger.debug(f"[{self.MODULE_NAME}] Found: {subdomain} -> {ip}")
            return True

        # Update IP if we have one now
        if ip and self.discovered[subdomain] is None:
            self.discovered[subdomain] = ip

        return False

    def _resolve_subdomain(self, subdomain: str) -> Optional[str]:
        """
        Resolve a subdomain using the configured resolver.

        Args:
            subdomain: Subdomain to resolve

        Returns:
            IP address or None
        """
        return self.resolver.resolve_a(subdomain)

    def get_results(self) -> Dict[str, Optional[str]]:
        """
        Get the discovered subdomains.

        Returns:
            Dict of {subdomain: ip_address}
        """
        return self.discovered.copy()

    def get_count(self) -> int:
        """
        Get the number of discovered subdomains.

        Returns:
            Count of discovered subdomains
        """
        return len(self.discovered)
