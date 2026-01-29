"""
USFX CLI

Command-line interface for the Ultimate Subdomain Finder.
Supports custom DNS servers for internal network enumeration.
"""

import logging
import os
import signal
import sys
import threading
from pathlib import Path
from typing import List, Optional, Tuple

import click

# Global state for signal handling
_current_engine = None
_interrupted = False

from . import __version__
from .config import OutputFormat, PipelineMode, ScanConfig, WordlistSize
from .engine import SubdomainEngine
from .utils.output import ConsoleOutput, OutputFormatter


def setup_logging(verbose: bool, quiet: bool) -> None:
    """Configure logging based on verbosity settings"""
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s' if not verbose else '%(asctime)s %(levelname)s [%(name)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )

    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def parse_modules(modules_str: Optional[str]) -> Optional[set]:
    """Parse comma-separated module list"""
    if not modules_str:
        return None

    valid_modules = {
        'bruteforce', 'dns_bruteforce',
        'zone', 'zone_transfer',
        'dnssec', 'dnssec_walker',
        'records', 'dns_records',
        'reverse', 'reverse_dns',
        'cname', 'cname_chaser',
        'permutation',
        'recursive', 'recursive_enum',
        'vhost', 'vhost_scanner',
        'tls', 'tls_analyzer',
        'takeover',
        'webtech', 'web_tech',
    }

    # Normalize module names
    module_map = {
        'bruteforce': 'dns_bruteforce',
        'zone': 'zone_transfer',
        'dnssec': 'dnssec_walker',
        'records': 'dns_records',
        'reverse': 'reverse_dns',
        'cname': 'cname_chaser',
        'recursive': 'recursive_enum',
        'vhost': 'vhost_scanner',
        'tls': 'tls_analyzer',
        'webtech': 'web_tech',
    }

    modules = set()
    for m in modules_str.split(','):
        m = m.strip().lower()
        if m in module_map:
            modules.add(module_map[m])
        elif m in valid_modules:
            modules.add(m)
        else:
            raise click.BadParameter(f"Unknown module: {m}")

    return modules


