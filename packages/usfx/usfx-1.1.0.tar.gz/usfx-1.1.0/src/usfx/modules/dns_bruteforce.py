"""
DNS Brute Force Module

Performs parallel DNS resolution against a wordlist to discover subdomains.
Uses the internal DNS resolver for custom DNS server support.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Optional, Set, TYPE_CHECKING

from .base import BaseModule
from ..utils.wordlist import WordlistManager
from ..utils.wildcard import WildcardDetector

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class DNSBruteforcer(BaseModule):
    """Subdomain discovery via DNS brute force"""

    MODULE_NAME = "dns_bruteforce"

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        wordlist_path: Optional[str] = None,
        wordlist_size: str = 'medium',
        threads: int = 30,
        timeout: float = 2.0,
        cancel_check: Optional[Callable[[], bool]] = None
    ):
        """
        Initialize DNS brute forcer.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver (uses internal if None)
            wordlist_path: Custom wordlist file path
            wordlist_size: Size of bundled wordlist ('small', 'medium', 'large')
            threads: Number of parallel threads
            timeout: DNS query timeout
            cancel_check: Optional function that returns True if cancelled
        """
        super().__init__(domain, resolver, timeout, cancel_check)

        self.threads = threads
        self.wordlist_path = wordlist_path
        self.wordlist_size = wordlist_size
        self.wordlist_manager = WordlistManager(wordlist_path)
        self.wildcard_detector = WildcardDetector(domain, resolver)

    def _resolve_subdomain(self, subdomain: str) -> tuple[str, Optional[str], Optional[Set[str]]]:
        """
        Resolve a single subdomain.

        Args:
            subdomain: Subdomain prefix to test

        Returns:
            Tuple of (full_subdomain, ip_address, all_ips)
        """
        fqdn = f"{subdomain}.{self.domain}"

        ips = self.resolver.resolve_a_all(fqdn)
        primary_ip = list(ips)[0] if ips else None

        return fqdn, primary_ip, ips

    def enumerate(
        self,
        max_words: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> Dict[str, Optional[str]]:
        """
        Perform DNS brute force enumeration.

        Args:
            max_words: Maximum number of words to test
            progress_callback: Callback for progress updates (current, total, found)

        Returns:
            Dict of {subdomain: ip_address}
        """
        if self.is_cancelled():
            return self.discovered

        logger.info(f"Starting DNS brute force for {self.domain}")

        # Detect wildcards first
        has_wildcard, wildcard_ips = self.wildcard_detector.detect()
        if has_wildcard:
            logger.warning(f"Wildcard DNS detected for {self.domain}: {wildcard_ips}")

        if self.is_cancelled():
            return self.discovered

        # Load wordlist
        wordlist = self.wordlist_manager.get_wordlist(
            size=self.wordlist_size,
            max_words=max_words,
            include_numbers=True,
            include_env=True
        )

        total = len(wordlist)
        logger.info(f"Testing {total} subdomain candidates")

        completed = 0
        found = 0

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self._resolve_subdomain, word): word
                for word in wordlist
            }

            for future in as_completed(futures):
                # Check for cancellation
                if self.is_cancelled():
                    # Cancel remaining futures and exit
                    for f in futures:
                        f.cancel()
                    executor.shutdown(wait=False, cancel_futures=True)
                    logger.info("DNS brute force cancelled")
                    return self.discovered

                try:
                    fqdn, ip, all_ips = future.result(timeout=self.timeout + 1)
                    completed += 1

                    if ip:
                        # Check if it's a wildcard result
                        if has_wildcard and all_ips and self.wildcard_detector.is_wildcard_result(all_ips):
                            logger.debug(f"Filtered wildcard result: {fqdn}")
                        else:
                            self._add_discovered(fqdn, ip)
                            found += 1

                    # Progress update every 100 results
                    if progress_callback and completed % 100 == 0:
                        progress_callback(completed, total, found)

                except Exception as e:
                    completed += 1
                    logger.debug(f"Error in brute force: {e}")

        # Final progress update
        if progress_callback:
            progress_callback(completed, total, found)

        logger.info(f"DNS brute force complete: {found} subdomains found")
        return self.discovered

    def test_specific(self, subdomains: Set[str]) -> Dict[str, Optional[str]]:
        """
        Test specific subdomain candidates.

        Args:
            subdomains: Set of subdomain prefixes to test

        Returns:
            Dict of {subdomain: ip_address}
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self._resolve_subdomain, sub): sub
                for sub in subdomains
            }

            for future in as_completed(futures):
                try:
                    fqdn, ip, _ = future.result()
                    if ip:
                        results[fqdn] = ip
                        self._add_discovered(fqdn, ip)
                except Exception as e:
                    logger.debug(f"Error testing subdomain: {e}")

        return results
