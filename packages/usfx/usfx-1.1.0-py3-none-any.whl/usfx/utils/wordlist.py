"""
Wordlist Management

Manages subdomain wordlists for brute force enumeration.
Uses importlib.resources for bundled wordlists to support pip installation.
"""

import logging
from pathlib import Path
from typing import List, Optional, Set

try:
    from importlib.resources import files as pkg_files
    from importlib.resources import as_file
except ImportError:
    # Python < 3.9 fallback
    from importlib_resources import files as pkg_files
    from importlib_resources import as_file

logger = logging.getLogger(__name__)


# Built-in minimal wordlist as fallback
BUILTIN_WORDLIST = [
    # Common
    'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'ns2',
    'ns3', 'ns4', 'dns', 'dns1', 'dns2', 'mx', 'mx1', 'mx2', 'imap', 'remote',
    'blog', 'shop', 'store', 'forum', 'cpanel', 'whm', 'webdisk', 'api',

    # Development
    'dev', 'development', 'test', 'testing', 'stage', 'staging', 'prod',
    'production', 'qa', 'uat', 'sandbox', 'demo', 'beta', 'alpha', 'preview',
    'pre', 'preprod', 'pre-production', 'dev1', 'dev2', 'test1', 'test2',

    # Infrastructure
    'db', 'database', 'mysql', 'postgres', 'postgresql', 'redis', 'mongo',
    'mongodb', 'elastic', 'elasticsearch', 'cache', 'memcache', 'memcached',
    'backup', 'bak', 'server', 'server1', 'server2', 'node', 'node1', 'node2',
    'host', 'host1', 'host2', 'web', 'web1', 'web2', 'app', 'app1', 'app2',
    'worker', 'worker1', 'worker2', 'lb', 'loadbalancer', 'proxy', 'gateway',

    # Services
    'api', 'api1', 'api2', 'rest', 'graphql', 'grpc', 'ws', 'websocket',
    'socket', 'cdn', 'static', 'assets', 'images', 'img', 'media', 'files',
    'upload', 'uploads', 'download', 'downloads', 'docs', 'documentation',
    'wiki', 'help', 'support', 'status', 'health', 'monitor', 'monitoring',
    'metrics', 'logs', 'logging', 'kibana', 'grafana', 'prometheus',

    # Security & Admin
    'admin', 'administrator', 'root', 'secure', 'security', 'ssl', 'vpn',
    'portal', 'login', 'signin', 'auth', 'authentication', 'oauth', 'sso',
    'panel', 'dashboard', 'console', 'control', 'manage', 'management',

    # Cloud & DevOps
    'jenkins', 'ci', 'cd', 'build', 'deploy', 'git', 'gitlab', 'github',
    'bitbucket', 'jira', 'confluence', 'slack', 'teams', 'kubernetes', 'k8s',
    'docker', 'container', 'registry', 'helm', 'terraform', 'ansible',
    'aws', 'azure', 'gcp', 'cloud', 's3', 'storage', 'bucket',

    # Email & Communication
    'email', 'newsletter', 'mail2', 'mail3', 'webmail2', 'exchange',
    'outlook', 'autodiscover', 'autoconfig', 'calendar', 'chat', 'im',

    # Regional & Language
    'en', 'es', 'de', 'fr', 'it', 'pt', 'ru', 'zh', 'ja', 'ko',
    'us', 'eu', 'uk', 'au', 'ca', 'asia', 'emea', 'apac', 'latam',

    # Versioning
    'v1', 'v2', 'v3', 'v4', 'api-v1', 'api-v2', 'api-v3',
    'old', 'new', 'legacy', 'archive', 'archives', 'backup1', 'backup2',

    # Mobile
    'mobile', 'm', 'app-api', 'ios', 'android', 'mobile-api',

    # Internal (important for internal network enumeration)
    'internal', 'intranet', 'corp', 'corporate', 'staff', 'employee',
    'office', 'hr', 'finance', 'sales', 'marketing', 'legal',
    'dc', 'dc1', 'dc2', 'ad', 'ldap', 'kerberos', 'ntp', 'radius',
    'fileserver', 'printserver', 'sharepoint', 'exchange',

    # Misc
    'home', 'public', 'private', 'www1', 'www2', 'www3', 'web3',
    'origin', 'origin-www', 'direct', 'main', 'primary', 'secondary',
    'temp', 'tmp', 'data', 'report', 'reports', 'analytics', 'tracking',
    'crm', 'erp', 'cms', 'ecommerce', 'payment', 'payments', 'checkout',
    'cart', 'order', 'orders', 'billing', 'invoice', 'invoices',

    # Name patterns
    'web01', 'web02', 'web03', 'app01', 'app02', 'app03',
    'srv01', 'srv02', 'srv03', 'srv1', 'srv2', 'srv3',
    'dc1', 'dc2', 'datacenter', 'datacenter1', 'datacenter2'
]


