"""
CNAME Chain Analysis Module

Follows CNAME records to discover related domains and potential
subdomain takeover vulnerabilities.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class CNAMEChaser(BaseModule):
    """Analyzes CNAME chains to discover related subdomains"""

    MODULE_NAME = "cname_chaser"

    # Known CDN/service CNAME patterns that might reveal subdomains
    INTERESTING_PATTERNS = [
        '.cloudfront.net',
        '.amazonaws.com',
        '.azurewebsites.net',
        '.azure-api.net',
        '.cloudflare.com',
        '.fastly.net',
        '.akamaiedge.net',
        '.akamaitechnologies.com',
        '.edgekey.net',
        '.edgesuite.net',
        '.herokuapp.com',
        '.github.io',
        '.gitlab.io',
        '.netlify.app',
        '.vercel.app',
        '.pages.dev',
    ]

    # Patterns that indicate potential subdomain takeover
    TAKEOVER_FINGERPRINTS = {
        '.s3.amazonaws.com': 'NoSuchBucket',
        '.s3-website': 'NoSuchBucket',
        '.cloudfront.net': 'Bad Request',
        '.herokuapp.com': 'No such app',
        '.github.io': "There isn't a GitHub Pages site here",
        '.gitlab.io': "The page you're looking for could not be found",
        '.netlify.app': 'Not Found',
        '.zendesk.com': 'Help Center Closed',
        '.shopify.com': 'Sorry, this shop is currently unavailable',
    }

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        max_chain_depth: int = 10,
        threads: int = 20
    ):
        """
        Initialize CNAME chaser.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver
            max_chain_depth: Maximum CNAME chain depth to follow
            threads: Number of parallel threads
        """
        super().__init__(domain, resolver)
        self.max_chain_depth = max_chain_depth
        self.threads = threads

    def _follow_cname_chain(self, subdomain: str) -> List[str]:
        """Follow CNAME chain and return all CNAMEs"""
        chain = []
        current = subdomain
        seen = set()

        for _ in range(self.max_chain_depth):
            if current in seen:
                break  # Circular reference
            seen.add(current)

            cname = self.resolver.resolve_cname(current)
            if cname:
                chain.append(cname)
                current = cname
            else:
                break

        return chain

    def _extract_related_subdomains(self, cname: str) -> Set[str]:
        """Extract potential related subdomains from CNAME"""
        related = set()

        # If CNAME contains our domain, it's a subdomain
        if self.domain in cname:
            # Extract the full subdomain
            if cname.endswith(self.domain):
                related.add(cname)
            else:
                # Maybe it's like "subdomain.example.com.cdn.cloudflare.com"
                parts = cname.split('.')
                for i in range(len(parts)):
                    candidate = '.'.join(parts[i:])
                    if candidate.endswith(self.domain) and candidate != self.domain:
                        related.add(candidate)
                        break

        return related

    def _check_takeover_potential(self, subdomain: str, cname_chain: List[str]) -> Optional[str]:
        """Check if subdomain might be vulnerable to takeover"""
        if not cname_chain:
            return None

        final_cname = cname_chain[-1].lower()

        for pattern, fingerprint in self.TAKEOVER_FINGERPRINTS.items():
            if pattern in final_cname:
                # Flag the pattern as potential vulnerability
                return f"Potential takeover: {final_cname} (pattern: {pattern})"

        return None

    def _analyze_subdomain(self, subdomain: str) -> Tuple[str, List[str], Set[str], Optional[str]]:
        """Analyze a single subdomain's CNAME chain"""
        chain = self._follow_cname_chain(subdomain)
        related = set()
        takeover_warning = None

        for cname in chain:
            related.update(self._extract_related_subdomains(cname))

        if chain:
            takeover_warning = self._check_takeover_potential(subdomain, chain)

        return subdomain, chain, related, takeover_warning

    def enumerate(self, known_subdomains: Dict[str, Optional[str]] = None) -> Dict[str, Optional[str]]:
        """
        Analyze CNAME chains for known subdomains.

        Args:
            known_subdomains: Dict of known subdomains to analyze

        Returns:
            Dict of newly discovered subdomains
        """
        if not known_subdomains:
            known_subdomains = {}

        logger.info(f"Analyzing CNAME chains for {len(known_subdomains)} subdomains")

        takeover_warnings = []

        # Analyze all known subdomains
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self._analyze_subdomain, sub): sub
                for sub in known_subdomains.keys()
            }

            for future in as_completed(futures, timeout=120):
                try:
                    subdomain, chain, related, warning = future.result()

                    # Add newly discovered subdomains
                    for sub in related:
                        if sub not in known_subdomains:
                            self._add_discovered(sub)
                            logger.debug(f"CNAME chain discovered: {sub}")

                    if warning:
                        takeover_warnings.append((subdomain, warning))

                except Exception as e:
                    logger.debug(f"CNAME analysis error: {e}")

        # Log takeover warnings
        if takeover_warnings:
            logger.warning(f"Found {len(takeover_warnings)} potential subdomain takeover vulnerabilities:")
            for sub, warning in takeover_warnings:
                logger.warning(f"  {sub}: {warning}")

        logger.info(f"CNAME analysis discovered {len(self.discovered)} new subdomains")

        return self.discovered

    def get_cname_chain(self, subdomain: str) -> List[str]:
        """
        Get the CNAME chain for a specific subdomain.

        Args:
            subdomain: Subdomain to analyze

        Returns:
            List of CNAMEs in the chain
        """
        return self._follow_cname_chain(subdomain)
