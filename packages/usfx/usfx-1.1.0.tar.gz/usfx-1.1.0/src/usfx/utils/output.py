"""
Output Formatter

Handles formatting and writing scan results to various formats:
JSON, CSV, and TXT.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import ScanResult, SubdomainResult

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Formats and outputs scan results in various formats"""

    @staticmethod
    def to_json(result: 'ScanResult', pretty: bool = True) -> str:
        """
        Convert scan result to JSON string.

        Args:
            result: ScanResult object
            pretty: Whether to pretty-print the JSON

        Returns:
            JSON string
        """
        data = {
            'domain': result.domain,
            'scan_time': datetime.now().isoformat(),
            'total_found': result.total_found,
            'duration_seconds': round(result.duration_seconds, 2),
            'dns_servers': result.dns_servers_used,
            'subdomains': [
                {
                    'subdomain': s.subdomain,
                    'ip': s.ip,
                    'discovered_by': s.discovered_by,
                    'is_active': s.is_active,
                }
                for s in result.subdomains
            ],
            'modules': [
                {
                    'name': m.module_name,
                    'found': m.found_count,
                    'duration': round(m.duration_seconds, 2),
                    'error': m.error,
                }
                for m in result.module_results
            ]
        }

        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def to_csv(result: 'ScanResult') -> str:
        """
        Convert scan result to CSV string.

        Args:
            result: ScanResult object

        Returns:
            CSV string
        """
        import io
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['subdomain', 'ip', 'discovered_by', 'is_active'])

        # Data
        for s in result.subdomains:
            writer.writerow([
                s.subdomain,
                s.ip or '',
                s.discovered_by,
                'yes' if s.is_active else 'no'
            ])

        return output.getvalue()

    @staticmethod
    def to_txt(result: 'ScanResult', include_ips: bool = True) -> str:
        """
        Convert scan result to plain text (one subdomain per line).

        Args:
            result: ScanResult object
            include_ips: Whether to include IP addresses

        Returns:
            Plain text string
        """
        lines = []

        for s in result.subdomains:
            if include_ips and s.ip:
                lines.append(f"{s.subdomain}\t{s.ip}")
            else:
                lines.append(s.subdomain)

        return '\n'.join(lines)

    @staticmethod
    def write_file(
        result: 'ScanResult',
        output_path: Path,
        format: str = 'json'
    ) -> None:
        """
        Write scan results to file.

        Args:
            result: ScanResult object
            output_path: Path to output file
            format: Output format ('json', 'csv', 'txt')
        """
        format = format.lower()

        if format == 'json':
            content = OutputFormatter.to_json(result)
        elif format == 'csv':
            content = OutputFormatter.to_csv(result)
        elif format == 'txt':
            content = OutputFormatter.to_txt(result)
        else:
            raise ValueError(f"Unknown output format: {format}")

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Results written to {output_path}")

    @staticmethod
    def format_summary(result: 'ScanResult') -> str:
        """
        Format a human-readable summary of scan results.

        Args:
            result: ScanResult object

        Returns:
            Formatted summary string
        """
        lines = [
            "",
            f"{'=' * 50}",
            f"Scan Complete: {result.domain}",
            f"{'=' * 50}",
            f"Total subdomains found: {result.total_found}",
            f"Duration: {result.duration_seconds:.1f}s",
            f"DNS servers: {', '.join(result.dns_servers_used) or 'system default'}",
            "",
            "Module Results:",
        ]

        for module in result.module_results:
            status = f"[ERROR: {module.error}]" if module.error else ""
            lines.append(
                f"  - {module.module_name}: {module.found_count} found "
                f"({module.duration_seconds:.1f}s) {status}"
            )

        if result.subdomains:
            lines.extend([
                "",
                "Discovered Subdomains:",
                "-" * 50,
            ])

            # Group by active status
            active = [s for s in result.subdomains if s.is_active]
            inactive = [s for s in result.subdomains if not s.is_active]

            if active:
                lines.append(f"\nActive ({len(active)}):")
                for s in active[:20]:  # Limit display
                    ip_str = f" -> {s.ip}" if s.ip else ""
                    lines.append(f"  {s.subdomain}{ip_str}")
                if len(active) > 20:
                    lines.append(f"  ... and {len(active) - 20} more")

            if inactive:
                lines.append(f"\nInactive/Unresolved ({len(inactive)}):")
                for s in inactive[:10]:
                    lines.append(f"  {s.subdomain}")
                if len(inactive) > 10:
                    lines.append(f"  ... and {len(inactive) - 10} more")

        return '\n'.join(lines)


