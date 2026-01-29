# SEE Python SDK

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

A modern Python SDK for **SEE Content Sharing services** (Short URL, Text, File, etc.), featuring async support, full type safety, and Python 3.11+ capabilities.

## Features

- 🚀 **Modern Python**: Built with Python 3.11+ features (type hints, pattern matching, dataclasses)
- 🔄 **Async First**: Fully async API based on `asyncio` and `httpx`
- 📝 **Type Safe**: 100% type annotated with mypy strict mode support
- 🛡️ **Reliable**: Built-in retry mechanism, error handling, and rate limiting
- 🧪 **Well Tested**: Comprehensive test suite with pytest
- 📦 **Standard Compliant**: Follows PEP 517/518 with `pyproject.toml`

## Requirements

- Python 3.11+
- httpx >= 0.27.0

## Installation

```bash
pip install see-sdk
```

or you can visit [PyPI page](https://pypi.org/project/see-sdk/) for more options.

Install from source:

```bash
git clone https://github.com/sdotee/sdk.py see-python-sdk
cd see-python-sdk && pip install -e .
```

## Quick Start

### Environment Setup

Set your API key as an environment variable:

```bash
export SEE_API_KEY="your-api-key-here"
```

### Basic Usage

See [examples/quickstart.py](examples/quickstart.py) for a simple example of how to create a short URL.

## Examples

The [examples](examples/) directory contains comprehensive usage examples for all features:

- **Quick Start**: [examples/quickstart.py](examples/quickstart.py) - Basic usage for Short URLs.
- **Short URLs**: [examples/complete_example.py](examples/complete_example.py) - Advanced Short URL features (custom slugs, tags, expiration).
- **Text Sharing**: [examples/text_sharing.py](examples/text_sharing.py) - Creating, updating, and deleting shared text.
- **File Sharing**: [examples/file_sharing.py](examples/file_sharing.py) - Uploading and managing files.
- **Advanced Usage**: [examples/advanced_example.py](examples/advanced_example.py) - Complex workflows and resource management.

## Development

### Setup

```bash
git clone https://github.com/yourusername/see-sdk.git
cd see-sdk

python -m venv venv
source venv/bin/activate  # Linux/macOS

pip install -e ".[dev]"
pre-commit install
```

### Testing

```bash
pytest
pytest --cov=see --cov-report=html
pytest tests/test_client.py
```

### Code Quality

```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

## API Reference

### SeeClient

Main client class for API interactions.

#### Methods

- `create_short_url(request)` - Create short URL
- `update_short_url(request)` - Update short URL
- `delete_short_url(request)` - Delete short URL
- `get_domains()` - Get available domains
- `get_tags()` - Get available tags

### Models

#### CreateShortUrlRequest

```python
@dataclass
class CreateShortUrlRequest:
    domain: str
    target_url: str
    title: str
    custom_slug: str | None = None
    expire_at: int | None = None
    tag_ids: list[int] | None = None
```

### Exceptions

- `SeeError` - Base exception
- `APIError` - API error
- `AuthenticationError` - Authentication error
- `ValidationError` - Validation error
- `RateLimitError` - Rate limit error
- `NotFoundError` - Not found error

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) file.
