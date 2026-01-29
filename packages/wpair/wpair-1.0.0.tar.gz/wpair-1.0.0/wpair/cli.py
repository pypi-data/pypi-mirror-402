"""Command-line interface for WPair."""

import asyncio
import click
import sys
from typing import List
from rich.panel import Panel

from wpair.core.scanner import BLEScanner
from wpair.core.device import FastPairDevice, DeviceStatus
from wpair.core.vulnerability_tester import VulnerabilityTester
from wpair.core.exploit import FastPairExploit
from wpair.bluetooth.classic_adapter import ClassicBluetoothAdapter
from wpair.ui.terminal import TerminalUI


@click.group()
@click.version_option(version="1.0.0", prog_name="wpair")
def cli():
    """
    WPair - CVE-2025-36911 Fast Pair Vulnerability Scanner

    A defensive security research tool for identifying vulnerable Bluetooth devices.

    \b
    Examples:
        wpair scan --timeout 30
        wpair test AA:BB:CC:DD:EE:FF
        wpair exploit AA:BB:CC:DD:EE:FF --confirm
    """
    pass


@cli.command()
@click.option("--all", is_flag=True, help="Scan all BLE devices, not just Fast Pair")
@click.option("--timeout", default=30, help="Scan duration in seconds", show_default=True)
def scan(all: bool, timeout: int):
    """
    Scan for Fast Pair devices.

    Discovers Bluetooth Low Energy devices advertising the Fast Pair service.
    Displays device names, addresses, Model IDs, and signal strength.
    """
    ui = TerminalUI()
    ui.show_banner()

    ui.print_info(f"Starting BLE scan for {timeout} seconds...")
    if all:
        ui.print_warning("Scanning ALL BLE devices (may be noisy)")

    devices: List[FastPairDevice] = []

    def on_device_found(device: FastPairDevice):
        devices.append(device)
        ui.print_info(f"Found: {device.display_name} ({device.address})")

    scanner = BLEScanner(on_device_found)

    async def run_scan():
        success = await scanner.start_scanning(scan_all=all)
        if not success:
            ui.print_error("Failed to start BLE scanner")
            return False

        await asyncio.sleep(timeout)
        await scanner.stop_scanning()
        return True

    try:
        success = asyncio.run(run_scan())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        ui.print_warning("Scan interrupted by user")
        asyncio.run(scanner.stop_scanning())
    except Exception as e:
        ui.print_error(f"Scan failed: {e}")
        sys.exit(1)

    ui.show_devices_table(devices)
    ui.print_success(f"Scan complete: {len(devices)} device(s) found")


@cli.command()
@click.argument("address")
def test(address: str):
    """
    Test a device for CVE-2025-36911 vulnerability.

    \b
    Performs a non-invasive test to determine if the device is vulnerable.
    Does NOT exploit or pair with the device.

    \b
    ADDRESS: Bluetooth MAC address (format: XX:XX:XX:XX:XX:XX)

    \b
    Status results:
        VULNERABLE - Device accepts unauthenticated pairing requests
        PATCHED    - Device correctly rejects unauthorized requests
        ERROR      - Test inconclusive (device may be paired already)
    """
    ui = TerminalUI()
    ui.show_banner()

    ui.print_info(f"Testing device: {address}")

    with ui.show_progress("Testing vulnerability") as progress:
        task = progress.add_task("Running test...", total=None)

        tester = VulnerabilityTester()

        try:
            status = asyncio.run(tester.test_device(address))
        except KeyboardInterrupt:
            ui.print_warning("Test interrupted by user")
            sys.exit(1)
        except Exception as e:
            ui.print_error(f"Test failed: {e}")
            sys.exit(1)

    ui.show_vulnerability_status(address, status)


@cli.command()
@click.argument("address")
@click.option("--confirm", is_flag=True,
              help="Confirm you own this device (REQUIRED)")
def exploit(address: str, confirm: bool):
    """
    Exploit a vulnerable device (AUTHORIZED TESTING ONLY).

    \b
    ⚠️  WARNING: This performs actual exploitation including:
        - Key-Based Pairing bypass
        - Bluetooth Classic bonding
        - Account Key persistence

    \b
    ADDRESS: Bluetooth MAC address of target device

    \b
    You MUST use --confirm flag to proceed.
    Only test devices you OWN or have explicit written permission to test.

    \b
    Unauthorized access is ILLEGAL under:
        - Computer Fraud and Abuse Act (USA)
        - Computer Misuse Act (UK)
        - Similar legislation worldwide
    """
    ui = TerminalUI()
    ui.show_banner()

    if not confirm:
        ui.print_error("You must use --confirm flag to proceed")
        ui.print_warning("Only test devices you own or have permission to test!")
        ui.print_info("Usage: wpair exploit <address> --confirm")
        sys.exit(1)

    ui.print_warning("⚠️  Starting exploitation ⚠️")
    ui.print_info(f"Target: {address}")
    ui.console.print()

    # Initialize components
    classic_adapter = ClassicBluetoothAdapter()
    exploit_engine = FastPairExploit(classic_adapter)

    progress_messages = []

    def on_progress(message: str):
        progress_messages.append(message)
        ui.console.print(f"[dim]→[/dim] {message}")

    # Run exploitation
    try:
        result = asyncio.run(exploit_engine.exploit(address, on_progress))
    except KeyboardInterrupt:
        ui.print_warning("Exploitation interrupted by user")
        sys.exit(1)
    except Exception as e:
        ui.print_error(f"Exploitation failed with exception: {e}")
        sys.exit(1)

    # Display result
    ui.console.print()
    ui.show_exploit_result(result)

    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


@cli.command()
def about():
    """Show information about WPair and CVE-2025-36911."""
    ui = TerminalUI()

    about_text = """[bold cyan]WPair[/bold cyan] - CVE-2025-36911 Fast Pair Vulnerability Scanner

[bold]What is CVE-2025-36911?[/bold]
A vulnerability in Google's Fast Pair protocol that affects millions of
Bluetooth audio devices worldwide. Also known as "WhisperPair".

[bold]Impact:[/bold]
  • Unauthorized Bluetooth pairing without user consent
  • Potential microphone access via HFP profile
  • Persistent device tracking via Account Key injection

[bold]CVSS Score:[/bold] 8.1 (High)

[bold]Affected Manufacturers:[/bold]
  JBL, Sony, Google, Anker, Nothing, OnePlus, Beats, Bose, Jabra, Xiaomi

[bold]Original Research:[/bold]
  KU Leuven, Belgium (COSIC Group & DistriNet Group)
  Research paper: https://whisperpair.eu

[bold]WPair Implementation:[/bold]
  Independent Python implementation for security research
  GitHub: https://github.com/wpair/wpair-cli
  License: Apache 2.0

[yellow]⚠️  This tool is for authorized security testing ONLY[/yellow]
    """

    ui.console.print(Panel(about_text, border_style="cyan", padding=(1, 2)))


def main():
    """Main entry point for CLI."""
    try:
        cli()
    except Exception as e:
        console = TerminalUI().console
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
