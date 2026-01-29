# Frequently Asked Questions (FAQ)

## General Questions

### Q: What is WPair?
A: WPair is a security research tool for identifying Bluetooth devices vulnerable to CVE-2025-36911 (WhisperPair), a critical vulnerability in Google's Fast Pair protocol.

### Q: Is using this tool illegal?
A: The tool itself is legal for authorized security research. However, using it on devices you don't own or without permission is illegal under various computer crime laws (CFAA, Computer Misuse Act, etc.).

### Q: Who discovered this vulnerability?
A: The vulnerability was discovered by security researchers at KU Leuven, Belgium (COSIC Group & DistriNet Group). WPair is an independent implementation for educational purposes.

### Q: Is this tool affiliated with the original researchers?
A: No. This is an independent implementation created for educational and defensive security research. The original researchers have not released any code.

## Usage Questions

### Q: How do I know if my device is vulnerable?
A: Use the `wpair test <address>` command. If it shows "VULNERABLE", your device is affected and needs a firmware update.

### Q: Can I use this on my company's devices?
A: Yes, but only if you have written authorization from your company to perform security testing. Always get permission first.

### Q: What's the difference between `test` and `exploit`?
A:
- **test**: Non-invasive read-only check. Doesn't pair or modify the device.
- **exploit**: Full exploitation that pairs with the device and writes persistent data. Requires --confirm flag.

### Q: Will this damage my device?
A: No. The exploitation is non-destructive and only adds a Bluetooth pairing entry. You can unpair normally through your device settings.

### Q: Can this access my conversations or audio history?
A: No. It can only enable future microphone access if the device supports HFP (Hands-Free Profile). It cannot retrieve historical data or past recordings.

### Q: Why do I need root/admin privileges?
A: Bluetooth operations (especially pairing) require elevated privileges on most operating systems for security reasons.

## Technical Questions

### Q: What Bluetooth adapters are supported?
A: Any adapter that supports:
- Bluetooth Low Energy (BLE) 4.0+
- Bluetooth Classic (BR/EDR) for pairing
- BlueZ stack (Linux) or WinRT (Windows)

### Q: Does this work on macOS?
A: Partially. BLE scanning works, but Bluetooth Classic pairing has limitations due to macOS restrictions on programmatic Bluetooth access.

### Q: What's the range for this attack?
A: Same as normal Bluetooth range:
- **BLE**: Up to ~100 meters (line of sight)
- **Bluetooth Classic**: Up to ~10 meters (typical)

Range depends on the Bluetooth adapter and environmental factors.

### Q: Why does the scan find devices but show "Unknown" status?
A: The scan only discovers devices. Use `wpair test <address>` to check vulnerability status for each device.

### Q: What are "device quirks"?
A: Some manufacturers implement Fast Pair slightly differently. Quirks are device-specific workarounds (delays, different request formats) needed for successful exploitation.

### Q: Why does exploitation sometimes fail?
A: Common reasons:
- Device already paired
- Device out of range
- Device-specific quirks not yet documented
- Bluetooth interference
- Device firmware has been updated

### Q: How do I add a new device to the database?
A: See [CONTRIBUTING.md](../CONTRIBUTING.md) for instructions on adding new device signatures and quirks.

## Security Questions

### Q: Can this be used for eavesdropping?
A: Potentially. If the device supports HFP profile and exploitation succeeds, the attacker could access the microphone. This is why the tool includes warnings and requires confirmation.

### Q: How can I protect my devices?
A:
1. **Update firmware** from the manufacturer
2. **Disable Bluetooth** when not in use
3. **Check for patches** at your device manufacturer's support site
4. **Use the test command** to verify if your device is vulnerable

### Q: Are there any patches available?
A: Yes. Most major manufacturers have released patches. Contact your device manufacturer or check their support website.

### Q: What should I do if my device is vulnerable?
A:
1. Check the manufacturer's website for firmware updates
2. If no update is available, contact support
3. Disable Bluetooth when not in use as a temporary measure
4. Consider replacing very old devices that won't receive updates

