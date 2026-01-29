"""
Subdomain Engine

Main entry point for subdomain enumeration. Provides a simple interface
for running scans and getting results.

This is a simplified engine for internal networks that:
- Does NOT use external databases
- Does NOT use external APIs
- Keeps all results in memory
- Returns results directly
"""

import logging
import time
from typing import List, Optional

from .config import ModuleResult, ScanConfig, ScanResult, SubdomainResult, TakeoverResult, WebTechResult
from .orchestrator import SubdomainOrchestrator

logger = logging.getLogger(__name__)


class SubdomainEngine:
    """Main subdomain enumeration engine"""

    def __init__(self):
        """Initialize the engine"""
        self.current_scan: Optional[SubdomainOrchestrator] = None

    def scan(
        self,
        config: ScanConfig,
        progress_callback=None
    ) -> ScanResult:
        """
        Run a full subdomain scan.

        Args:
            config: Scan configuration
            progress_callback: Optional callback for progress updates

        Returns:
            ScanResult with discovered subdomains
        """
        start_time = time.time()

        logger.info(f"Starting subdomain scan for {config.domain}")
        if config.dns_servers:
            logger.info(f"Using DNS servers: {', '.join(config.dns_servers)}")
        else:
            logger.info("Using system default DNS servers")

        # Create resolver
        from .utils.dns_resolver import InternalDNSResolver
        resolver = InternalDNSResolver(
            dns_servers=config.dns_servers if config.dns_servers else None,
            timeout=config.timeout
        )

        # Create orchestrator
        orchestrator = SubdomainOrchestrator(
            domain=config.domain,
            resolver=resolver,
            config=config
        )

        self.current_scan = orchestrator

        # Set up progress callback
        if progress_callback:
            orchestrator.set_progress_callback(progress_callback)

        try:
            # Run enumeration
            state = orchestrator.run_all()

            duration = time.time() - start_time

            # Build result
            subdomains = []
            for subdomain, info in state.discovered.items():
                subdomains.append(SubdomainResult(
                    subdomain=subdomain,
                    ip=info.get('ip'),
                    discovered_by=info.get('discovered_by', 'unknown'),
                    is_active=info.get('is_active', False),
                ))

            # Sort by subdomain name
            subdomains.sort(key=lambda x: x.subdomain)

            # Build module results
            module_results = []
            for phase_result in state.phase_results:
                for module in phase_result.modules:
                    module_results.append(ModuleResult(
                        module_name=module.module_name,
                        found_count=module.found_count,
                        subdomains=[
                            SubdomainResult(subdomain=s, ip=ip)
                            for s, ip in module.subdomains.items()
                        ],
                        duration_seconds=module.duration_seconds,
                        error=module.error
                    ))

            # Build takeover results
            takeover_results = []
            for t in state.takeover_results:
                takeover_results.append(TakeoverResult(
                    subdomain=t['subdomain'],
                    cname=t['cname'],
                    service=t['service'],
                    status=t['status'],
                    reason=t['reason']
                ))

            # Build web tech results
            web_tech_results = []
            for w in state.web_tech_results:
                web_tech_results.append(WebTechResult(
                    subdomain=w['subdomain'],
                    url=w['url'],
                    port=w['port'],
                    status=w['status'],
                    title=w.get('title'),
                    server=w.get('server'),
                    technologies=w.get('technologies', [])
                ))

            return ScanResult(
                domain=config.domain,
                total_found=state.total_found,
                subdomains=subdomains,
                module_results=module_results,
                duration_seconds=duration,
                dns_servers_used=resolver.dns_servers,
                config=config,
                takeover_results=takeover_results,
                web_tech_results=web_tech_results
            )

        except Exception as e:
            logger.error(f"Scan failed for {config.domain}: {e}")
            duration = time.time() - start_time

            return ScanResult(
                domain=config.domain,
                total_found=0,
                subdomains=[],
                module_results=[],
                duration_seconds=duration,
                dns_servers_used=config.dns_servers if config.dns_servers else [],
                config=config
            )

        finally:
            self.current_scan = None

    def cancel_scan(self) -> bool:
        """
        Cancel the current scan.

        Returns:
            True if cancelled, False if no scan was running
        """
        if self.current_scan:
            self.current_scan.cancel()
            return True
        return False

    def quick_scan(
        self,
        domain: str,
        dns_servers: Optional[List[str]] = None,
        threads: int = 30
    ) -> ScanResult:
        """
        Run a quick scan with default settings.

        Args:
            domain: Target domain
            dns_servers: Optional list of DNS server IPs
            threads: Number of threads

        Returns:
            ScanResult with discovered subdomains
        """
        from .config import WordlistSize

        config = ScanConfig(
            domain=domain,
            dns_servers=dns_servers or [],
            wordlist_size=WordlistSize.SMALL,
            threads=threads
        )

        return self.scan(config)

    def full_scan(
        self,
        domain: str,
        dns_servers: Optional[List[str]] = None,
        threads: int = 50
    ) -> ScanResult:
        """
        Run a full scan with comprehensive settings.

        Args:
            domain: Target domain
            dns_servers: Optional list of DNS server IPs
            threads: Number of threads

        Returns:
            ScanResult with discovered subdomains
        """
        from .config import WordlistSize

        config = ScanConfig(
            domain=domain,
            dns_servers=dns_servers or [],
            wordlist_size=WordlistSize.LARGE,
            threads=threads
        )

        return self.scan(config)


# Global engine instance
_engine: Optional[SubdomainEngine] = None


def get_engine() -> SubdomainEngine:
    """Get or create the global subdomain engine"""
    global _engine
    if _engine is None:
        _engine = SubdomainEngine()
    return _engine
