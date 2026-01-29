# Docker Detector

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/ysskrishna/docker-detector/blob/main/LICENSE)
![Tests](https://github.com/ysskrishna/docker-detector/actions/workflows/test.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/docker-detector)](https://pypi.org/project/docker-detector/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/docker-detector?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/docker-detector)

Detect if your Python process is running inside a Docker container. Inspired by the popular [is-docker](https://github.com/sindresorhus/is-docker) npm package. Supports cached results with optional refresh.

## Features

- Fast and reliable Docker container detection
- Multiple detection methods for robustness
- Cached results for performance optimization
- Zero dependencies, minimal overhead
- Type hints for better IDE support

## Installation

```bash
pip install docker-detector
```

Or using `uv`:

```bash
uv add docker-detector
```

## Usage

### Check if running inside Docker

```python
from docker_detector import is_docker

if is_docker():
    print("Running inside a Docker container")
else:
    print("Not running inside a Docker container")
```

### Force refresh cache

```python
from docker_detector import is_docker

# Use cached result (default)
is_docker()  # Fast, uses cache

# Force a fresh check, bypassing cache
is_docker(force_refresh=True)  # Performs new detection
```

## Credits

This package is inspired by the [is-docker](https://github.com/sindresorhus/is-docker) npm package by [Sindre Sorhus](https://github.com/sindresorhus).

## Changelog

See [CHANGELOG.md](https://github.com/ysskrishna/docker-detector/blob/main/CHANGELOG.md) for a detailed list of changes and version history.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct, development setup, and the process for submitting pull requests.

## Support

If you find this library useful, please consider:

- ⭐ **Starring** the repository on GitHub to help others discover it.
- 💖 **Sponsoring** to support ongoing maintenance and development.

[Become a Sponsor on GitHub](https://github.com/sponsors/ysskrishna) | [Support on Patreon](https://patreon.com/ysskrishna)

## License

MIT License - see [LICENSE](https://github.com/ysskrishna/docker-detector/blob/main/LICENSE) file for details.

## Author

**Y. Siva Sai Krishna**

- GitHub: [@ysskrishna](https://github.com/ysskrishna)
- LinkedIn: [ysskrishna](https://linkedin.com/in/ysskrishna)