### Q: Can this bypass encryption?
A: No. This bypasses the authentication step in Fast Pair's Key-Based Pairing, but doesn't break encryption algorithms. It exploits a protocol design weakness, not cryptographic weakness.

## Platform-Specific Questions

### Q: Why doesn't Bluetooth Classic pairing work on my system?
A: The current implementation includes platform-specific stubs. Full Bluetooth Classic support requires:
- **Linux**: BlueZ with D-Bus bindings
- **Windows**: Windows Bluetooth APIs

Contributions for platform-specific implementations are welcome!

### Q: I get "permission denied" errors on Linux
A: You need to either:
1. Run with `sudo`: `sudo wpair scan`
2. Add your user to the `bluetooth` group: `sudo usermod -aG bluetooth $USER`
3. Configure capabilities: `sudo setcap cap_net_raw+eip $(which python3)`

### Q: Scanning doesn't find any devices on Windows
A: Ensure:
1. Bluetooth is enabled in Windows settings
2. You're running with administrator privileges
3. Your Bluetooth adapter supports BLE
4. No other Bluetooth software is blocking access

## Development Questions

### Q: Can I use WPair as a library in my project?
A: Yes. WPair is designed to be used both as a CLI tool and as a Python library. See [API.md](API.md) for documentation.

### Q: How can I contribute?
A: See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Submitting pull requests
- Adding device quirks

### Q: What's the test coverage?
A: Current coverage is 55% (67 tests). We welcome contributions to improve coverage, especially for integration tests.

### Q: Why is coverage not 100%?
A: Some code paths require actual Bluetooth hardware and are difficult to test in CI:
- BLE scanning callbacks
- Bluetooth Classic pairing
- Platform-specific adapters
- Hardware timeout scenarios

## Ethical Questions

### Q: Should I disclose vulnerabilities I find using this tool?
A: Yes! If you discover new vulnerable devices or quirks:
1. Report to the manufacturer first (responsible disclosure)
2. Allow time for patching (typically 90 days)
3. Share findings with the security community

### Q: Is it ethical to release this tool publicly?
A: Yes, because:
1. The vulnerability was already publicly disclosed
2. Patches are available from manufacturers
3. Defensive security teams need tools to identify vulnerable devices
4. Security through obscurity doesn't work
5. The tool includes prominent warnings and safety features

### Q: What if someone uses this tool maliciously?
A: Malicious use is illegal and already prohibited by existing laws. The tool includes:
- Clear legal warnings
- Confirmation requirements for dangerous operations
- Audit logging capabilities
- Educational disclaimers

Responsible researchers need these tools to identify and protect against threats.

## Troubleshooting

### Q: "No Bluetooth adapter found"
A: Ensure:
- Bluetooth adapter is connected and enabled
- Drivers are installed
- `hciconfig` (Linux) or Device Manager (Windows) shows the adapter

### Q: "Failed to start BLE scanner"
A: Try:
- Restarting Bluetooth service
- Checking no other apps are using Bluetooth
- Running with elevated privileges
- Checking system logs for errors

### Q: "Device not responding to KBP request"
A: Check:
- Device is in range
- Device is powered on and not already paired
- Device supports Fast Pair (scan should show it)
- Try different exploitation strategies

### Q: Tests fail with "insufficient data"
A: This usually means:
- Device already paired (unpair first)
- Device moved out of range
- Bluetooth connection dropped
- Device doesn't implement Fast Pair correctly

## Getting Help

### Q: Where can I get help?
A:
- Check this FAQ
- Review the [README.md](../README.md)
- Search [GitHub Issues](https://github.com/wpair/wpair-cli/issues)
- Open a new issue with details about your problem

### Q: How do I report a security issue?
A: Use GitHub Security Advisories to report security issues privately. Do not open public issues for security vulnerabilities.

### Q: Is there a chat or community?
A: Currently, GitHub Issues and Discussions are the main communication channels. Community channels may be added in the future.

---

**Didn't find your answer?** Open an issue on GitHub: https://github.com/wpair/wpair-cli/issues
