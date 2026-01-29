"""
USFX Modules

Offline-capable modules for subdomain enumeration:
- dns_bruteforce: Wordlist-based DNS queries
- zone_transfer: AXFR zone transfer attempts
- dnssec_walker: NSEC/NSEC3 zone walking
- dns_records: MX/NS/TXT/SRV/SOA/CAA analysis
- reverse_dns: PTR lookups on IP ranges
- cname_chaser: CNAME chain tracking
- permutation: Subdomain variation generation
- recursive_enum: Sub-subdomain discovery
- vhost_scanner: Host header brute force
- tls_analyzer: TLS certificate SAN extraction
- takeover: Subdomain takeover vulnerability detection
- web_tech: Web technology detection (Wappalyzer)
"""

from .base import BaseModule
from .dns_bruteforce import DNSBruteforcer
from .zone_transfer import ZoneTransfer
from .dnssec_walker import DNSSECWalker
from .dns_records import DNSRecordMiner
from .reverse_dns import ReverseDNS
from .cname_chaser import CNAMEChaser
from .permutation import PermutationEngine
from .recursive_enum import RecursiveEnumerator
from .vhost_scanner import VHostScanner
from .tls_analyzer import TLSAnalyzer
from .takeover import TakeoverDetector
from .web_tech import WebTechDetector

__all__ = [
    "BaseModule",
    "DNSBruteforcer",
    "ZoneTransfer",
    "DNSSECWalker",
    "DNSRecordMiner",
    "ReverseDNS",
    "CNAMEChaser",
    "PermutationEngine",
    "RecursiveEnumerator",
    "VHostScanner",
    "TLSAnalyzer",
    "TakeoverDetector",
    "WebTechDetector",
]