class ConsoleOutput:
    """
    Console output helper with optional Rich formatting.
    Falls back to plain text if Rich is not available.
    """

    def __init__(self, use_rich: bool = True, quiet: bool = False):
        """
        Initialize console output.

        Args:
            use_rich: Whether to use Rich for formatting
            quiet: Whether to suppress non-essential output
        """
        self.quiet = quiet
        self.use_rich = use_rich

        if use_rich:
            try:
                from rich.console import Console
                from rich.table import Table
                from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
                self.console = Console()
                self._rich_available = True
            except ImportError:
                self._rich_available = False
                self.use_rich = False
        else:
            self._rich_available = False

    def print_banner(self, version: str) -> None:
        """Print application banner"""
        if self.quiet:
            return

        if self.use_rich:
            # Big ASCII art with gradient
            art_lines = [
                " ██╗   ██╗███████╗███████╗██╗  ██╗",
                " ██║   ██║██╔════╝██╔════╝╚██╗██╔╝",
                " ██║   ██║███████╗█████╗   ╚███╔╝ ",
                " ██║   ██║╚════██║██╔══╝   ██╔██╗ ",
                " ╚██████╔╝███████║██║     ██╔╝ ██╗",
                "  ╚═════╝ ╚══════╝╚═╝     ╚═╝  ╚═╝",
            ]

            colors = [
                "bright_cyan",
                "cyan",
                "bright_blue",
                "blue",
                "bright_magenta",
                "magenta",
            ]

            self.console.print()
            for i, line in enumerate(art_lines):
                color = colors[i % len(colors)]
                self.console.print(f"  [{color}]{line}[/{color}]", highlight=False)

            self.console.print()
            self.console.print(f"  [bold bright_white]Ultimate Subdomain Finder X[/bold bright_white]  [bright_yellow]v{version}[/bright_yellow]")
            self.console.print(f"  [dim italic]Internal Network Subdomain Discovery Tool[/dim italic]")
            self.console.print()
            self.console.print(f"  [bright_green]◆[/bright_green] [dim]Offline Mode[/dim]  [bright_blue]◆[/bright_blue] [dim]Custom DNS[/dim]  [bright_magenta]◆[/bright_magenta] [dim]10 Modules[/dim]")
            self.console.print()
        else:
            ascii_art = r"""
  ██╗   ██╗███████╗███████╗██╗  ██╗
  ██║   ██║██╔════╝██╔════╝╚██╗██╔╝
  ██║   ██║███████╗█████╗   ╚███╔╝
  ██║   ██║╚════██║██╔══╝   ██╔██╗
  ╚██████╔╝███████║██║     ██╔╝ ██╗
   ╚═════╝ ╚══════╝╚═╝     ╚═╝  ╚═╝
"""
            print(ascii_art)
            print(f"  Ultimate Subdomain Finder X  v{version}")
            print(f"  Internal Network Subdomain Discovery Tool")
            print()
            print(f"  * Offline Mode  * Custom DNS  * 10 Modules")
            print()

    def print_config(self, domain: str, dns_servers: List[str], modules: List[str]) -> None:
        """Print scan configuration"""
        if self.quiet:
            return

        if self.use_rich:
            self.console.print(f"  [bold]Target:[/bold] [bright_white]{domain}[/bright_white]")
            if dns_servers:
                self.console.print(f"  [bold]DNS:[/bold]    [dim]{', '.join(dns_servers)}[/dim]")
            else:
                self.console.print(f"  [bold]DNS:[/bold]    [dim]system default[/dim]")
            self.console.print()
        else:
            print(f"  Target: {domain}")
            if dns_servers:
                print(f"  DNS:    {', '.join(dns_servers)}")
            else:
                print(f"  DNS:    system default")
            print()

    def print_phase(self, phase: str) -> None:
        """Print phase header"""
        if self.quiet:
            return

        if self.use_rich:
            self.console.print(f"\n[bold cyan][{phase}][/bold cyan]")
        else:
            print(f"\n[{phase}]")

    def print_module_result(self, module: str, count: int, duration: float) -> None:
        """Print module result"""
        if self.quiet:
            return

        if self.use_rich:
            self.console.print(f"  └─ {module}: [green]{count}[/green] found ({duration:.1f}s)")
        else:
            print(f"  └─ {module}: {count} found ({duration:.1f}s)")

    def print_result_table(self, result: 'ScanResult') -> None:
        """Print results as a table"""
        if self.quiet or not result.subdomains:
            return

        if self.use_rich:
            from rich.table import Table

            table = Table(title=f"Results: {result.total_found} subdomains")
            table.add_column("Subdomain", style="cyan")
            table.add_column("IP Address", style="green")
            table.add_column("Source", style="dim")

            for s in result.subdomains[:50]:  # Limit to 50 rows
                table.add_row(s.subdomain, s.ip or "-", s.discovered_by)

            if result.total_found > 50:
                table.add_row("...", f"({result.total_found - 50} more)", "")

            self.console.print(table)
        else:
            print(f"\nResults: {result.total_found} subdomains")
            print("-" * 60)
            print(f"{'Subdomain':<35} {'IP Address':<15} Source")
            print("-" * 60)

            for s in result.subdomains[:50]:
                print(f"{s.subdomain:<35} {(s.ip or '-'):<15} {s.discovered_by}")

            if result.total_found > 50:
                print(f"... ({result.total_found - 50} more)")

    def print_summary(self, result: 'ScanResult') -> None:
        """Print scan summary"""
        if self.use_rich:
            self.console.print(f"\n[bold green]Scan complete![/bold green]")
            self.console.print(f"Found [bold]{result.total_found}[/bold] subdomains in {result.duration_seconds:.1f}s")
        else:
            print(f"\nScan complete!")
            print(f"Found {result.total_found} subdomains in {result.duration_seconds:.1f}s")

    def print_error(self, message: str) -> None:
        """Print error message"""
        if self.use_rich:
            self.console.print(f"[bold red]Error:[/bold red] {message}")
        else:
            print(f"Error: {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message"""
        if self.use_rich:
            self.console.print(f"[bold yellow]Warning:[/bold yellow] {message}")
        else:
            print(f"Warning: {message}")

    def create_progress(self):
        """Create a progress context manager"""
        if self.use_rich and not self.quiet:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

            return Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console,
            )
        else:
            # Return a dummy context manager
            class DummyProgress:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

                def add_task(self, *args, **kwargs):
                    return 0

                def update(self, *args, **kwargs):
                    pass

            return DummyProgress()
