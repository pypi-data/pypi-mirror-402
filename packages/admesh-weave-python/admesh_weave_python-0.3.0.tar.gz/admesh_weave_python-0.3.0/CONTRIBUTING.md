# Contributing to admesh-weave-python

Thank you for your interest in contributing to admesh-weave-python!

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip or rye for package management

### Installation

1. Clone the repository:
```bash
git clone https://github.com/GouniManikumar12/admesh-weave-python.git
cd admesh-weave-python
```

2. Install dependencies:
```bash
# Using pip
pip install -e ".[dev]"

# Or using rye
rye sync
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=admesh_weave

# Run specific test file
pytest tests/test_client.py
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code
ruff format

# Lint code
ruff check .

# Fix linting issues automatically
ruff check --fix .

# Type check
mypy .
```

### Running Examples

```bash
# Set your API key
export ADMESH_API_KEY=your-api-key-here

# Run the basic usage example
python examples/basic_usage.py
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep line length to 120 characters
- Use snake_case for function and variable names
- Use PascalCase for class names

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting a PR
- Aim for high test coverage
- Include both unit tests and integration tests where appropriate

## Pull Request Process

1. Fork the repository
2. Create a new branch for your feature (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Reporting Issues

When reporting issues, please include:

- Python version
- admesh-weave-python version
- Operating system
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any error messages or stack traces

## Questions?

If you have questions, please open an issue or contact us at mani@useadmesh.com.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

