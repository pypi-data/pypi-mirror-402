# WPair - CVE-2025-36911 Fast Pair Vulnerability Scanner

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

**WPair** is a defensive security research tool that demonstrates CVE-2025-36911 vulnerability in Google's Fast Pair protocol.

## ⚠️  SECURITY RESEARCH TOOL - AUTHORIZED USE ONLY ⚠️

This tool is provided for:
- Security research and education
- Testing devices you **OWN**
- Authorized penetration testing with **written permission**

**Unauthorized access to computer systems is ILLEGAL.**

Violators will be prosecuted under applicable laws including:
- Computer Fraud and Abuse Act (USA)
- Computer Misuse Act (UK)
- Similar legislation in your jurisdiction

By using this tool, you agree to use it responsibly and legally.

---

## What is CVE-2025-36911?

CVE-2025-36911 (also known as "WhisperPair") is a vulnerability in Google's Fast Pair protocol that affects millions of Bluetooth audio devices worldwide.

**Impact:**
- **Unauthorized Bluetooth pairing** without user consent
- **Microphone access** via Hands-Free Profile (HFP)
- **Persistent device tracking** via Account Key injection

**CVSS Score:** 8.1 (High)

**Affected Devices:** JBL, Sony, Google Pixel Buds, Anker, Nothing, OnePlus, Beats, Bose, Jabra, Xiaomi, and many others.

---

## Installation

### From PyPI (when published)

```bash
pip install wpair
```

### From Source

```bash
git clone https://github.com/markmysler/wpair-cli.git
cd wpair-cli
pip install -e ".[dev]"
```

---

## Usage

### 1. Scan for Fast Pair Devices

Discover nearby Bluetooth devices advertising Fast Pair service:

```bash
wpair scan --timeout 30
```

**Options:**
- `--timeout N` - Scan duration in seconds (default: 30)
- `--all` - Scan all BLE devices, not just Fast Pair

**Example output:**
```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ Name               ┃ Address          ┃ Model ID ┃ Signal ┃ Status  ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ Pixel Buds Pro 2   │ AA:BB:CC:DD:EE:FF│ 30018E   │ ████   │ Unknown │
│ Sony WF-1000XM4    │ 11:22:33:44:55:66│ CD8256   │ ███    │ Unknown │
└────────────────────┴──────────────────┴──────────┴────────┴─────────┘
```

### 2. Test a Device for Vulnerability (Non-Invasive)

Test if a device is vulnerable **without exploiting or pairing**:

```bash
wpair test AA:BB:CC:DD:EE:FF
```

This performs a read-only test by sending a Key-Based Pairing request and interpreting the GATT error code. **No pairing or modification occurs.**

**Output:**
- `VULNERABLE` - Device accepts unauthenticated pairing requests
- `PATCHED` - Device correctly rejects unauthorized requests
- `ERROR` - Test inconclusive (device may already be paired)

### 3. Exploit (Authorized Testing ONLY)

**⚠️  WARNING:** This performs actual exploitation. Use only on devices you own.

```bash
wpair exploit AA:BB:CC:DD:EE:FF --confirm
```

The `--confirm` flag is **required** and serves as acknowledgment that you own the device or have explicit written permission.

**What this does:**
- Bypasses Key-Based Pairing authentication
- Establishes Bluetooth Classic bonding
- Writes persistent Account Key to device
- May enable microphone access via HFP profile

### 4. About CVE-2025-36911

Display detailed information about the vulnerability:

```bash
wpair about
```

---

## Features

| Feature | Description |
|---------|-------------|
| **BLE Scanner** | Discovers Fast Pair devices broadcasting the 0xFE2C service UUID |
| **Vulnerability Tester** | Non-invasive check if device is patched against CVE-2025-36911 |
| **Exploit Demonstration** | Full proof-of-concept for authorized security testing |
| **Device Database** | 20+ known vulnerable device models with quirks handling |
| **Multi-Strategy Exploitation** | 4 different KBP request strategies with automatic fallback |
| **Progress Tracking** | Real-time progress display with Rich terminal UI |

