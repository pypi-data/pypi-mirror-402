# Contributing to HyperDev LLMRouter

Thank you for your interest in contributing to HyperDev LLMRouter! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### Prerequisites
- Python 3.9+
- Git

### Development Setup

1. Fork the repository and clone it:
```bash
git clone https://github.com/yourusername/llmrouter.git
cd llmrouter
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

## Making Changes

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### Code Style

We follow PEP 8 with these tools:
- **Black** - Code formatting (line length: 100)
- **Ruff** - Linting
- **MyPy** - Type checking (optional)

Run checks before committing:
```bash
black src/ examples/
ruff check src/ examples/ --fix
mypy src/
```

### Adding a New Provider

1. Create a new file in `src/hyperdev/llmrouter/providers/`
2. Extend `BaseProvider` with required methods:
   - `stream_chat()` - Implement streaming logic
   - `validate_model()` - Validate model strings
3. Register in `src/hyperdev/llmrouter/providers/__init__.py`:
   ```python
   from .your_provider import YourProvider

   PROVIDER_REGISTRY[LLMProvider.YOUR_PROVIDER] = YourProvider
   ```
4. Create config example in `config_examples/`
5. Add tests in `tests/`

### Testing

Run the full test suite:
```bash
pytest tests/ -v
pytest tests/ --cov=hyperdev --cov-report=term-missing
```

Run specific tests:
```bash
pytest tests/test_config.py -v
pytest tests/test_providers/ -v
```

### Writing Tests

Test files follow the pattern: `tests/test_*.py`

Example test:
```python
import pytest
from pathlib import Path
from hyperdev.llmrouter import chat_stream, LLMProvider
from hyperdev.llmrouter.exceptions import ValidationError

def test_empty_prompt_raises_validation_error():
    with pytest.raises(ValidationError):
        list(chat_stream("", LLMProvider.OPENAI, "gpt-4"))
```

## Committing Changes

Write clear commit messages following the format:

```
<type>: <subject>

<body>

Closes #<issue-number>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Example:
```
feat: add support for custom timeout in stream_chat

Allows users to specify custom timeout values for streaming operations.
Adds timeout parameter to BaseProvider.stream_chat() method.

Closes #42
```

## Creating a Pull Request

1. Push your branch:
```bash
git push origin feature/your-feature-name
```

2. Create a PR on GitHub with:
   - Clear title and description
   - Reference to related issues
   - Summary of changes
   - Test coverage information

## Documentation

### Updating README

- Keep it concise and current
- Add examples for new features
- Update API reference
- Test all code examples

### Docstring Style

Use Google-style docstrings:

```python
def stream_chat(self, prompt: str, llm_string: str) -> Iterator[StreamChunk]:
    """
    Stream chat response from the provider.

    Args:
        prompt: User's message or prompt
        llm_string: Model identifier specific to the provider

    Yields:
        StreamChunk objects containing response content

    Raises:
        StreamingError: If streaming fails
    """
```

## Release Process

Maintainers:

1. Update version in `pyproject.toml`
2. Update CHANGELOG
3. Create release notes
4. Tag release: `git tag v0.2.0`
5. GitHub Actions automatically publishes to PyPI

## Reporting Issues

When reporting bugs, include:
- Python version
- Package version
- Minimal reproducible example
- Error messages and tracebacks
- Operating system

## Questions?

- Open an issue for discussions
- Check existing issues for similar topics
- Review the documentation

## License

By contributing, you agree your code will be licensed under the MIT License.

Thank you for contributing! 🎉
