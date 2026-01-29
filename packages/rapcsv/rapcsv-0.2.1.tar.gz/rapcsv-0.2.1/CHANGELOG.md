# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-01-19

### Fixed
- Fixed all GitHub links in README to use `blob/master` instead of `blob/main`
- Added performance optimization goal to roadmap to match or surpass aiocsv performance

## [0.2.0] - 2026-01-19

### Added
- **Advanced Quoting Modes**: Support for QUOTE_NOTNULL (4) and QUOTE_STRINGS (6) quoting modes
- **Header Detection and Manipulation**: Automatic header detection in AsyncDictReader, plus `add_field()`, `remove_field()`, and `rename_field()` methods
- **Configurable Write Buffer Sizes**: `write_size` parameter for Writer and AsyncDictWriter
- **Field Size Limit Enforcement**: `field_size_limit` parameter now properly enforced in Reader operations
- **Improved Line Number Tracking**: Accurate line_num tracking that counts actual lines for multi-line records
- **Dialect Presets**: Excel, Unix, and RFC 4180 dialect presets (`EXCEL_DIALECT`, `UNIX_DIALECT`, `RFC4180_DIALECT`)
- **Type Conversion Features**: Automatic type inference and per-column converters via `convert_types()` utility function
- **Performance Benchmarks**: Comprehensive benchmark suite comparing with csv, aiocsv, and pandas
- **Expanded Test Coverage**: Additional aiocsv compatibility tests covering advanced features
- Ruff configuration for Python linting and formatting
- Python linting job in CI/CD workflows
- Comprehensive documentation structure matching rapfiles
- `CHANGELOG.md` for version history tracking
- `BUGS_AND_IMPROVEMENTS.md` for issue tracking
- Enhanced testing documentation with coverage and troubleshooting guides
- Development setup documentation with code quality tools
- `.pypi-release-ready` marker file for release tracking

### Changed
- Updated CI/CD to use `pip install -e ".[test]"` for test dependencies
- Enhanced README with feature categories and current status section
- Improved documentation organization and navigation
- Updated roadmap to reflect Phase 2 completion
- Enhanced release checklist with new validation steps
- Improved line_num tracking to accurately count lines in multi-line records

### Documentation
- Added comprehensive testing guide with multiple sections
- Added documentation index linking to all docs
- Updated roadmap with Phase 2 completion status
- Enhanced API reference documentation
- Added benchmark documentation

## [0.1.2] - 2026-01-16

### Added
- Support for async file-like objects from `aiofiles` and `rapfiles`
- `AsyncDictReader` and `AsyncDictWriter` classes for dictionary-based CSV operations
- Enhanced file handle support for better integration with async file I/O libraries

### Changed
- Improved file handle detection and event loop integration
- Enhanced error handling for file handle operations

## [0.1.1] - 2026-01-16

### Added
- Python 3.14 support with ABI3 forward compatibility
- Python 3.13 support with ABI3 forward compatibility
- Updated CI/CD workflows to test and build for Python 3.13 and 3.14

### Fixed
- Fixed exception registration issue where exceptions created with `create_exception!` were not accessible from Python
- Fixed exception handling for ABI3 compatibility (using `create_exception!` macro)
- Explicitly registered exception classes in Python module

### Changed
- Updated exception handling to use ABI3-compatible approach
- Enhanced compatibility across Python 3.8 through 3.14

## [0.1.0] - 2025-01-12

### Added
- Streaming file reading - files are read incrementally without loading entire file into memory
- Context manager support (`async with`) for automatic resource cleanup
- CSV-specific exception types (`CSVError`, `CSVFieldCountError`)
- Improved error handling with detailed error messages and file context
- `close()` method for explicit file handle closure
- aiocsv compatibility aliases (`AsyncReader`, `AsyncWriter`)
- Comprehensive test coverage (29 tests including aiocsv compatibility tests)
- aiocsv test suite migration - tests adapted from [aiocsv test suite](https://github.com/MKuranowski/aiocsv/tree/master/tests)
- RFC 4180 compliant CSV parsing and writing
- Proper handling of quoted fields with special characters

### Changed
- Enhanced error messages with file path context
- Improved file handle lifecycle management

## [0.0.2] - 2024-XX-XX

### Added
- Position tracking: Reader now maintains position state across `read_row()` calls
- File handle reuse: Writer reuses file handle across multiple `write_row()` calls
- CSV escaping: Implemented RFC 4180 compliant CSV escaping and quoting
- Input validation: Added path validation (non-empty, no null bytes)
- Type stubs: Added `.pyi` type stubs for better IDE support and type checking

### Fixed
- Security fixes: Upgraded dependencies (pyo3 0.27, pyo3-async-runtimes 0.27)
- Fixed CSV injection vulnerability

### Changed
- Improved error handling: Enhanced error messages with file path context

## [0.0.1] - 2024-XX-XX

### Added
- Initial release
- Basic async CSV reading and writing functionality
- True async I/O with GIL-independent operations
- Rust-backed implementation using Tokio

[Unreleased]: https://github.com/eddiethedean/rapcsv/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/eddiethedean/rapcsv/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/eddiethedean/rapcsv/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/eddiethedean/rapcsv/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/eddiethedean/rapcsv/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/eddiethedean/rapcsv/compare/v0.0.2...v0.1.0
[0.0.2]: https://github.com/eddiethedean/rapcsv/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/eddiethedean/rapcsv/releases/tag/v0.0.1
