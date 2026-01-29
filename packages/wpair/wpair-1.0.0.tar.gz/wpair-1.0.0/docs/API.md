# WPair API Documentation

This document describes the main classes and APIs in WPair for developers who want to use it as a library or contribute to the project.

## Core Module

### FastPairDevice

Data model representing a Fast Pair device.

```python
from wpair.core.device import FastPairDevice, DeviceStatus, SignalStrength

device = FastPairDevice(
    name="Pixel Buds Pro",
    address="AA:BB:CC:DD:EE:FF",
    is_pairing_mode=True,
    has_account_key_filter=False,
    model_id="30018E",
    rssi=-50,
    status=DeviceStatus.NOT_TESTED
)

# Properties
signal = device.signal_strength  # SignalStrength.EXCELLENT
display = device.display_name    # "Pixel Buds Pro (Google)"
```

**Enums:**
- `DeviceStatus`: NOT_TESTED, VULNERABLE, PATCHED, ERROR
- `SignalStrength`: EXCELLENT, GOOD, FAIR, WEAK

### BLEScanner

Scans for Fast Pair devices using Bluetooth Low Energy.

```python
from wpair.core.scanner import BLEScanner

def on_device_found(device: FastPairDevice):
    print(f"Found: {device.display_name}")

scanner = BLEScanner(on_device_found)

# Start scanning
await scanner.start_scanning(scan_all=False)
await asyncio.sleep(30)
await scanner.stop_scanning()
```

**Methods:**
- `start_scanning(scan_all=False) -> bool`: Start BLE scan
- `stop_scanning()`: Stop scan and cleanup
- `_detection_callback(device, advertisement_data)`: Internal callback

### VulnerabilityTester

Tests devices for CVE-2025-36911 vulnerability non-invasively.

```python
from wpair.core.vulnerability_tester import VulnerabilityTester

tester = VulnerabilityTester()
status = await tester.test_device("AA:BB:CC:DD:EE:FF")

if status == DeviceStatus.VULNERABLE:
    print("Device is vulnerable!")
```

**Methods:**
- `test_device(address: str) -> DeviceStatus`: Test a device
- `_build_kbp_request(address: str) -> bytes`: Build test request

### FastPairExploit

Full exploitation engine with multiple strategies.

```python
from wpair.core.exploit import FastPairExploit, ExploitResult
from wpair.bluetooth.classic_adapter import ClassicBluetoothAdapter

adapter = ClassicBluetoothAdapter()
exploit = FastPairExploit(adapter)

def progress_callback(message: str):
    print(f"Progress: {message}")

result: ExploitResult = await exploit.exploit(
    address="AA:BB:CC:DD:EE:FF",
    on_progress=progress_callback
)

if result.success:
    print(f"Paired with {result.br_edr_address}")
    print(f"Account key written: {result.account_key_written}")
```

**Classes:**
- `ExploitStrategy`: RAW_KBP, RAW_WITH_SEEKER, EXTENDED_RESPONSE, RETROACTIVE
- `ExploitResult`: success, br_edr_address, paired, account_key_written, message
- `DeviceQuirks`: needs_extended_response, delay_before_kbp, delay_before_account_key

**Methods:**
- `exploit(address, on_progress=None) -> ExploitResult`: Run exploitation
- `_build_kbp_request(address, strategy) -> bytes`: Build KBP request
- `_parse_kbp_response(data) -> Optional[str]`: Extract BR/EDR address
- `_get_device_quirks(model_id) -> DeviceQuirks`: Get device-specific quirks

## Bluetooth Module

### ClassicBluetoothAdapter

Bluetooth Classic (BR/EDR) adapter for pairing.

```python
from wpair.bluetooth.classic_adapter import ClassicBluetoothAdapter

adapter = ClassicBluetoothAdapter()

# Pair with device
success = await adapter.pair(
    address="AA:BB:CC:DD:EE:FF",
    pin=None
)

# Check pairing status
is_paired = await adapter.is_paired("AA:BB:CC:DD:EE:FF")

# Unpair
await adapter.unpair("AA:BB:CC:DD:EE:FF")
```

**Methods:**
- `pair(address, pin=None) -> bool`: Pair with device
- `unpair(address) -> bool`: Remove pairing
- `is_paired(address) -> bool`: Check pairing status

**Note**: Current implementation is a stub. Platform-specific implementations needed for Windows/Linux.

## Crypto Module

### ECDH

Elliptic Curve Diffie-Hellman key exchange using secp256r1.

```python
from wpair.crypto.ecdh import (
    generate_ecdh_keypair,
    compute_shared_secret,
    serialize_public_key
)

# Generate keypair
private_key, public_key = generate_ecdh_keypair()

# Serialize public key (64 bytes, uncompressed point)
public_bytes = serialize_public_key(public_key)

# Compute shared secret (with peer's public key)
shared_secret = compute_shared_secret(private_key, peer_public_key)
```