---

## How It Works

### Attack Overview

The vulnerability exploits weaknesses in Google's Fast Pair Key-Based Pairing (KBP) protocol:

1. **Discovery**: Scan for devices advertising Fast Pair service (UUID 0xFE2C)
2. **KBP Request**: Send unauthenticated Key-Based Pairing request
3. **Address Extraction**: Parse BR/EDR address from response
4. **Classic Bonding**: Pair via Bluetooth Classic
5. **Account Key Injection**: Write persistent tracking identifier

### Technical Details

- **Protocol**: Google Fast Pair (GATT-based BLE service)
- **Vulnerability**: Insufficient authentication in Key-Based Pairing
- **Crypto**: ECDH (secp256r1) + AES-ECB
- **Persistence**: Account Key stored in device NVRAM

### Known Vulnerable Devices

WPair includes a database of 20+ confirmed vulnerable devices:

- Google Pixel Buds (multiple models)
- Sony WF-1000XM4, WH-1000XM5
- JBL Tune Buds, Live Pro 2
- Nothing Ear, Ear (a), Ear (2)
- OnePlus Buds Pro 2
- Beats Studio Buds+
- Anker Soundcore Liberty 4 NC

See [wpair/database/known_devices.py](wpair/database/known_devices.py) for full list.

---

## Architecture

```
wpair/
├── core/              # Core functionality
│   ├── device.py      # Device data models
│   ├── scanner.py     # BLE scanner
│   ├── vulnerability_tester.py  # Non-invasive testing
│   └── exploit.py     # Exploitation engine
├── bluetooth/         # Bluetooth adapters
│   └── classic_adapter.py  # BR/EDR pairing
├── crypto/            # Cryptography
│   ├── ecdh.py        # ECDH key exchange
│   └── aes.py         # AES encryption
├── database/          # Known devices database
├── ui/                # User interface
│   └── terminal.py    # Rich-based TUI
└── cli.py             # Click-based CLI
```

---

## Legal and Ethical Usage

### ⚠️ CRITICAL: Read Before Use

**This tool is for AUTHORIZED security testing ONLY.**

✅ **Allowed:**
- Testing your own devices
- Authorized penetration testing with written permission
- Academic security research in controlled environments
- Defensive security to identify vulnerable devices

❌ **FORBIDDEN:**
- Testing devices you do not own
- Unauthorized access to any device
- Malicious use or privacy violations

### Legal Consequences

Unauthorized access to Bluetooth devices is **ILLEGAL** under:
- **USA**: Computer Fraud and Abuse Act (CFAA), 18 U.S.C. § 1030
- **UK**: Computer Misuse Act 1990
- **EU**: Directive 2013/40/EU
- **Similar legislation worldwide**

**By using this tool, you agree to use it only on devices you own or have explicit written permission to test.**

---

## Development

### Setup Development Environment

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black wpair/
ruff check wpair/
```

### Type Checking

```bash
mypy wpair/
```

---

## Credits

### Original Research Team - KU Leuven, Belgium

| Researcher | Affiliation |
|------------|-------------|
| Sayon Duttagupta | COSIC Group |
| Nikola Antonijević | COSIC Group |
| Bart Preneel | COSIC Group |
| Seppe Wyns | DistriNet Group |
| Dave Singelée | DistriNet Group |

**Funding:** Flemish Government Cybersecurity Research Program (VOEWICS02)

**Resources:**
- [WhisperPair Research Paper](https://whisperpair.eu)
- [WIRED Coverage](https://www.wired.com/story/google-fast-pair-bluetooth-audio-accessories-vulnerability-patches/)

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This application is an independent implementation created for security research purposes. The original KU Leuven researchers discovered and disclosed the vulnerability but have not released any code and are not affiliated with this project. Their inclusion in credits is solely to acknowledge their research contribution.

**Built for the security research community.**
