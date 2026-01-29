"""
Recursive Subdomain Enumeration Module

Discovers sub-subdomains by treating discovered subdomains as base domains
and running enumeration on them (e.g., finding dev.api.example.com when
api.example.com was discovered).
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Optional, TYPE_CHECKING

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class RecursiveEnumerator(BaseModule):
    """Discovers sub-subdomains through recursive enumeration"""

    MODULE_NAME = "recursive_enum"

    # Short wordlist for recursive enumeration (most common prefixes only)
    RECURSIVE_WORDLIST = [
        # Development
        'dev', 'staging', 'test', 'qa', 'beta',

        # Versioning
        'v1', 'v2', 'v3',

        # Environments
        'prod', 'internal',

        # Geographic
        'us', 'eu', 'asia',

        # Numbered
        '1', '2', 'node1', 'node2',

        # Services
        'api', 'app', 'www', 'admin', 'auth', 'db', 'cdn', 'static',
    ]

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        threads: int = 20,
        max_depth: int = 2
    ):
        """
        Initialize recursive enumerator.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver
            threads: Number of parallel threads
            max_depth: Maximum recursion depth
        """
        super().__init__(domain, resolver)
        self.threads = threads
        self.max_depth = max_depth

    def _enumerate_subdomain(self, base_subdomain: str) -> Dict[str, Optional[str]]:
        """Enumerate sub-subdomains for a given subdomain"""
        discovered = {}

        for prefix in self.RECURSIVE_WORDLIST:
            candidate = f'{prefix}.{base_subdomain}'

            # Skip if it's too deep (more than max_depth levels above original domain)
            depth = candidate.count('.') - self.domain.count('.')
            if depth > self.max_depth:
                continue

            ip = self.resolver.resolve_a(candidate)
            if ip:
                discovered[candidate] = ip

        return discovered

    def _get_subdomain_depth(self, subdomain: str) -> int:
        """Calculate depth of subdomain relative to base domain"""
        return subdomain.count('.') - self.domain.count('.')

    def enumerate(
        self,
        known_subdomains: Dict[str, Optional[str]] = None,
        resolver_func: Optional[Callable[[str], Optional[str]]] = None
    ) -> Dict[str, Optional[str]]:
        """
        Recursively enumerate sub-subdomains.

        Args:
            known_subdomains: Dict of discovered subdomains to use as base
            resolver_func: Optional custom resolver function

        Returns:
            Dict of newly discovered sub-subdomains with IPs
        """
        start_time = time.time()
        max_duration = 45  # Maximum 45 seconds

        if not known_subdomains:
            return {}

        logger.info(f"Starting recursive enumeration on {len(known_subdomains)} subdomains")

        # Filter subdomains that are worth recursing on
        # Only recurse on depth-1 subdomains (direct subdomains of base domain)
        candidates = []
        for subdomain in known_subdomains.keys():
            depth = self._get_subdomain_depth(subdomain)
            if depth == 1:  # Only direct subdomains
                candidates.append(subdomain)

        if not candidates:
            logger.info("No suitable subdomains for recursive enumeration")
            return {}

        # Limit to first 10 candidates
        candidates = candidates[:10]
        logger.info(f"Recursively enumerating {len(candidates)} base subdomains")

        all_discovered = {}

        # Process each candidate subdomain
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self._enumerate_subdomain, sub): sub
                for sub in candidates
            }

            for future in as_completed(futures, timeout=30):
                if time.time() - start_time > max_duration:
                    logger.info("Recursive enumeration timeout reached")
                    break

                try:
                    results = future.result(timeout=10)
                    for subdomain, ip in results.items():
                        if subdomain not in known_subdomains and subdomain not in all_discovered:
                            all_discovered[subdomain] = ip
                            self._add_discovered(subdomain, ip)
                            logger.debug(f"Recursive discovery: {subdomain} -> {ip}")
                except Exception as e:
                    logger.debug(f"Recursive enumeration error: {e}")

        logger.info(f"Recursive enumeration discovered {len(all_discovered)} new sub-subdomains in {time.time() - start_time:.1f}s")

        return self.discovered

    def deep_enumerate(
        self,
        known_subdomains: Dict[str, Optional[str]],
        max_iterations: int = 3
    ) -> Dict[str, Optional[str]]:
        """
        Perform multiple rounds of recursive enumeration.

        Each round uses newly discovered subdomains as seeds for the next round.

        Args:
            known_subdomains: Initial set of known subdomains
            max_iterations: Maximum number of recursive rounds

        Returns:
            All newly discovered subdomains
        """
        all_discovered = {}
        current_known = dict(known_subdomains)

        for iteration in range(max_iterations):
            logger.info(f"Recursive enumeration round {iteration + 1}/{max_iterations}")

            new_discoveries = self.enumerate(current_known)

            if not new_discoveries:
                logger.info(f"No new discoveries in round {iteration + 1}, stopping")
                break

            # Add to total discovered
            all_discovered.update(new_discoveries)

            # Update known for next round
            current_known.update(new_discoveries)

            logger.info(f"Round {iteration + 1} found {len(new_discoveries)} new subdomains")

        return all_discovered
