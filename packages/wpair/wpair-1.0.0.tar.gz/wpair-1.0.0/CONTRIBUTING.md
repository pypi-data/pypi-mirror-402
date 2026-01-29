# Contributing to WPair

Thank you for your interest in contributing to WPair! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a professional and respectful environment. We are committed to providing a welcoming and harassment-free experience for everyone.

## Security and Ethics First

**Before contributing, understand that:**

1. This tool is for **defensive security research only**
2. Contributions that enable malicious use will be **rejected**
3. All features must include appropriate **security warnings**
4. Code must not facilitate unauthorized access

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/markmysler/wpair-cli/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, Bluetooth adapter)
   - Relevant logs (sanitize any sensitive info)

### Suggesting Enhancements

We welcome suggestions for:
- Additional device quirks and signatures
- Platform-specific Bluetooth improvements
- Better error handling
- Documentation improvements
- Test coverage expansion

**Please do not suggest:**
- Features that enable unauthorized access
- Stealth or evasion capabilities
- Bulk scanning/exploitation tools
- Anything that violates ethical hacking principles

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the style guide below
4. **Add tests** for new functionality
5. **Run the test suite** to ensure everything passes
6. **Commit** with clear, descriptive messages
7. **Push** to your fork
8. **Open a Pull Request** with:
   - Description of changes
   - Motivation/use case
   - Test results
   - Screenshots (if UI changes)

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Bluetooth adapter (for hardware tests)
- Linux or Windows

### Initial Setup

```bash
# Clone your fork
git clone https://github.com/markmysler/wpair-cli.git
cd wpair-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=wpair

# Run specific test file
pytest tests/unit/test_exploit.py -v

# Run with verbose output
pytest tests/ -vv --tb=short
```

### Code Quality Checks

Before submitting a PR, ensure:

```bash
# Format code with Black
black wpair/ tests/

# Check linting (if configured)
pylint wpair/

# Type checking (if configured)
mypy wpair/
```

## Style Guide

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://github.com/psf/black) for formatting (line length: 100)
- Use type hints where possible
- Write docstrings for all public functions/classes

### Code Organization

```python
"""Module docstring explaining purpose."""

import standard_library
import third_party
from wpair.module import something

# Constants
CONSTANT_NAME = value

# Classes and functions
class MyClass:
    """Class docstring."""

    def method(self, param: str) -> bool:
        """Method docstring.

        Args:
            param: Parameter description

        Returns:
            Return value description
        """
        pass
```

### Naming Conventions

- **Classes**: `PascalCase`
- **Functions/methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

### Documentation

- Add docstrings to all public APIs
- Include usage examples for complex functions
- Update README.md if adding user-facing features
- Add comments for non-obvious code

### Testing

- Write unit tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names: `test_<what>_<when>_<expected>`
- Mock external dependencies (Bluetooth hardware)

Example test structure:

```python
def test_parse_advertisement_with_model_id():
    """Test advertisement parsing when Model ID is present."""
    # Arrange
    data = bytes([0x00, 0x12, 0x34, 0x56])

    # Act
    result = parse_advertisement(data)

    # Assert
    assert result.model_id == "123456"
    assert result.is_pairing_mode is True
```

## Project Structure

```
wpair-cli/
├── wpair/                 # Main package
│   ├── core/             # Core functionality
│   ├── bluetooth/        # Bluetooth adapters
│   ├── crypto/           # Cryptography utilities
│   ├── database/         # Known devices
│   ├── ui/               # User interface
│   └── cli.py            # CLI entry point
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests (if any)
├── docs/                # Documentation
├── pyproject.toml       # Project configuration
└── README.md           # Main documentation
```

## Adding New Device Quirks

If you've discovered a device that requires special handling:

1. Add the device to `wpair/database/known_devices.py`:
   ```python
   "MODELID": DeviceInfo("Device Name", "Manufacturer"),
   ```

2. If it needs special quirks, update `wpair/core/exploit.py`:
   ```python
   def _get_device_quirks(self, model_id: bytes) -> DeviceQuirks:
       model_str = model_id.hex().upper()

       if model_str.startswith("NEW"):
           return DeviceQuirks(
               needs_extended_response=True,
               delay_before_kbp=0.5
           )
   ```

3. Add a test case in `tests/unit/test_exploit.py`

4. Document the quirk in your PR description

## Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance tasks

**Examples:**
```
feat(scanner): add support for extended advertisements

fix(exploit): handle timeout in KBP response parsing

docs(readme): add FAQ section about device compatibility

test(crypto): add edge cases for ECDH key generation
```

## Release Process

(Maintainers only)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag -a v1.2.0 -m "Version 1.2.0"`
4. Push tag: `git push origin v1.2.0`
5. Build and publish to PyPI (see PyPI Publishing guide)

## Questions?

- Open an issue for questions
- Check existing issues and discussions
- Review the documentation in `docs/`

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to WPair and helping improve Bluetooth security research tools!
