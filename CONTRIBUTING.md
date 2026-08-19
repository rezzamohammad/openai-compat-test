# Contributing to OpenAI Compatible API Tester

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment tool (venv, virtualenv, or similar)

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/rezzamohammad/openai-compat-test.git
cd openai-compat-test
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your local configuration
```

## Development Workflow

### Running Tests

```bash
# Run all tests
python3 -m pytest

# Run with coverage
python3 -m pytest --cov=src --cov-report=term-missing

# Run specific test file
python3 -m pytest tests/test_config.py

# Run with verbose output
python3 -m pytest -v

# Run specific test file (UI flows)
python3 -m pytest tests/test_ui_flows.py
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Keep functions focused and single-purpose
- Write docstrings for public APIs
- Maximum line length: 100 characters

### Making Changes

1. Create a new branch for your feature or fix:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and add tests

3. Run the test suite to ensure everything passes:
```bash
python3 -m pytest
```

4. Commit your changes with a clear message:
```bash
git commit -m "Add feature: description of your changes"
```

5. Push to your fork and submit a pull request

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues and pull requests after the first line

Example:
```
Add support for Anthropic API format

- Implement Anthropic response parser
- Add tests for Claude API responses
- Update documentation

Fixes #123
```

## Testing

### Test Coverage

We aim for high test coverage. New features should include tests that cover:

- Happy path scenarios
- Error conditions
- Edge cases
- Integration with existing functionality

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names that explain what is being tested
- Use fixtures for common setup
- Mock external dependencies (API calls, file I/O)

Example:
```python
def test_parse_response_handles_empty_content():
    """Test that parser handles responses with empty content gracefully."""
    # Test implementation
```

## Documentation

- Update README.md if you change functionality
- Add docstrings to new functions and classes
- Update .env.example if you add new configuration options
- Keep documentation in sync with code changes

## Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Add a clear description of your changes
4. Reference any related issues
5. Wait for review from maintainers

### Pull Request Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests passing
- [ ] Code follows project style
- [ ] Commit messages are clear
- [ ] No merge conflicts

## Reporting Issues

### Bug Reports

Include:
- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages or logs
- Configuration (with secrets removed)

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (optional)
- Examples of how it would be used

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## Questions?

If you have questions about contributing, feel free to:
- Open an issue with the "question" label
- Start a discussion in GitHub Discussions
- Reach out to the maintainers

## Adding Support for New Providers

When adding support for new API providers:

1. **Add format detection logic** in `src/response_parser.py`:
   - Update `ResponseParser._detect_format()` method
   - Add provider-specific detection logic

2. **Add parser method** `_parse_provider_name()`:
   - Create a new parser method for the provider format
   - Follow existing patterns (e.g., `_parse_anthropic()`, `_parse_google()`)

3. **Ensure output normalization**:
   - All parsers must output standard OpenAI format
   - Include `id`, `choices`, `message`, `content` fields

4. **Test with real API responses**:
   - Add test cases in `tests/test_response_parser.py`
   - Test with actual API response samples
   - Verify edge cases and error conditions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