@click.command()
@click.argument('domain')
@click.option(
    '-d', '--dns-server',
    'dns_servers',
    multiple=True,
    help='DNS server IP address (can be specified multiple times for multiple servers)'
)
@click.option(
    '-w', '--wordlist',
    'wordlist_path',
    type=click.Path(exists=True),
    help='Path to custom wordlist file'
)
@click.option(
    '-s', '--wordlist-size',
    'wordlist_size',
    type=click.Choice(['small', 'medium', 'large']),
    default='medium',
    help='Size of bundled wordlist (default: medium)'
)
@click.option(
    '-o', '--output',
    'output_path',
    type=click.Path(),
    help='Output file path'
)
@click.option(
    '-f', '--format',
    'output_format',
    type=click.Choice(['json', 'csv', 'txt']),
    default='json',
    help='Output format (default: json)'
)
@click.option(
    '-t', '--threads',
    default=30,
    type=click.IntRange(1, 100),
    help='Number of parallel threads (default: 30)'
)
@click.option(
    '--timeout',
    default=3.0,
    type=click.FloatRange(0.5, 30.0),
    help='DNS query timeout in seconds (default: 3.0)'
)
@click.option(
    '-m', '--modules',
    'modules_str',
    help='Comma-separated list of modules to run (e.g., bruteforce,zone,dnssec)'
)
@click.option(
    '--reverse-range',
    'reverse_ranges',
    multiple=True,
    help='CIDR range for reverse DNS scanning (e.g., 192.168.0.0/24)'
)
@click.option(
    '--vhost-ip',
    'vhost_ips',
    multiple=True,
    help='IP address for virtual host scanning'
)
@click.option(
    '--takeover',
    is_flag=True,
    help='Enable subdomain takeover vulnerability detection'
)
@click.option(
    '--web-tech',
    'web_tech',
    is_flag=True,
    help='Enable web technology detection (Wappalyzer)'
)
@click.option(
    '--web-ports',
    'web_ports',
    default='80,443,8080,8443',
    help='Comma-separated ports for web tech scanning (default: 80,443,8080,8443)'
)
@click.option(
    '--pipe-subs',
    is_flag=True,
    help='Pipeline mode: output only subdomains (one per line)'
)
@click.option(
    '--pipe-web',
    is_flag=True,
    help='Pipeline mode: output only web URLs (one per line)'
)
@click.option(
    '--pipe-ips',
    is_flag=True,
    help='Pipeline mode: output only IP addresses (one per line)'
)
@click.option(
    '--pipe-json',
    is_flag=True,
    help='Pipeline mode: JSON output to stdout (no banner/progress)'
)
@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='Enable verbose output'
)
@click.option(
    '-q', '--quiet',
    is_flag=True,
    help='Suppress non-essential output'
)
@click.option(
    '--no-color',
    is_flag=True,
    help='Disable colored output'
)
@click.version_option(version=__version__, prog_name='USFX')
def main(
    domain: str,
    dns_servers: Tuple[str, ...],
    wordlist_path: Optional[str],
    wordlist_size: str,
    output_path: Optional[str],
    output_format: str,
    threads: int,
    timeout: float,
    modules_str: Optional[str],
    reverse_ranges: Tuple[str, ...],
    vhost_ips: Tuple[str, ...],
    takeover: bool,
    web_tech: bool,
    web_ports: str,
    pipe_subs: bool,
    pipe_web: bool,
    pipe_ips: bool,
    pipe_json: bool,
    verbose: bool,
    quiet: bool,
    no_color: bool
) -> None:
    """
    USFX - Ultimate Subdomain Finder X for Internal Networks

    Discover subdomains on internal networks using custom DNS servers.

    Examples:

        # Basic scan using system DNS
        usfx corp.local

        # Scan with internal DNS server
        usfx corp.local -d 192.168.1.1

        # Scan with multiple DNS servers
        usfx corp.local -d 192.168.1.1 -d 192.168.1.2

        # Quick scan with small wordlist
        usfx corp.local -d 10.0.0.1 -s small

        # Full scan with large wordlist
        usfx corp.local -d 10.0.0.1 -s large -t 50

        # Save results to JSON file
        usfx corp.local -d 10.0.0.1 -o results.json

        # Save as CSV
        usfx corp.local -d 10.0.0.1 -o results.csv -f csv

        # Only run specific modules
        usfx corp.local -d 10.0.0.1 -m bruteforce,zone,records

        # Scan with reverse DNS range
        usfx corp.local -d 10.0.0.1 --reverse-range 192.168.0.0/16

        # Scan with vhost discovery on specific IP
        usfx corp.local -d 10.0.0.1 --vhost-ip 192.168.1.100

        # Enable subdomain takeover detection
        usfx corp.local -d 10.0.0.1 --takeover

        # Enable web technology detection
        usfx corp.local -d 10.0.0.1 --web-tech

        # Pipeline mode: subdomains only (for piping to other tools)
        usfx corp.local -d 10.0.0.1 --pipe-subs | httpx

        # Pipeline mode: JSON to stdout
        usfx corp.local -d 10.0.0.1 --pipe-json | jq '.subdomains'
    """
    # Determine pipeline mode
    pipeline_mode = PipelineMode.NONE
    if pipe_subs:
        pipeline_mode = PipelineMode.SUBS
    elif pipe_web:
        pipeline_mode = PipelineMode.WEB
    elif pipe_ips:
        pipeline_mode = PipelineMode.IPS
    elif pipe_json:
        pipeline_mode = PipelineMode.JSON

    # Pipeline modes force quiet mode (no banner/progress)
    if pipeline_mode != PipelineMode.NONE:
        quiet = True

    # Parse web ports
    try:
        parsed_web_ports = [int(p.strip()) for p in web_ports.split(',')]
    except ValueError:
        click.echo("Error: Invalid web ports format", err=True)
        sys.exit(1)

    # Setup logging
    setup_logging(verbose, quiet)

    # Create console output helper
    console = ConsoleOutput(use_rich=not no_color, quiet=quiet)

    # Print banner
    console.print_banner(__version__)

    # Parse modules
    try:
        modules = parse_modules(modules_str)
    except click.BadParameter as e:
        console.print_error(str(e))
        sys.exit(1)

    # Create scan configuration
    try:
        config = ScanConfig(
            domain=domain,
            dns_servers=list(dns_servers),
            wordlist_size=WordlistSize(wordlist_size),
            custom_wordlist=Path(wordlist_path) if wordlist_path else None,
            threads=threads,
            timeout=timeout,
            modules=modules,
            reverse_dns_ranges=list(reverse_ranges),
            vhost_ips=list(vhost_ips),
            takeover=takeover,
            web_tech=web_tech,
            web_ports=parsed_web_ports,
            output_file=Path(output_path) if output_path else None,
            output_format=OutputFormat(output_format),
            pipeline_mode=pipeline_mode,
            verbose=verbose,
            quiet=quiet
        )
    except Exception as e:
        console.print_error(f"Invalid configuration: {e}")
        sys.exit(1)

    # Print configuration
    enabled_modules = sorted(config.get_enabled_modules())
    console.print_config(
        domain=config.domain,
        dns_servers=config.dns_servers,
        modules=enabled_modules
    )

    # Check DNS connectivity if custom DNS servers specified
    if dns_servers and not quiet:
        from .utils.dns_resolver import InternalDNSResolver
        test_resolver = InternalDNSResolver(dns_servers=list(dns_servers), timeout=timeout)
        is_reachable, error_msg = test_resolver.check_connectivity(domain)
        if not is_reachable:
            console.print_warning(f"DNS connectivity issue: {error_msg}")
            console.print_warning("Scan may produce incomplete results")

    # Create engine and run scan
    global _current_engine, _interrupted
    engine = SubdomainEngine()
    _current_engine = engine
    _interrupted = False

    # Signal handler for Ctrl+C
    def signal_handler(signum, frame):
        global _interrupted
        if _interrupted:
            # Second Ctrl+C - force exit immediately
            if not quiet:
                click.echo("\nForce exit.", err=True)
            os._exit(130)

        _interrupted = True
        if not quiet:
            click.echo("\n\nInterrupted. Stopping scan...", err=True)

        if _current_engine:
            _current_engine.cancel_scan()

    # Register signal handler
    original_handler = signal.signal(signal.SIGINT, signal_handler)

    # Progress tracking
    last_phase = None

    def progress_callback(state):
        nonlocal last_phase
        if _interrupted:
            return
        if state.current_phase and state.current_phase != last_phase:
            console.print_phase(state.current_phase.value)
            last_phase = state.current_phase

    try:
        result = engine.scan(config, progress_callback=progress_callback if not quiet else None)

        if _interrupted:
            sys.exit(130)

    except KeyboardInterrupt:
        if not quiet:
            click.echo("\nScan cancelled.", err=True)
        sys.exit(130)
    except Exception as e:
        if not _interrupted:
            console.print_error(f"Scan failed: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
        sys.exit(1)
    finally:
        signal.signal(signal.SIGINT, original_handler)
        _current_engine = None

    # Handle pipeline mode output
    if pipeline_mode != PipelineMode.NONE:
        output = OutputFormatter.to_pipeline(result, pipeline_mode)
        click.echo(output)
    else:
        # Print results
        console.print_result_table(result)
        console.print_summary(result)

        # Print takeover results if available
        if result.takeover_results:
            console.print_takeover_results(result.takeover_results)

        # Print web tech results if available
        if result.web_tech_results:
            console.print_web_tech_results(result.web_tech_results)

    # Write output file if requested
    if config.output_file:
        try:
            OutputFormatter.write_file(
                result,
                config.output_file,
                config.output_format.value
            )
            if not quiet:
                click.echo(f"\nResults saved to: {config.output_file}")
        except Exception as e:
            console.print_error(f"Failed to write output file: {e}")
            sys.exit(1)

    # Exit with success (0) - finding 0 subdomains is not an error
    sys.exit(0)


if __name__ == '__main__':
    main()
