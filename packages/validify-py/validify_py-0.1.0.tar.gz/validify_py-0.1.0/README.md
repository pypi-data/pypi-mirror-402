# ValidX

[![CI](https://github.com/2024si96524-Mithun/ValidX/actions/workflows/ci.yml/badge.svg)](https://github.com/2024si96524-Mithun/ValidX/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/validify-py.svg)](https://badge.fury.io/py/validify-py)
[![Python Versions](https://img.shields.io/pypi/pyversions/validify-py.svg)](https://pypi.org/project/validify-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A flexible and extensible validation library for Python.

## Features

- 🔍 **Type Validators**: Check for strings, integers, floats, booleans, lists, dicts, and None
- 📧 **Format Validators**: Validate emails and URLs with robust regex patterns
- 📏 **Range & Length Validators**: Check numeric ranges and string/collection lengths
- 🎯 **Decorators**: Validate function arguments and return values
- 🛠️ **Utilities**: Helper functions for empty/non-empty checks
- ✨ **Type Hints**: Full type annotation support for better IDE experience
- 🧪 **Well Tested**: Comprehensive test suite with high coverage

## Installation

```bash
pip install validify-py
```

For development:

```bash
pip install validify-py[dev]
```

## Quick Start

```python
from validx import is_email, is_url, is_string, is_in_range, ValidationError

# Basic type validation
is_string("hello")  # True
is_string(123)      # False

# Email validation
is_email("user@example.com")  # True
is_email("invalid-email")     # False

# URL validation
is_url("https://github.com")  # True
is_url("not-a-url")           # False

# Range validation
is_in_range(5, min_value=0, max_value=10)  # True
is_in_range(15, min_value=0, max_value=10) # False
```

## Using Decorators

```python
from validx import validate_args, validate_return, ValidationError

def is_positive(x):
    return x > 0

@validate_args(is_positive)
def square(x):
    return x * x

square(5)   # Returns 25
square(-1)  # Raises ValidationError

def is_not_none(value):
    return value is not None

@validate_return(is_not_none)
def find_user(user_id):
    # ... lookup logic
    return user

find_user(123)  # Works if user found
find_user(999)  # Raises ValidationError if returns None
```

## Available Validators

| Function | Description |
|----------|-------------|
| `is_string(value)` | Check if value is a string |
| `is_integer(value)` | Check if value is an integer (excludes booleans) |
| `is_float(value)` | Check if value is a float |
| `is_boolean(value)` | Check if value is a boolean |
| `is_list(value)` | Check if value is a list |
| `is_dict(value)` | Check if value is a dictionary |
| `is_none(value)` | Check if value is None |
| `is_email(value)` | Check if value is a valid email format |
| `is_url(value)` | Check if value is a valid URL format |
| `is_in_range(value, min_value, max_value)` | Check if numeric value is in range |
| `has_min_length(value, min_length)` | Check minimum length |
| `has_max_length(value, max_length)` | Check maximum length |
| `is_empty(value)` | Check if value is empty (None, '', or empty collection) |
| `is_not_empty(value)` | Check if value is not empty |

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development

```bash
# Clone the repository
git clone https://github.com/2024si96524-Mithun/ValidX.git
cd ValidX

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linting
flake8 src tests
black --check src tests
isort --check-only src tests
mypy src

# Format code
black src tests
isort src tests
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

If you discover a security vulnerability, please open an issue or contact the maintainers directly. All security vulnerabilities will be promptly addressed.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.
