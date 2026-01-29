"""
USFX - Ultimate Subdomain Finder for Internal Networks

A standalone CLI tool for discovering subdomains on internal networks
using custom DNS servers. Designed for air-gapped environments without
internet connectivity.
"""

__version__ = "1.2.0"
__author__ = "LACRYMARIA Team"

from .config import ScanConfig
from .engine import SubdomainEngine
from .orchestrator import SubdomainOrchestrator

__all__ = [
    "__version__",
    "ScanConfig",
    "SubdomainEngine",
    "SubdomainOrchestrator",
]
