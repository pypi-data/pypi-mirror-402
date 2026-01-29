"""
Subdomain Enumeration Orchestrator

Manages the execution order of enumeration modules and aggregates results.
Uses parallel execution within phases for maximum speed.

This is a simplified orchestrator for internal networks that:
- Does NOT use external APIs
- Does NOT store results in a database
- Keeps all results in memory
"""

import logging
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from .utils.validator import SubdomainValidator
from .utils.wildcard import WildcardDetector

if TYPE_CHECKING:
    from .config import ScanConfig
    from .utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


class Phase(Enum):
    """Enumeration phases"""
    QUICK_DISCOVERY = "quick_discovery"
    DNS_ENUMERATION = "dns_enumeration"
    EXTENSION = "extension"
    VALIDATION = "validation"


@dataclass
class ModuleResult:
    """Result from a single module"""
    module_name: str
    found_count: int
    subdomains: Dict[str, Optional[str]]
    duration_seconds: float
    error: Optional[str] = None


@dataclass
class PhaseResult:
    """Result from a phase"""
    phase: Phase
    modules: List[ModuleResult]
    total_found: int
    duration_seconds: float


@dataclass
class OrchestrationState:
    """Current state of the orchestration"""
    domain: str
    current_phase: Optional[Phase] = None
    current_module: Optional[str] = None
    progress: int = 0
    total_found: int = 0
    discovered: Dict[str, dict] = field(default_factory=dict)
    phase_results: List[PhaseResult] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    is_cancelled: bool = False


