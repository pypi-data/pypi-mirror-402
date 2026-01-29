# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-18

### Added
- Initial release of WPair CLI
- BLE scanner for Fast Pair device discovery
- Vulnerability tester for CVE-2025-36911
- Full exploitation engine with 4 strategy types
- Device database with 20+ known vulnerable models
- Rich-based terminal UI with tables and progress bars
- Click-based CLI with scan/test/exploit/about commands
- ECDH key exchange (secp256r1)
- AES-ECB encryption/decryption
- Device-specific quirks handling (Sony, JBL, Nothing, Google)
- Comprehensive test suite (67 tests, 55% coverage)
- Security warnings and confirmation requirements
- Module execution support (`python -m wpair`)

### Security
- Added mandatory --confirm flag for exploit command
- Included legal disclaimers in CLI help text
- Implemented banner warnings for authorized use only
- Added progress tracking for audit trail

## [Unreleased]

### Planned
- Bluetooth Classic adapter implementation for Windows
- Bluetooth Classic adapter implementation for Linux
- Integration tests with mock devices
- Additional device quirks and signatures
- Improved error messages
- Performance optimizations for large scans

---

For full commit history, see: https://github.com/wpair/wpair-cli/commits/
