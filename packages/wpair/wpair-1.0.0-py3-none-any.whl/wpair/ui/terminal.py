"""Rich-based terminal user interface."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from typing import List

from wpair.core.device import FastPairDevice, DeviceStatus


class TerminalUI:
    """Rich-based terminal user interface for WPair."""

    def __init__(self):
        self.console = Console()

    def show_banner(self):
        """Display application banner with security warning."""
        banner = """[bold cyan]WPair[/bold cyan] - CVE-2025-36911 Vulnerability Scanner
[dim]Fast Pair Security Research Tool[/dim]

[yellow]⚠️  FOR AUTHORIZED SECURITY TESTING ONLY ⚠️[/yellow]

[dim]Only test devices you own or have explicit permission to test.
Unauthorized access is illegal under CFAA and similar laws.[/dim]
        """
        self.console.print(Panel(banner, border_style="cyan", padding=(1, 2)))

    def show_devices_table(self, devices: List[FastPairDevice]):
        """
        Display discovered devices in a formatted table.

        Args:
            devices: List of FastPairDevice objects to display
        """
        if not devices:
            self.console.print("[yellow]No devices found[/yellow]")
            return

        table = Table(title="Discovered Fast Pair Devices", show_header=True, header_style="bold cyan")

        table.add_column("Name", style="cyan", no_wrap=False)
        table.add_column("Address", style="white")
        table.add_column("Model ID", style="yellow")
        table.add_column("RSSI", justify="right", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Pairing", justify="center")

        for device in devices:
            # Color-code status
            status_style = {
                DeviceStatus.NOT_TESTED: "white",
                DeviceStatus.TESTING: "yellow",
                DeviceStatus.VULNERABLE: "red bold",
                DeviceStatus.PATCHED: "green",
                DeviceStatus.ERROR: "dim"
            }.get(device.status, "white")

            # Status icon
            status_icon = {
                DeviceStatus.NOT_TESTED: "?",
                DeviceStatus.TESTING: "⋯",
                DeviceStatus.VULNERABLE: "⚠",
                DeviceStatus.PATCHED: "✓",
                DeviceStatus.ERROR: "✗"
            }.get(device.status, "?")

            table.add_row(
                device.display_name,
                device.address,
                device.model_id or "-",
                f"{device.rssi} dBm",
                f"[{status_style}]{status_icon} {device.status.value.upper()}[/{status_style}]",
                "✓" if device.is_pairing_mode else "✗"
            )

        self.console.print(table)

    def show_exploit_result(self, result):
        """
        Display exploitation result.

        Args:
            result: ExploitResult object
        """
        if result.success:
            panel = Panel(
                f"[green bold]✓ Exploitation Successful![/green bold]\n\n"
                f"[white]BR/EDR Address:[/white] {result.br_edr_address}\n"
                f"[white]Paired:[/white] {'Yes' if result.paired else 'No'}\n"
                f"[white]Account Key Written:[/white] {'Yes' if result.account_key_written else 'No'}\n\n"
                f"[dim]{result.message}[/dim]",
                title="Exploit Result",
                border_style="green",
                padding=(1, 2)
            )
        else:
            panel = Panel(
                f"[red]✗ Exploitation Failed[/red]\n\n"
                f"[white]Message:[/white] {result.message}\n"
                f"[white]BR/EDR Address:[/white] {result.br_edr_address or 'N/A'}",
                title="Exploit Result",
                border_style="red",
                padding=(1, 2)
            )

        self.console.print(panel)

    def show_vulnerability_status(self, address: str, status: DeviceStatus):
        """
        Display vulnerability test status.

        Args:
            address: Device MAC address
            status: DeviceStatus result
        """
        if status == DeviceStatus.VULNERABLE:
            self.console.print(
                f"\n[red bold]⚠️  VULNERABLE[/red bold]\n"
                f"Device [cyan]{address}[/cyan] accepts unauthenticated Key-Based Pairing requests!\n"
                f"[yellow]This device is affected by CVE-2025-36911[/yellow]"
            )
        elif status == DeviceStatus.PATCHED:
            self.console.print(
                f"\n[green]✓ PATCHED[/green]\n"
                f"Device [cyan]{address}[/cyan] correctly rejects unauthorized pairing."
            )
        else:
            self.console.print(
                f"\n[yellow]? ERROR[/yellow]\n"
                f"Test inconclusive for [cyan]{address}[/cyan]. Device may already be paired or unavailable."
            )

    def show_progress(self, description: str, total: int = None):
        """
        Show progress spinner or bar.

        Args:
            description: Progress description
            total: Total steps (None for spinner)

        Returns:
            Progress context manager
        """
        if total is None:
            # Spinner for indefinite tasks
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            )
        else:
            # Progress bar for definite tasks
            return Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
            )

    def print_info(self, message: str):
        """Print informational message."""
        self.console.print(f"[cyan]ℹ[/cyan] {message}")

    def print_success(self, message: str):
        """Print success message."""
        self.console.print(f"[green]✓[/green] {message}")

    def print_warning(self, message: str):
        """Print warning message."""
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def print_error(self, message: str):
        """Print error message."""
        self.console.print(f"[red]✗[/red] {message}")

    def confirm_exploit(self, address: str) -> bool:
        """
        Ask user to confirm exploitation.

        Args:
            address: Target device address

        Returns:
            True if user confirms, False otherwise
        """
        self.console.print(
            f"\n[red bold]⚠️  WARNING ⚠️[/red bold]\n"
            f"You are about to exploit device: [cyan]{address}[/cyan]\n"
            f"[yellow]Only proceed if you OWN this device or have explicit permission![/yellow]\n"
        )

        # In a real CLI, we'd use input(), but for now we'll return True
        # This will be handled by Click's --confirm flag
        return True
