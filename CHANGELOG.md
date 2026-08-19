# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/0.2.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v0.2.0.html).

## [0.2.0] - 2026-08-19

### Added
- Universal multi-format response parser supporting SSE, JSON, NDJSON, and provider-specific formats
- Smart endpoint routing between chat and non-chat endpoints
- Response text caching to prevent "content already consumed" errors
- Exponential backoff retry mechanism with configurable settings
- Interactive TUI setup mode with rich prompts
- Model selection interface
- Comprehensive test suite with 18 tests
- Support for Anthropic, Google, Azure, and custom provider formats
- JSON output to file option
- Verbose mode with detailed logging
- Package metadata in pyproject.toml
- Contributing guidelines
- Development requirements file

### Changed
- Improved error messages with provider context
- Enhanced URL construction to avoid double `/v1/v1/` paths
- Refactored response parsing into dedicated parser class
- Reduced default retry attempts from 3 to 2 for faster feedback
- Updated retry configuration for mass testing scenarios

### Fixed
- SSE stream handling for streaming responses
- Content already consumed errors with response caching
- Double `/v1/v1/` URL construction issue
- No text in response parsing errors
- Parse failures for empty responses

### Security
- Masked API key display in interactive mode
- Environment variable validation
- No hardcoded credentials in codebase

## [0.1.0] - 2026-08-17 - Initial Release

### Added
- Basic OpenAI-compatible API testing
- Multi-model support
- JSON output formatting
- Environment variable configuration
- Command-line interface
- Model discovery from `/v1/models` endpoint
- Request timeout and delay settings
- MIT License

[0.2.0]: https://github.com/rezzamohammad/openai-compat-test/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rezzamohammad/openai-compat-test/releases/tag/v0.1.0