def get_bundled_wordlist(size: str = 'medium') -> Path:
    """
    Get path to a bundled wordlist file.

    Args:
        size: Wordlist size - 'small', 'medium', or 'large'

    Returns:
        Path to the wordlist file

    Raises:
        FileNotFoundError: If the wordlist file doesn't exist
    """
    filename_map = {
        'small': 'wordlist_small.txt',
        'medium': 'wordlist.txt',
        'large': 'wordlist_large.txt',
    }

    filename = filename_map.get(size, 'wordlist.txt')

    try:
        # Try to get the bundled resource
        ref = pkg_files('usfx.data').joinpath(filename)
        with as_file(ref) as path:
            if path.exists():
                return path

        # Fallback: check relative to this file
        data_dir = Path(__file__).parent.parent / 'data'
        path = data_dir / filename
        if path.exists():
            return path

        raise FileNotFoundError(f"Wordlist not found: {filename}")

    except Exception as e:
        logger.warning(f"Could not load bundled wordlist: {e}")
        raise FileNotFoundError(f"Wordlist not found: {filename}")


class WordlistManager:
    """Manages subdomain wordlists with support for bundled and custom lists"""

    def __init__(self, wordlist_path: Optional[str] = None):
        """
        Initialize wordlist manager.

        Args:
            wordlist_path: Optional custom wordlist file path
        """
        self.wordlist_path = wordlist_path
        self._wordlist: Optional[List[str]] = None

    def load_wordlist(self, size: str = 'medium') -> List[str]:
        """
        Load wordlist from file or use built-in.

        Args:
            size: Wordlist size for bundled lists ('small', 'medium', 'large')

        Returns:
            List of subdomain words
        """
        if self._wordlist is not None:
            return self._wordlist

        wordlist = set()

        # Try to load from custom path first
        if self.wordlist_path:
            try:
                with open(self.wordlist_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip().lower()
                        if word and not word.startswith('#'):
                            wordlist.add(word)
                logger.info(f"Loaded {len(wordlist)} words from {self.wordlist_path}")
            except Exception as e:
                logger.error(f"Error loading custom wordlist: {e}")

        # If no custom wordlist or it failed, try bundled
        if not wordlist:
            try:
                bundled_path = get_bundled_wordlist(size)
                with open(bundled_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip().lower()
                        if word and not word.startswith('#'):
                            wordlist.add(word)
                logger.info(f"Loaded {len(wordlist)} words from bundled {size} wordlist")
            except FileNotFoundError:
                logger.warning("Bundled wordlist not found, using built-in minimal list")

        # Always add built-in words as fallback
        wordlist.update(BUILTIN_WORDLIST)

        self._wordlist = sorted(list(wordlist))
        logger.info(f"Total wordlist size: {len(self._wordlist)}")

        return self._wordlist

    def get_wordlist(
        self,
        size: str = 'medium',
        max_words: Optional[int] = None,
        include_numbers: bool = True,
        include_env: bool = True
    ) -> List[str]:
        """
        Get wordlist with optional filtering and expansion.

        Args:
            size: Wordlist size for bundled lists
            max_words: Maximum number of words to return
            include_numbers: Include numbered variations (api1, api2, etc.)
            include_env: Include environment variations (api-dev, api-prod, etc.)

        Returns:
            List of subdomain words
        """
        base_list = self.load_wordlist(size)
        result = set(base_list)

        if include_numbers:
            # Add numbered variations
            for word in list(result)[:500]:  # Limit base words for expansion
                for i in range(1, 6):
                    result.add(f"{word}{i}")
                    result.add(f"{word}0{i}")

        if include_env:
            # Add environment variations
            envs = ['dev', 'test', 'stage', 'staging', 'prod', 'qa', 'uat']
            for word in list(result)[:200]:  # Limit base words
                for env in envs:
                    result.add(f"{word}-{env}")
                    result.add(f"{env}-{word}")

        result_list = sorted(list(result))

        if max_words:
            result_list = result_list[:max_words]

        return result_list

    def add_discovered(self, subdomains: Set[str]) -> None:
        """
        Add newly discovered subdomains to wordlist.

        Args:
            subdomains: Set of discovered subdomains
        """
        if self._wordlist is None:
            self.load_wordlist()

        existing = set(self._wordlist)
        new_words = []

        for subdomain in subdomains:
            parts = subdomain.split('.')
            for part in parts:
                if part and part not in existing:
                    new_words.append(part)
                    existing.add(part)

        if new_words:
            self._wordlist.extend(new_words)
            self._wordlist.sort()
            logger.debug(f"Added {len(new_words)} new words to wordlist")

    def save_wordlist(self, path: str) -> None:
        """
        Save current wordlist to file.

        Args:
            path: Path to save the wordlist
        """
        if self._wordlist is None:
            self.load_wordlist()

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("# Subdomain Wordlist\n")
                f.write("# Generated by USFX\n\n")
                for word in self._wordlist:
                    f.write(f"{word}\n")
            logger.info(f"Saved {len(self._wordlist)} words to {path}")
        except Exception as e:
            logger.error(f"Error saving wordlist: {e}")
