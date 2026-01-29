"""Unit tests for terminal UI."""

import pytest
from io import StringIO
from wpair.ui.terminal import TerminalUI
from wpair.core.device import FastPairDevice, DeviceStatus
from wpair.core.exploit import ExploitResult


def test_terminal_ui_initialization():
    """Test that TerminalUI can be initialized."""
    ui = TerminalUI()
    assert ui is not None
    assert ui.console is not None


def test_show_banner(capsys):
    """Test banner display."""
    ui = TerminalUI()
    ui.show_banner()
    # Just verify it doesn't crash
    # Rich output is hard to test precisely


def test_print_info():
    """Test info message printing."""
    ui = TerminalUI()
    # Just verify it doesn't crash
    ui.print_info("Test info message")


def test_print_success():
    """Test success message printing."""
    ui = TerminalUI()
    ui.print_success("Test success message")


def test_print_warning():
    """Test warning message printing."""
    ui = TerminalUI()
    ui.print_warning("Test warning message")


def test_print_error():
    """Test error message printing."""
    ui = TerminalUI()
    ui.print_error("Test error message")


def test_show_devices_table_empty():
    """Test showing empty device table."""
    ui = TerminalUI()
    devices = []
    ui.show_devices_table(devices)


def test_show_devices_table_with_devices():
    """Test showing device table with devices."""
    ui = TerminalUI()
    devices = [
        FastPairDevice(
            name="Test Device 1",
            address="AA:BB:CC:DD:EE:FF",
            is_pairing_mode=True,
            has_account_key_filter=False,
            model_id="123456",
            rssi=-50,
            status=DeviceStatus.VULNERABLE
        ),
        FastPairDevice(
            name="Test Device 2",
            address="11:22:33:44:55:66",
            is_pairing_mode=False,
            has_account_key_filter=True,
            model_id="789ABC",
            rssi=-80,
            status=DeviceStatus.PATCHED
        ),
    ]
    ui.show_devices_table(devices)


def test_show_vulnerability_status_vulnerable():
    """Test showing vulnerable status."""
    ui = TerminalUI()
    ui.show_vulnerability_status("AA:BB:CC:DD:EE:FF", DeviceStatus.VULNERABLE)


def test_show_vulnerability_status_patched():
    """Test showing patched status."""
    ui = TerminalUI()
    ui.show_vulnerability_status("AA:BB:CC:DD:EE:FF", DeviceStatus.PATCHED)


def test_show_vulnerability_status_error():
    """Test showing error status."""
    ui = TerminalUI()
    ui.show_vulnerability_status("AA:BB:CC:DD:EE:FF", DeviceStatus.ERROR)


def test_show_exploit_result_success():
    """Test showing successful exploit result."""
    ui = TerminalUI()
    result = ExploitResult(
        success=True,
        message="Exploitation successful",
        br_edr_address="AA:BB:CC:DD:EE:FF",
        paired=True,
        account_key_written=True
    )
    ui.show_exploit_result(result)


def test_show_exploit_result_failure():
    """Test showing failed exploit result."""
    ui = TerminalUI()
    result = ExploitResult(
        success=False,
        message="Device not vulnerable",
        br_edr_address=None,
        paired=False,
        account_key_written=False
    )
    ui.show_exploit_result(result)


def test_show_progress():
    """Test progress context manager."""
    ui = TerminalUI()
    with ui.show_progress("Testing") as progress:
        task = progress.add_task("Test task", total=100)
        progress.update(task, advance=50)
        assert task is not None
