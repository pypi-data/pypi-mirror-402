# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1]

### Changed
- Improved README description for better clarity and readability

## [1.0.0]

### Added
- Initial release of docker-detector Python package
- `is_docker()` function to check if the current process is running inside a Docker container
- Linux-only detection using multiple methods:
  - Check for `/.dockerenv` file existence
  - Check `/proc/self/cgroup` for Docker references
  - Check `/proc/self/mountinfo` for Docker container paths
- `force_refresh` parameter to bypass cache and perform fresh detection
- LRU cache optimization for repeated calls using `functools.lru_cache`
- Type hints for better IDE support and type checking
- Zero dependencies for minimal overhead
- Comprehensive test suite with unit tests covering all detection methods
- Python 3.8+ compatibility

### Features
- Fast and reliable Docker container detection
- Multiple detection methods for robustness
- Cached results for performance optimization
- Linux platform support
- Graceful error handling for file system operations

[1.0.1]: https://github.com/ysskrishna/social-links/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/ysskrishna/docker-detector/releases/tag/v1.0.0

