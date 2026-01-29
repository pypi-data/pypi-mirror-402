# Contributing to LockLLM Python SDK

Thank you for your interest in contributing to LockLLM! We welcome contributions from the community to help make AI security more accessible and effective.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Detailed steps to reproduce the issue
- Expected behavior vs actual behavior
- Code samples demonstrating the issue
- Your environment (Python version, OS, SDK version)
- Error messages and stack traces

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When suggesting an enhancement:

- Use a clear and descriptive title
- Provide a detailed description of the proposed functionality
- Explain why this enhancement would be useful
- Include code examples if applicable

### Code Contributions

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following our coding standards
3. **Add tests** for any new functionality
4. **Update documentation** as needed
5. **Submit a pull request**

## Development Setup

### Prerequisites

- Python 3.8+ and pip
- Virtual environment tool (venv or virtualenv)
- Git

### Setup Steps

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR-USERNAME/lockllm-pip.git
cd lockllm-pip
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e ".[dev]"
```

4. Install peer dependencies for testing (optional):
```bash
pip install openai anthropic
```

5. Run tests to ensure everything works:
```bash
pytest
```

### Available Commands

- `pytest` - Run the test suite
- `pytest --cov=lockllm --cov-report=html` - Generate coverage report
- `pytest -v` - Run tests with verbose output
- `mypy lockllm/` - Run type checking
- `black lockllm/` - Format code with Black
- `isort lockllm/` - Sort imports
- `flake8 lockllm/` - Run linting

## Pull Request Process

1. **Update Documentation**: Ensure README.md and relevant documentation reflect your changes

2. **Add Tests**: All new features and bug fixes must include tests

3. **Run the Full Test Suite**:
```bash
# Type checking
mypy lockllm/

# Tests
pytest

# Linting
flake8 lockllm/

# Format code
black lockllm/
isort lockllm/
```

4. **Update CHANGELOG**: Add your changes to the Unreleased section

5. **Write Clear Commit Messages**:
   - Use present tense ("Add feature" not "Added feature")
   - Use imperative mood ("Move cursor to..." not "Moves cursor to...")
   - Reference issues and pull requests when relevant

6. **Submit PR**:
   - Fill out the PR template completely
   - Link related issues
   - Request review from maintainers

7. **Address Review Feedback**: Be responsive to review comments and make requested changes

## Coding Standards

### Python Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Provide docstrings for all public APIs
- Avoid using `Any` - use `Union`, `Optional`, or proper types

### Code Style

We use Black, isort, and Flake8 for consistent code style:

```bash
# Format code
black lockllm/
isort lockllm/

# Check linting
flake8 lockllm/
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `LockLLM`, `PromptInjectionError`)
- **Functions/Methods**: snake_case (e.g., `create_openai`, `scan_prompt`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`)
- **Private members**: Prefix with underscore (e.g., `_process_request`)
- **Modules**: snake_case (e.g., `http_client.py`)

### File Organization

- Place source code in `lockllm/`
- Place tests in `tests/` directory
- Export public API through `lockllm/__init__.py`
- Keep files focused and single-purpose

## Testing Guidelines

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Aim for >90% code coverage
- Tests should be isolated and deterministic

### Writing Tests

We use pytest for testing:

```python
import pytest
from lockllm import LockLLM

def test_scan_input_successfully():
    """Test scanning input returns expected results."""
    client = LockLLM(api_key='test-key')
    result = client.scan(input='Hello world')
    assert result.safe is True
```

### Test Categories

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test wrapper functions with provider SDKs
- **Error Handling Tests**: Verify proper error handling

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scan.py

# Run with coverage
pytest --cov=lockllm --cov-report=html

# Run in verbose mode
pytest -v

# Run specific test
pytest tests/test_scan.py::test_scan_input_successfully
```

## Documentation

### Code Documentation

- Add docstrings for all public APIs
- Include parameter descriptions and return types
- Provide usage examples in docstrings

Example:
```python
def scan(self, input: str, sensitivity: Sensitivity = "medium", **options) -> ScanResponse:
    """Scan a prompt for security threats before sending to an LLM.

    Args:
        input: Text to scan for security threats
        sensitivity: Detection level - "low", "medium" (default), or "high"
            - "low": Fewer false positives, may miss sophisticated attacks
            - "medium": Balanced detection (recommended)
            - "high": Maximum protection, may have more false positives
        **options: Additional options (headers, timeout)

    Returns:
        ScanResponse containing safety classification and threat details

    Raises:
        AuthenticationError: If API key is invalid
        RateLimitError: If rate limit is exceeded
        NetworkError: If request fails

    Example:
        >>> client = LockLLM(api_key="your-key")
        >>> result = client.scan(
        ...     input="User input here",
        ...     sensitivity="medium"
        ... )
        >>> print(f"Safe: {result.safe}")
    """
```

### README Updates

- Update feature lists when adding capabilities
- Add examples for new functionality
- Keep API reference section current
- Update performance metrics if applicable

## Security Considerations

- Never commit API keys or secrets
- Be cautious with user input in examples
- Follow security best practices
- Report security vulnerabilities privately (see [SECURITY.md](SECURITY.md))

## Questions?

- Open an issue for questions about contributing
- Email support@lockllm.com for private inquiries
- Check existing issues and pull requests for similar discussions

## License

By contributing to LockLLM, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to LockLLM! Your efforts help make AI applications more secure for everyone.
