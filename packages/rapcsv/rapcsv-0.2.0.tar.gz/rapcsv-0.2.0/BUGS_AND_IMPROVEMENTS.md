# Bugs and Improvements

This document tracks known issues, limitations, and planned improvements for `rapcsv`.

## Known Limitations

### Current Limitations (v0.2.0)

- **File handle support (aiofiles/rapfiles integration)**: Partially implemented (structure in place, full bridging deferred)
  - Basic support for async file-like objects is implemented
  - Some edge cases in event loop integration may need refinement
  - Full compatibility testing with all aiofiles/rapfiles features is ongoing

- **DictReader/DictWriter dict conversion**: Structure implemented, some methods need async/GIL refinement
  - `AsyncDictReader` and `AsyncDictWriter` classes are available
  - Some advanced features may need further optimization
  - Full aiocsv parity for dict operations is in progress

- **Not designed for synchronous use cases**: This library is specifically designed for async/await patterns
  - Synchronous blocking operations are not supported
  - Users should use Python's standard `csv` module for synchronous operations

### Phase 2 Planned Improvements

- **Advanced CSV dialect support**: Custom delimiters, quote characters, line terminators, quoting modes
- **Header detection and manipulation**: Automatic header detection, header row skipping, named field access
- **Iterator protocol support**: `async for` iterator support (`__aiter__` / `__anext__`)
- **Additional reader/writer methods**: `read_rows(n)`, `skip_rows(n)`, enhanced `writerows()` support
- **Type conversion**: Automatic type inference, configurable type converters, date/time parsing
- **Performance optimizations**: Configurable buffer sizes, zero-copy operations where possible

### Phase 3 Planned Improvements

- **Zero-copy streaming**: Memory-mapped file support for large files, direct buffer passing
- **Advanced parsing options**: Custom field parsers, validation rules and schemas, error recovery strategies
- **Schema support**: CSV schema definitions, type validation per column, required/optional field support
- **Parallel processing**: Multi-file processing, chunk-based parallel parsing, concurrent read/write operations
- **Monitoring & observability**: Performance metrics export, progress callbacks, resource usage tracking

## Known Issues

### None Currently

No critical bugs are currently known. If you encounter an issue, please report it via GitHub Issues.

## Improvement Suggestions

### Code Quality

- ✅ Added Ruff for Python linting and formatting (v0.2.0)
- Consider adding mypy for stricter type checking
- Consider adding test coverage reporting

### Documentation

- ✅ Added CHANGELOG.md (v0.2.0)
- ✅ Added BUGS_AND_IMPROVEMENTS.md (v0.2.0)
- Consider adding more usage examples
- Consider adding performance benchmarks

### Testing

- Expand test coverage for edge cases
- Add property-based testing for CSV parsing
- Add fuzzing tests for malformed CSV files
- Add performance benchmarks

### CI/CD

- ✅ Enhanced CI with Python linting (v0.2.0)
- Consider adding automated dependency updates
- Consider adding automated security scanning

## Reporting Issues

If you find a bug or have a suggestion for improvement, please:

1. Check if the issue is already documented here or in GitHub Issues
2. If not, create a new GitHub Issue with:
   - Clear description of the problem or suggestion
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Python version and platform information
   - Minimal code example if applicable

## Contributing

Contributions are welcome! See the [ROADMAP.md](docs/ROADMAP.md) for planned improvements and development priorities.
