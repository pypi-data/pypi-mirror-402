"""
Permutation Engine Module

Generates subdomain variations based on discovered subdomains:
- Version variations (api-v1 -> api-v2, api-v3)
- Environment variations (api -> api-dev, api-staging)
- Numeric variations (web1 -> web2, web3)
- Prefix/suffix combinations
"""

import logging
import re
from typing import Callable, Dict, List, Optional, Set, TYPE_CHECKING

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class PermutationEngine(BaseModule):
    """Subdomain permutation generator"""

    MODULE_NAME = "permutation"

    # Common prefixes
    PREFIXES = [
        'dev', 'test', 'stage', 'staging', 'prod', 'production',
        'qa', 'uat', 'sandbox', 'demo', 'beta', 'alpha',
        'internal', 'external', 'private', 'public',
        'old', 'new', 'legacy', 'backup', 'temp', 'tmp',
        'api', 'app', 'web', 'mobile', 'm', 'admin',
        'secure', 'ssl', 'vpn', 'remote', 'local'
    ]

    # Common suffixes
    SUFFIXES = [
        'dev', 'test', 'stage', 'staging', 'prod', 'production',
        'qa', 'uat', 'sandbox', 'demo', 'beta', 'alpha',
        'internal', 'external', 'api', 'app', 'web',
        'old', 'new', 'backup', 'bak', 'temp', 'tmp',
        '01', '02', '03', '1', '2', '3'
    ]

    # Separator characters
    SEPARATORS = ['-', '.', '_', '']

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None
    ):
        """
        Initialize permutation engine.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver
        """
        super().__init__(domain, resolver)

    def _extract_patterns(self, subdomains: Set[str]) -> dict:
        """
        Analyze discovered subdomains to extract patterns.

        Args:
            subdomains: Set of discovered subdomains

        Returns:
            Dict of pattern types and examples
        """
        patterns = {
            'versioned': [],      # api-v1, api-v2
            'numbered': [],       # web1, web2
            'environment': [],    # api-dev, api-prod
            'base_names': set()   # base names without modifiers
        }

        for subdomain in subdomains:
            # Extract the subdomain part (without parent domain)
            if subdomain.endswith(f".{self.domain}"):
                name = subdomain[:-len(self.domain) - 1]
            else:
                continue

            # Detect versioned patterns (v1, v2, etc.)
            version_match = re.match(r'^(.+?)[-._]?v(\d+)$', name, re.IGNORECASE)
            if version_match:
                patterns['versioned'].append({
                    'base': version_match.group(1),
                    'version': int(version_match.group(2)),
                    'original': name
                })
                patterns['base_names'].add(version_match.group(1))
                continue

            # Detect numbered patterns (web1, web2, etc.)
            numbered_match = re.match(r'^(.+?)(\d+)$', name)
            if numbered_match:
                patterns['numbered'].append({
                    'base': numbered_match.group(1),
                    'number': int(numbered_match.group(2)),
                    'original': name
                })
                patterns['base_names'].add(numbered_match.group(1))
                continue

            # Detect environment patterns
            for env in ['dev', 'test', 'stage', 'staging', 'prod', 'qa', 'uat']:
                if re.search(rf'[-._]{env}$', name, re.IGNORECASE):
                    base = re.sub(rf'[-._]{env}$', '', name, flags=re.IGNORECASE)
                    patterns['environment'].append({
                        'base': base,
                        'env': env,
                        'original': name
                    })
                    patterns['base_names'].add(base)
                    break
                elif re.search(rf'^{env}[-._]', name, re.IGNORECASE):
                    base = re.sub(rf'^{env}[-._]', '', name, flags=re.IGNORECASE)
                    patterns['environment'].append({
                        'base': base,
                        'env': env,
                        'original': name,
                        'prefix': True
                    })
                    patterns['base_names'].add(base)
                    break
            else:
                patterns['base_names'].add(name)

        return patterns

    def _generate_version_permutations(self, patterns: List[dict]) -> Set[str]:
        """Generate version-based permutations"""
        permutations = set()

        for pattern in patterns:
            base = pattern['base']
            current_version = pattern['version']

            # Generate nearby versions
            for v in range(1, min(current_version + 5, 20)):
                if v != current_version:
                    for sep in ['-', '_', '.', '']:
                        permutations.add(f"{base}{sep}v{v}")

        return permutations

    def _generate_numbered_permutations(self, patterns: List[dict]) -> Set[str]:
        """Generate number-based permutations"""
        permutations = set()

        for pattern in patterns:
            base = pattern['base']
            current_num = pattern['number']

            # Generate nearby numbers
            for n in range(1, min(current_num + 10, 50)):
                if n != current_num:
                    permutations.add(f"{base}{n}")
                    if n < 10:
                        permutations.add(f"{base}0{n}")

        return permutations

    def _generate_environment_permutations(self, patterns: List[dict]) -> Set[str]:
        """Generate environment-based permutations"""
        permutations = set()
        environments = ['dev', 'test', 'stage', 'staging', 'prod', 'production', 'qa', 'uat', 'sandbox', 'demo']

        for pattern in patterns:
            base = pattern['base']
            is_prefix = pattern.get('prefix', False)

            for env in environments:
                if env != pattern.get('env', '').lower():
                    for sep in ['-', '_', '.']:
                        if is_prefix:
                            permutations.add(f"{env}{sep}{base}")
                        else:
                            permutations.add(f"{base}{sep}{env}")

        return permutations

    def _generate_prefix_suffix_permutations(self, base_names: Set[str]) -> Set[str]:
        """Generate prefix/suffix combinations"""
        permutations = set()

        for base in base_names:
            # Don't permute very short names
            if len(base) < 2:
                continue

            # Add common prefixes
            for prefix in self.PREFIXES[:15]:  # Limit to avoid explosion
                for sep in ['-', '.']:
                    permutations.add(f"{prefix}{sep}{base}")

            # Add common suffixes
            for suffix in self.SUFFIXES[:15]:
                for sep in ['-', '.']:
                    permutations.add(f"{base}{sep}{suffix}")

        return permutations

    def generate(
        self,
        discovered_subdomains: Set[str],
        max_permutations: int = 1000
    ) -> Set[str]:
        """
        Generate permutations of discovered subdomains.

        Args:
            discovered_subdomains: Set of discovered subdomains
            max_permutations: Maximum number of permutations to generate

        Returns:
            Set of generated subdomain candidates (full FQDNs)
        """
        logger.info(f"Generating permutations for {len(discovered_subdomains)} subdomains")

        patterns = self._extract_patterns(discovered_subdomains)
        all_permutations = set()

        # Generate different types of permutations
        all_permutations.update(self._generate_version_permutations(patterns['versioned']))
        all_permutations.update(self._generate_numbered_permutations(patterns['numbered']))
        all_permutations.update(self._generate_environment_permutations(patterns['environment']))
        all_permutations.update(self._generate_prefix_suffix_permutations(patterns['base_names']))

        # Convert to FQDNs
        fqdns = set()
        for perm in all_permutations:
            fqdn = f"{perm}.{self.domain}"
            if fqdn not in discovered_subdomains:
                fqdns.add(fqdn)

        # Limit results
        if len(fqdns) > max_permutations:
            fqdns = set(list(fqdns)[:max_permutations])

        logger.info(f"Generated {len(fqdns)} permutation candidates")
        return fqdns

    def enumerate(
        self,
        discovered_subdomains: Dict[str, Optional[str]] = None,
        resolver_func: Callable[[str], Optional[str]] = None
    ) -> Dict[str, Optional[str]]:
        """
        Generate and validate permutations.

        Args:
            discovered_subdomains: Dict of {subdomain: ip}
            resolver_func: Optional function to resolve subdomains

        Returns:
            Dict of {subdomain: ip_address} for valid permutations
        """
        if not discovered_subdomains:
            discovered_subdomains = {}

        # Generate candidates
        candidates = self.generate(set(discovered_subdomains.keys()))

        if not candidates:
            return {}

        # Use provided resolver or default
        if resolver_func is None:
            resolver_func = self._resolve_subdomain

        logger.info(f"Validating {len(candidates)} permutation candidates")

        for candidate in candidates:
            ip = resolver_func(candidate)
            if ip:
                self._add_discovered(candidate, ip)
                logger.debug(f"Valid permutation: {candidate} -> {ip}")

        logger.info(f"Permutation engine found {len(self.discovered)} valid subdomains")
        return self.discovered