class SubdomainOrchestrator:
    """Orchestrates subdomain enumeration modules"""

    # Phase weight for overall progress calculation
    PHASE_WEIGHTS = {
        Phase.QUICK_DISCOVERY: (0, 15),      # 0-15%
        Phase.DNS_ENUMERATION: (15, 60),     # 15-60%
        Phase.EXTENSION: (60, 90),           # 60-90%
        Phase.VALIDATION: (90, 100),         # 90-100%
    }

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        config: Optional['ScanConfig'] = None
    ):
        """
        Initialize orchestrator.

        Args:
            domain: Target domain
            resolver: Custom DNS resolver
            config: Scan configuration
        """
        self.domain = domain.lower().strip('.')
        self.state = OrchestrationState(domain=self.domain)
        self.config = config

        # Create resolver
        if resolver:
            self.resolver = resolver
        else:
            from .utils.dns_resolver import InternalDNSResolver
            dns_servers = config.dns_servers if config else None
            timeout = config.timeout if config else 3.0
            self.resolver = InternalDNSResolver(dns_servers=dns_servers, timeout=timeout)

        self.validator = SubdomainValidator(resolver=self.resolver)
        self.wildcard_detector = WildcardDetector(domain, self.resolver)

        # Progress callback
        self.progress_callback: Optional[Callable[[OrchestrationState], None]] = None

        # Lock for thread-safe result collection
        self._results_lock = threading.Lock()

    def set_progress_callback(self, callback: Callable[[OrchestrationState], None]):
        """Set callback for progress updates"""
        self.progress_callback = callback

    def _update_progress(self, phase: Phase, module: str, phase_progress: int):
        """Update and broadcast progress"""
        self.state.current_phase = phase
        self.state.current_module = module

        # Calculate overall progress based on phase and phase_progress
        phase_start, phase_end = self.PHASE_WEIGHTS.get(phase, (0, 100))
        phase_range = phase_end - phase_start
        overall_progress = phase_start + (phase_progress * phase_range // 100)

        self.state.progress = overall_progress

        if self.progress_callback:
            self.progress_callback(self.state)

    def _add_results(self, results: Dict[str, Optional[str]], module_name: str):
        """Add results from a module (thread-safe)"""
        with self._results_lock:
            for subdomain, ip in results.items():
                if subdomain not in self.state.discovered:
                    self.state.discovered[subdomain] = {
                        'ip': ip,
                        'discovered_by': module_name,
                        'is_active': ip is not None
                    }
                    self.state.total_found += 1
                elif ip and not self.state.discovered[subdomain].get('ip'):
                    # Update IP if we have one now
                    self.state.discovered[subdomain]['ip'] = ip
                    self.state.discovered[subdomain]['is_active'] = True

    def _run_module_task(
        self,
        module_factory: Callable,
        module_name: str,
        needs_known_subs: bool = False,
        **kwargs
    ) -> ModuleResult:
        """Run a single module as a task"""
        start_time = time.time()

        # Check cancellation before starting
        if self.state.is_cancelled:
            return ModuleResult(
                module_name=module_name,
                found_count=0,
                subdomains={},
                duration_seconds=0,
                error="cancelled"
            )

        try:
            module = module_factory()

            # Get current state snapshot for modules that need it
            if needs_known_subs:
                with self._results_lock:
                    known_subs = {k: v.get('ip') for k, v in self.state.discovered.items()}

                if module_name == "tls_analyzer":
                    results = module.enumerate(known_hosts=known_subs)
                elif module_name == "permutation":
                    def resolve(subdomain):
                        if self.state.is_cancelled:
                            return None
                        return self.resolver.resolve_a(subdomain)
                    results = module.enumerate(known_subs, resolver_func=resolve)
                else:
                    results = module.enumerate(known_subs)
            else:
                results = module.enumerate()

            # Check cancellation after module completion
            if self.state.is_cancelled:
                return ModuleResult(
                    module_name=module_name,
                    found_count=0,
                    subdomains={},
                    duration_seconds=time.time() - start_time,
                    error="cancelled"
                )

            duration = time.time() - start_time
            self._add_results(results, module_name)

            logger.info(f"Module {module_name} found {len(results)} subdomains in {duration:.1f}s")

            return ModuleResult(
                module_name=module_name,
                found_count=len(results),
                subdomains=results,
                duration_seconds=duration
            )

        except Exception as e:
            if self.state.is_cancelled:
                return ModuleResult(
                    module_name=module_name,
                    found_count=0,
                    subdomains={},
                    duration_seconds=time.time() - start_time,
                    error="cancelled"
                )
            logger.error(f"Error in module {module_name}: {e}")
            return ModuleResult(
                module_name=module_name,
                found_count=0,
                subdomains={},
                duration_seconds=time.time() - start_time,
                error=str(e)
            )

    def _run_modules_parallel(
        self,
        phase: Phase,
        module_tasks: List[Tuple[Callable, str, dict]],
        max_workers: int = 10
    ) -> List[ModuleResult]:
        """Run multiple modules in parallel"""
        results = []
        completed_count = 0
        total_modules = len(module_tasks)

        if self.state.is_cancelled:
            return results

        module_names = [name for _, name, _ in module_tasks]
        self._update_progress(phase, f"parallel: {', '.join(module_names)}", 0)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures: Dict[Future, str] = {}
            for module_factory, module_name, kwargs in module_tasks:
                if self.state.is_cancelled:
                    break
                future = executor.submit(
                    self._run_module_task,
                    module_factory,
                    module_name,
                    **kwargs
                )
                futures[future] = module_name

            for future in as_completed(futures):
                if self.state.is_cancelled:
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                module_name = futures[future]
                try:
                    result = future.result(timeout=300)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Module {module_name} failed: {e}")
                    results.append(ModuleResult(
                        module_name=module_name,
                        found_count=0,
                        subdomains={},
                        duration_seconds=0,
                        error=str(e)
                    ))

                completed_count += 1
                progress = int(completed_count * 100 / total_modules)
                self._update_progress(phase, module_name, progress)

        return results

    def _get_enabled_modules(self) -> Set[str]:
        """Get set of enabled module names"""
        if self.config and self.config.modules:
            return self.config.modules
        return {
            "zone_transfer", "dns_records", "dns_bruteforce", "dnssec_walker",
            "reverse_dns", "cname_chaser", "permutation", "recursive_enum",
            "vhost_scanner", "tls_analyzer"
        }

    def run_phase1_quick_discovery(self) -> PhaseResult:
        """Phase 1: Quick Discovery - Zone Transfer and DNS Records"""
        from .modules.zone_transfer import ZoneTransfer
        from .modules.dns_records import DNSRecordMiner

        phase_start = time.time()
        results = []
        enabled = self._get_enabled_modules()

        # Get config values
        threads = self.config.threads if self.config else 30

        module_tasks = []

        if "zone_transfer" in enabled:
            module_tasks.append((
                lambda: ZoneTransfer(self.domain, self.resolver),
                "zone_transfer",
                {}
            ))

        if "dns_records" in enabled:
            module_tasks.append((
                lambda: DNSRecordMiner(self.domain, self.resolver),
                "dns_records",
                {}
            ))

        if module_tasks:
            results = self._run_modules_parallel(Phase.QUICK_DISCOVERY, module_tasks, max_workers=2)

        self._update_progress(Phase.QUICK_DISCOVERY, "complete", 100)

        return PhaseResult(
            phase=Phase.QUICK_DISCOVERY,
            modules=results,
            total_found=sum(r.found_count for r in results),
            duration_seconds=time.time() - phase_start
        )

    def run_phase2_dns_enumeration(self) -> PhaseResult:
        """Phase 2: DNS Enumeration - Brute force and DNSSEC"""
        from .modules.dns_bruteforce import DNSBruteforcer
        from .modules.dnssec_walker import DNSSECWalker

        phase_start = time.time()
        results = []
        enabled = self._get_enabled_modules()

        threads = self.config.threads if self.config else 30
        wordlist_size = self.config.wordlist_size.value if self.config else 'medium'
        wordlist_path = str(self.config.custom_wordlist) if self.config and self.config.custom_wordlist else None

        # Cancellation check function for modules
        cancel_check = lambda: self.state.is_cancelled

        module_tasks = []

        if "dns_bruteforce" in enabled:
            module_tasks.append((
                lambda: DNSBruteforcer(
                    self.domain, self.resolver,
                    wordlist_path=wordlist_path,
                    wordlist_size=wordlist_size,
                    threads=threads,
                    cancel_check=cancel_check
                ),
                "dns_bruteforce",
                {}
            ))

        if "dnssec_walker" in enabled:
            module_tasks.append((
                lambda: DNSSECWalker(self.domain, self.resolver),
                "dnssec_walker",
                {}
            ))

        if module_tasks:
            results = self._run_modules_parallel(Phase.DNS_ENUMERATION, module_tasks, max_workers=2)

        self._update_progress(Phase.DNS_ENUMERATION, "complete", 100)

        return PhaseResult(
            phase=Phase.DNS_ENUMERATION,
            modules=results,
            total_found=sum(r.found_count for r in results),
            duration_seconds=time.time() - phase_start
        )

    def run_phase3_extension(self) -> PhaseResult:
        """Phase 3: Extension - Permutation, Reverse DNS, Recursive, VHost, TLS"""
        from .modules.permutation import PermutationEngine
        from .modules.reverse_dns import ReverseDNS
        from .modules.recursive_enum import RecursiveEnumerator
        from .modules.vhost_scanner import VHostScanner
        from .modules.tls_analyzer import TLSAnalyzer
        from .modules.cname_chaser import CNAMEChaser

        phase_start = time.time()
        results = []
        enabled = self._get_enabled_modules()

        threads = self.config.threads if self.config else 30
        vhost_ips = self.config.vhost_ips if self.config else []
        reverse_ranges = self.config.reverse_dns_ranges if self.config else []

        module_tasks = []

        if "permutation" in enabled:
            module_tasks.append((
                lambda: PermutationEngine(self.domain, self.resolver),
                "permutation",
                {"needs_known_subs": True}
            ))

        if "cname_chaser" in enabled:
            module_tasks.append((
                lambda: CNAMEChaser(self.domain, self.resolver, threads=threads),
                "cname_chaser",
                {"needs_known_subs": True}
            ))

        if "recursive_enum" in enabled:
            module_tasks.append((
                lambda: RecursiveEnumerator(self.domain, self.resolver, threads=threads),
                "recursive_enum",
                {"needs_known_subs": True}
            ))

        if "tls_analyzer" in enabled:
            module_tasks.append((
                lambda: TLSAnalyzer(self.domain, self.resolver, threads=threads),
                "tls_analyzer",
                {"needs_known_subs": True}
            ))

        if module_tasks:
            results = self._run_modules_parallel(Phase.EXTENSION, module_tasks, max_workers=4)

        # Run reverse DNS separately (may need special IP ranges)
        if "reverse_dns" in enabled:
            self._update_progress(Phase.EXTENSION, "reverse_dns", 80)
            reverse_module = ReverseDNS(self.domain, self.resolver, threads=threads)
            with self._results_lock:
                known_ips = {v.get('ip') for v in self.state.discovered.values() if v.get('ip')}
            reverse_results = reverse_module.enumerate(
                additional_ips=known_ips,
                ip_ranges=reverse_ranges if reverse_ranges else None
            )
            self._add_results(reverse_results, "reverse_dns")
            results.append(ModuleResult(
                module_name="reverse_dns",
                found_count=len(reverse_results),
                subdomains=reverse_results,
                duration_seconds=0
            ))

        # Run vhost scanner separately (may need special IPs)
        if "vhost_scanner" in enabled and vhost_ips:
            self._update_progress(Phase.EXTENSION, "vhost_scanner", 90)
            vhost_module = VHostScanner(self.domain, self.resolver, threads=threads)
            with self._results_lock:
                known_subs = {k: v.get('ip') for k, v in self.state.discovered.items()}
            vhost_results = vhost_module.enumerate(known_subs, vhost_ips=vhost_ips)
            self._add_results(vhost_results, "vhost_scanner")
            results.append(ModuleResult(
                module_name="vhost_scanner",
                found_count=len(vhost_results),
                subdomains=vhost_results,
                duration_seconds=0
            ))

        self._update_progress(Phase.EXTENSION, "complete", 100)

        return PhaseResult(
            phase=Phase.EXTENSION,
            modules=results,
            total_found=sum(r.found_count for r in results),
            duration_seconds=time.time() - phase_start
        )

    def run_phase4_validation(self) -> PhaseResult:
        """Phase 4: Validation - DNS resolution verification and wildcard filtering"""
        phase_start = time.time()

        self._update_progress(Phase.VALIDATION, "validating", 0)

        # Detect wildcards
        has_wildcard, wildcard_ips = self.wildcard_detector.detect()

        # Validate all discovered subdomains
        subdomains_to_validate = set(self.state.discovered.keys())
        threads = self.config.threads if self.config else 30
        validated = self.validator.validate_batch(subdomains_to_validate, threads=threads)

        # Update state with validation results
        removed_count = 0
        for subdomain, result in validated.items():
            if subdomain in self.state.discovered:
                if result['ip']:
                    # Check wildcard
                    if has_wildcard and result['ip'] in wildcard_ips:
                        del self.state.discovered[subdomain]
                        removed_count += 1
                    else:
                        self.state.discovered[subdomain]['ip'] = result['ip']
                        self.state.discovered[subdomain]['is_active'] = True
                else:
                    self.state.discovered[subdomain]['is_active'] = False

        self.state.total_found = len(self.state.discovered)

        self._update_progress(Phase.VALIDATION, "complete", 100)

        if removed_count > 0:
            logger.info(f"Filtered {removed_count} wildcard results")

        logger.info(f"Validation complete: {self.state.total_found} valid subdomains")

        return PhaseResult(
            phase=Phase.VALIDATION,
            modules=[ModuleResult(
                module_name="validation",
                found_count=self.state.total_found,
                subdomains={},
                duration_seconds=time.time() - phase_start
            )],
            total_found=self.state.total_found,
            duration_seconds=time.time() - phase_start
        )

    def cancel(self):
        """Cancel the orchestration"""
        self.state.is_cancelled = True

    def run_all(self) -> OrchestrationState:
        """Run all phases"""
        logger.info(f"Starting subdomain enumeration for {self.domain}")

        # Phase 1: Quick Discovery
        result = self.run_phase1_quick_discovery()
        self.state.phase_results.append(result)
        if self.state.is_cancelled:
            return self.state

        # Phase 2: DNS Enumeration
        result = self.run_phase2_dns_enumeration()
        self.state.phase_results.append(result)
        if self.state.is_cancelled:
            return self.state

        # Phase 3: Extension
        result = self.run_phase3_extension()
        self.state.phase_results.append(result)
        if self.state.is_cancelled:
            return self.state

        # Phase 4: Validation
        result = self.run_phase4_validation()
        self.state.phase_results.append(result)

        logger.info(f"Enumeration complete: {self.state.total_found} subdomains found")
        return self.state
