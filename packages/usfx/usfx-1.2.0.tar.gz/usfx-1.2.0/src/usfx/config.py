"""
Scan Configuration

Dataclasses for configuring subdomain enumeration scans.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set


class WordlistSize(Enum):
    """Predefined wordlist sizes"""
    SMALL = "small"      # ~500 words - quick scan
    MEDIUM = "medium"    # ~3500 words - default
    LARGE = "large"      # ~10000 words - thorough


class OutputFormat(Enum):
    """Output format types"""
    JSON = "json"
    CSV = "csv"
    TXT = "txt"


class PipelineMode(Enum):
    """Pipeline output modes for integration with other tools"""
    NONE = "none"        # Normal output
    SUBS = "subs"        # Only subdomains (one per line)
    WEB = "web"          # Only web servers (URLs)
    IPS = "ips"          # Only IP addresses
    JSON = "json"        # JSON to stdout (no banner/progress)


@dataclass
class ScanConfig:
    """Configuration for a subdomain scan"""

    # Target domain (required)
    domain: str

    # DNS server configuration (core feature for internal networks)
    dns_servers: List[str] = field(default_factory=list)

    # Wordlist configuration
    wordlist_size: WordlistSize = WordlistSize.MEDIUM
    custom_wordlist: Optional[Path] = None

    # Performance settings
    threads: int = 30
    timeout: float = 3.0

    # Module selection (None = all modules)
    modules: Optional[Set[str]] = None

    # Additional options
    reverse_dns_ranges: List[str] = field(default_factory=list)  # CIDR ranges
    vhost_ips: List[str] = field(default_factory=list)  # IPs for vhost scanning

    # Extended scan options
    takeover: bool = False  # Enable subdomain takeover detection
    web_tech: bool = False  # Enable web technology detection
    web_ports: List[int] = field(default_factory=lambda: [80, 443, 8080, 8443])

    # Output configuration
    output_file: Optional[Path] = None
    output_format: OutputFormat = OutputFormat.JSON
    pipeline_mode: PipelineMode = field(default_factory=lambda: PipelineMode.NONE)

    # Verbosity
    verbose: bool = False
    quiet: bool = False

    def __post_init__(self):
        """Validate and normalize configuration"""
        # Normalize domain
        self.domain = self.domain.lower().strip('.')

        # Validate threads
        if self.threads < 1:
            self.threads = 1
        elif self.threads > 100:
            self.threads = 100

        # Validate timeout
        if self.timeout < 0.5:
            self.timeout = 0.5
        elif self.timeout > 30.0:
            self.timeout = 30.0

    @property
    def uses_custom_dns(self) -> bool:
        """Check if custom DNS servers are configured"""
        return len(self.dns_servers) > 0

    def get_enabled_modules(self) -> Set[str]:
        """Get the set of enabled module names"""
        all_modules = {
            "dns_bruteforce",
            "zone_transfer",
            "dnssec_walker",
            "dns_records",
            "reverse_dns",
            "cname_chaser",
            "permutation",
            "recursive_enum",
            "vhost_scanner",
            "tls_analyzer",
            "takeover",
            "web_tech",
        }

        if self.modules is None:
            # Default: exclude takeover and web_tech unless explicitly enabled
            enabled = all_modules - {"takeover", "web_tech"}
            if self.takeover:
                enabled.add("takeover")
            if self.web_tech:
                enabled.add("web_tech")
            return enabled

        return self.modules & all_modules


@dataclass
class SubdomainResult:
    """Result for a single discovered subdomain"""
    subdomain: str
    ip: Optional[str] = None
    discovered_by: str = "unknown"
    is_active: bool = False
    cname_chain: List[str] = field(default_factory=list)


@dataclass
class ModuleResult:
    """Result from a single module execution"""
    module_name: str
    found_count: int
    subdomains: List[SubdomainResult]
    duration_seconds: float
    error: Optional[str] = None


@dataclass
class TakeoverResult:
    """Takeover vulnerability result"""
    subdomain: str
    cname: str
    service: str
    status: str  # "vulnerable" or "potential"
    reason: str


@dataclass
class WebTechResult:
    """Web technology detection result"""
    subdomain: str
    url: str
    port: int
    status: int
    title: Optional[str]
    server: Optional[str]
    technologies: List[str]


@dataclass
class ScanResult:
    """Complete scan result"""
    domain: str
    total_found: int
    subdomains: List[SubdomainResult]
    module_results: List[ModuleResult]
    duration_seconds: float
    dns_servers_used: List[str]
    config: ScanConfig

    # Extended results
    takeover_results: List[TakeoverResult] = field(default_factory=list)
    web_tech_results: List[WebTechResult] = field(default_factory=list)
