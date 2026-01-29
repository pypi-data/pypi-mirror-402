# Contributing to Simple Python Utils 🤝

First off, thank you for considering contributing to Simple Python Utils! It's people like you that make this project better.

## 📜 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Style Guide](#style-guide)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## 🤝 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Standards

- **Be respectful** and inclusive
- **Be collaborative** and constructive
- **Be patient** with newcomers
- **Be mindful** of your language

## 🚀 Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/simple-python-utils.git
   cd simple-python-utils
   ```
3. **Set up** the development environment (see below)
4. **Create** a new branch for your feature/fix:
   ```bash
   git checkout -b feature/amazing-feature
   ```

## 🔧 Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- pip

### Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### Verify Setup

```bash
# Run tests
pytest

# Run quality checks
black --check .
isort --check .
flake8
mypy simple_utils/

# Run pre-commit on all files
pre-commit run --all-files
```

## 📝 How to Contribute

### Types of Contributions

We welcome several types of contributions:

- 🐛 **Bug fixes**
- ✨ **New features** (simple utilities only)
- 📚 **Documentation improvements**
- 🧹 **Code cleanup**
- 🧪 **Test improvements**

### Contribution Workflow

1. **Check** existing issues and PRs to avoid duplication
2. **Create an issue** for large changes to discuss first
3. **Write code** following our style guide
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Run quality checks** locally
7. **Submit a pull request**

## 🎨 Style Guide

### Code Style

We follow strict coding standards:

- **PEP 8** compliance (enforced by `flake8`)
- **Black** formatting (88 character line limit)
- **isort** for import organization
- **Type hints** for all functions and methods
- **Google-style docstrings**

### Principles

1. **Clarity over cleverness**
2. **Simplicity over abstraction**
3. **Readability over compactness**
4. **Explicit over implicit**

### Example Code Style

```python
def example_function(param: str, count: int = 1) -> str:
    """Example function demonstrating our style.
    
    Args:
        param: Description of the parameter.
        count: Number of times to repeat (default: 1).
        
    Returns:
        The processed string result.
        
    Raises:
        TypeError: If param is not a string.
        ValueError: If count is negative.
        
    Examples:
        >>> example_function("hello", 2)
        "hellohello"
    """
    if not isinstance(param, str):
        raise TypeError(f"Expected str, got {type(param).__name__}")
    
    if count < 0:
        raise ValueError("Count must be non-negative")
    
    return param * count
```

## 🧪 Testing

### Test Requirements

- **100% code coverage** is required
- **All tests must pass** on all supported Python versions
- **Test both success and error cases**
- **Use descriptive test names**

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=simple_utils --cov-report=term-missing

# Run specific test file
pytest tests/test_core.py

# Run specific test
pytest tests/test_core.py::TestPrintMessage::test_print_message_valid_string
```

### Writing Tests

```python
class TestNewFeature:
    """Tests for new_feature function."""
    
    def test_new_feature_success(self):
        """Test successful operation."""
        result = new_feature("input")
        assert result == "expected"
        
    def test_new_feature_type_error(self):
        """Test TypeError for invalid input."""
        with pytest.raises(TypeError, match="Expected str, got int"):
            new_feature(123)
```

## 🔄 Pull Request Process

### Before Submitting

1. **Ensure all tests pass**:
   ```bash
   pytest
   ```

2. **Run quality checks**:
   ```bash
   black simple_utils/ tests/
   isort simple_utils/ tests/
   flake8 simple_utils/ tests/
   mypy simple_utils/
   ```

3. **Update documentation** if needed

4. **Add entry to CHANGELOG.md** (if applicable)

### PR Guidelines

- **Use descriptive titles** following conventional commits
- **Fill out the PR template** completely
- **Keep changes focused** - one feature/fix per PR
- **Include tests** for new functionality
- **Maintain 100% test coverage**
- **Update documentation** as needed

### PR Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add new utility function`
- `fix: resolve issue with type validation`
- `docs: update README with new examples`
- `test: add tests for edge cases`
- `refactor: simplify error handling`

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Clear description** of the issue
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment information** (OS, Python version, package version)
- **Code sample** demonstrating the issue
- **Full error traceback** if applicable

### Feature Requests

For new features:

- **Describe the use case** and motivation
- **Provide code examples** of proposed API
- **Explain why it fits** the project's scope
- **Consider alternatives** and trade-offs

## 📊 Project Scope

### What We Accept

- ✅ **Simple utility functions**
- ✅ **Bug fixes and improvements**
- ✅ **Documentation enhancements**
- ✅ **Test improvements**
- ✅ **Performance optimizations**

### What We Don't Accept

- ❌ **Complex features or frameworks**
- ❌ **External dependencies** (except dev dependencies)
- ❌ **Object-oriented solutions** (prefer functions)
- ❌ **Breaking changes** without major version bump
- ❌ **Platform-specific code**

## 🎆 Recognition

Contributors will be:

- **Listed in CONTRIBUTORS.md**
- **Mentioned in release notes**
- **Credited in commit messages**
- **Thanked publicly** on social media

## 📞 Getting Help

If you need help:

- **Check existing issues** for similar problems
- **Read the documentation** thoroughly
- **Create an issue** with your question
- **Tag maintainers** if needed: @fjmpereira20

---

**Thank you for contributing! 🚀**

Your efforts help make this project better for everyone. We appreciate your time and expertise!