### AES

AES-ECB encryption/decryption without padding.

```python
from wpair.crypto.aes import aes_encrypt_ecb, aes_decrypt_ecb

key = b'0123456789ABCDEF'  # 16 bytes
plaintext = b'TestData12345678'  # 16 bytes

# Encrypt
ciphertext = aes_encrypt_ecb(key, plaintext)

# Decrypt
decrypted = aes_decrypt_ecb(key, ciphertext)
```

**Note**: Data must be multiple of 16 bytes (AES block size). No padding is applied.

## Database Module

### KnownDevices

Database of known vulnerable Fast Pair devices.

```python
from wpair.database.known_devices import DEVICES, DeviceInfo, get_device_info

# Get device info by Model ID
info = get_device_info("30018E")
if info:
    print(f"{info.name} by {info.manufacturer}")

# Check if model ID is known
if "CD8256" in DEVICES:
    device = DEVICES["CD8256"]
    print(f"Found: {device.name}")
```

**Data Structure:**
```python
@dataclass
class DeviceInfo:
    name: str
    manufacturer: str
```

**Known Manufacturers:**
- Google (Pixel Buds series)
- Sony (WF/WH series)
- JBL (Tune, Live series)
- Nothing (Ear series)
- OnePlus, Beats, Bose, Jabra, Anker, Xiaomi

## UI Module

### TerminalUI

Rich-based terminal user interface.

```python
from wpair.ui.terminal import TerminalUI

ui = TerminalUI()

# Show banner
ui.show_banner()

# Print messages
ui.print_info("Information message")
ui.print_success("Success message")
ui.print_warning("Warning message")
ui.print_error("Error message")

# Show device table
ui.show_devices_table(devices)

# Show vulnerability status
ui.show_vulnerability_status("AA:BB:CC:DD:EE:FF", DeviceStatus.VULNERABLE)

# Show exploit result
ui.show_exploit_result(result)

# Progress bar
with ui.show_progress("Scanning") as progress:
    task = progress.add_task("Finding devices...", total=100)
    for i in range(100):
        progress.update(task, advance=1)
```

**Methods:**
- `show_banner()`: Display security warning banner
- `print_info/success/warning/error(message)`: Colored output
- `show_devices_table(devices)`: Table of discovered devices
- `show_vulnerability_status(address, status)`: Vulnerability test result
- `show_exploit_result(result)`: Exploitation result panel
- `show_progress(description)`: Context manager for progress display

## Utils Module

### Validators

Input validation utilities.

```python
from wpair.utils.validators import is_valid_mac_address

# Validate MAC address
if is_valid_mac_address("AA:BB:CC:DD:EE:FF"):
    print("Valid MAC")

# Invalid formats
is_valid_mac_address("invalid")  # False
is_valid_mac_address("AA:BB:CC")  # False
```

### Logger

Logging configuration for debugging.

```python
from wpair.utils.logger import setup_logger

# Setup logging
logger = setup_logger("wpair.scanner", level="DEBUG")

# Use logger
logger.info("Starting scan...")
logger.debug("Advertisement data: %s", data.hex())
logger.error("Failed to connect: %s", error)
```

## CLI Module

The CLI module uses Click framework. See main [README.md](../README.md) for usage examples.

## Error Handling

All async functions can raise exceptions. Common exceptions:

```python
from bleak import BleakError

try:
    await scanner.start_scanning()
except BleakError as e:
    print(f"Bluetooth error: {e}")
except PermissionError:
    print("Need root/admin privileges")
except TimeoutError:
    print("Operation timed out")
```

## Type Hints

WPair uses type hints throughout. Enable type checking with mypy:

```bash
mypy wpair/
```

## Async/Await

Most Bluetooth operations are asynchronous:

```python
import asyncio

async def main():
    scanner = BLEScanner(callback)
    await scanner.start_scanning()
    # ...

# Run
asyncio.run(main())
```

## Testing

Import test utilities:

```python
from tests.conftest import mock_device, mock_adapter

def test_something(mock_device):
    assert mock_device.address == "AA:BB:CC:DD:EE:FF"
```

## Best Practices

1. **Always validate MAC addresses** before Bluetooth operations
2. **Use async context managers** for cleanup
3. **Handle BleakError** for Bluetooth failures
4. **Check permissions** before Bluetooth operations
5. **Log sensitive operations** for audit trail
6. **Respect device quirks** from database
7. **Test with mocks** for CI/CD

## Examples

See [examples/](../examples/) directory for:
- Simple scanner
- Vulnerability batch tester
- Device database query
- Custom exploit strategies

---

For questions or contributions, see [CONTRIBUTING.md](../CONTRIBUTING.md).
