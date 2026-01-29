# Contributing to wintouch

Thank you for your interest in contributing to wintouch. This document provides
guidelines and best practices for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Making Changes](#making-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- **Be respectful**: Treat all contributors with respect regardless of background or experience level
- **Be constructive**: Provide helpful feedback focused on improving the project
- **Be collaborative**: Work together towards common goals
- **Be patient**: Remember that contributors are often volunteers with limited time

## Getting Started

### Prerequisites

Before contributing, ensure you have:

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.8+ | Runtime and testing |
| Git | 2.20+ | Version control |
| Windows | 8+ | Development and testing |
| C Compiler | MSVC 14+ or MinGW-w64 | Building C extension |
| Windows SDK | 8.0+ | Windows API headers |

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/wintouch
   cd wintouch
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/phdye/wintouch
   ```

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- `pytest>=7.0` - Testing framework
- `black>=23.0` - Code formatter
- `mypy>=1.0` - Static type checker

## Development Environment

### Recommended Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Cygwin/Git Bash)
source .venv/Scripts/activate

# Install in development mode
pip install -e ".[dev]"

# Build C extension
python setup.py build_ext --inplace
```

### IDE Configuration

#### Visual Studio Code

`.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "[python]": {
        "editor.formatOnSave": true
    }
}
```

#### PyCharm

1. Set Python interpreter to `.venv/Scripts/python.exe`
2. Enable Black formatter: Settings → Tools → Black
3. Enable MyPy: Settings → Editor → Inspections → Python → Type Checker

### Building the C Extension

```bash
# Standard build
python setup.py build_ext --inplace

# Debug build (with symbols)
python setup.py build_ext --inplace --debug

# Clean rebuild
rm -rf build/ *.pyd
python setup.py build_ext --inplace
```

## Making Changes

### Branch Naming

Use descriptive branch names with prefixes:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New features | `feature/gesture-helpers` |
| `fix/` | Bug fixes | `fix/memory-leak-inject` |
| `docs/` | Documentation | `docs/api-examples` |
| `refactor/` | Code refactoring | `refactor/contact-conversion` |
| `test/` | Test additions | `test/multitouch-coverage` |

### Workflow

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make changes** following [Coding Standards](#coding-standards)

4. **Test thoroughly** (see [Testing](#testing))

5. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add gesture helper functions"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature
   ```

7. **Create pull request** on GitHub

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, whitespace)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(inject): add support for touch flags parameter

fix(initialize): handle ERROR_ACCESS_DENIED gracefully

docs(api): add examples for multitouch gestures

refactor(module.c): extract contact conversion to helper function
```

## Coding Standards

### Python Code

#### Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Maximum line length: 88 characters (Black default)

```bash
# Format code
black wintouch/ tests/

# Check without modifying
black --check wintouch/ tests/
```

#### Type Hints

Use type hints for all public functions:

```python
def tap(x: int, y: int, *, duration: float = 0.0) -> None:
    """
    Perform a touch tap at the specified coordinates.

    Args:
        x: X coordinate in pixels
        y: Y coordinate in pixels
        duration: Hold duration in seconds (default: 0)
    """
    ...
```

Run type checking:
```bash
mypy wintouch/
```

#### Docstrings

Use Google-style docstrings:

```python
def inject(contacts: list[dict]) -> bool:
    """
    Inject touch input events.

    Args:
        contacts: List of touch contact dictionaries. Each dictionary must
            contain 'x', 'y', and 'flags' keys. Optional keys include
            'pointer_id', 'pressure', 'orientation', 'contact_width',
            and 'contact_height'.

    Returns:
        True on success.

    Raises:
        RuntimeError: If touch injection is not initialized.
        ValueError: If contacts list is empty or exceeds max_contacts.
        OSError: If the Windows API call fails.

    Example:
        >>> import wintouch
        >>> wintouch.initialize()
        >>> wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])
        True
    """
```

### C Code

#### Style

- Follow [Linux kernel style](https://www.kernel.org/doc/html/latest/process/coding-style.html) with modifications
- 4-space indentation (not tabs)
- Opening brace on same line for functions
- Maximum line length: 100 characters

```c
static PyObject* wintouch_function(PyObject *self, PyObject *args) {
    /* Variables at start of block */
    PyObject *result = NULL;
    int value;

    /* Validate arguments */
    if (!PyArg_ParseTuple(args, "i", &value)) {
        return NULL;
    }

    /* Main logic */
    if (value < 0) {
        PyErr_SetString(PyExc_ValueError, "value must be non-negative");
        return NULL;
    }

    /* Cleanup and return */
    result = PyLong_FromLong(value * 2);
    return result;
}
```

#### Error Handling

Always check return values and handle errors:

```c
/* Check memory allocation */
ptr = malloc(size);
if (ptr == NULL) {
    PyErr_NoMemory();
    return NULL;
}

/* Check Win32 API calls */
if (!SomeWin32Function()) {
    DWORD err = GetLastError();
    PyErr_Format(PyExc_OSError, "Function failed (error %lu)", err);
    goto cleanup;
}

/* Use cleanup pattern for complex functions */
cleanup:
    free(ptr);
    return result;
```

#### Memory Management

- Always free allocated memory
- Use `calloc()` for arrays that need zero-initialization
- Document ownership of pointers

```c
/* Caller owns returned memory */
static char* allocate_buffer(size_t size) {
    return (char *)malloc(size);
}

/* Function manages its own memory */
static PyObject* process_data(const char *data) {
    char *buffer = malloc(strlen(data) + 1);
    PyObject *result = NULL;

    if (buffer == NULL) {
        PyErr_NoMemory();
        return NULL;
    }

    /* ... process ... */

    result = PyUnicode_FromString(buffer);
    free(buffer);  /* Always free before returning */
    return result;
}
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_basic.py

# Run specific test
pytest tests/test_basic.py::test_is_available

# Run with coverage
pytest --cov=wintouch --cov-report=html
```

### Writing Tests

#### Test File Organization

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_basic.py        # Basic functionality tests
├── test_initialize.py   # initialize() tests
├── test_inject.py       # inject() tests
├── test_diagnose.py     # diagnose() tests
└── test_constants.py    # Constants tests
```

#### Test Structure

```python
import pytest
import wintouch


class TestInitialize:
    """Tests for wintouch.initialize()."""

    @pytest.fixture(autouse=True)
    def skip_if_unavailable(self):
        """Skip tests if touch injection is unavailable."""
        if not wintouch.is_available():
            pytest.skip("Touch injection not available")

    def test_default_parameters(self):
        """Test initialize with default parameters."""
        wintouch.initialize()
        assert wintouch.is_initialized()
        assert wintouch.get_max_contacts() == 1

    def test_max_contacts_range(self):
        """Test initialize accepts valid max_contacts values."""
        for n in range(1, 11):
            wintouch.initialize(max_contacts=n)
            assert wintouch.get_max_contacts() == n

    def test_invalid_max_contacts_zero(self):
        """Test initialize rejects max_contacts=0."""
        with pytest.raises(ValueError) as exc_info:
            wintouch.initialize(max_contacts=0)
        assert "max_contacts must be between 1 and 10" in str(exc_info.value)

    def test_invalid_max_contacts_eleven(self):
        """Test initialize rejects max_contacts=11."""
        with pytest.raises(ValueError):
            wintouch.initialize(max_contacts=11)
```

#### Fixtures

```python
# conftest.py
import pytest
import wintouch


@pytest.fixture
def initialized():
    """Fixture that ensures touch injection is initialized."""
    if not wintouch.is_available():
        pytest.skip("Touch injection not available")
    wintouch.initialize(max_contacts=2)
    yield
    # No cleanup needed - state persists until process exit


@pytest.fixture
def touch_available():
    """Fixture that skips tests if touch injection unavailable."""
    if not wintouch.is_available():
        pytest.skip("Touch injection not available")
```

### Test Categories

#### Unit Tests

Test individual functions in isolation:

```python
def test_is_available_returns_bool():
    """is_available() must return a boolean."""
    result = wintouch.is_available()
    assert isinstance(result, bool)
```

#### Integration Tests

Test interactions between functions:

```python
def test_inject_requires_initialize(touch_available):
    """inject() must fail if initialize() not called."""
    # Note: Cannot easily reset state, so this may need process isolation
    pass
```

#### Functional Tests

Test complete workflows:

```python
def test_tap_gesture(initialized):
    """Test a complete tap gesture sequence."""
    # Down
    wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])
    # Up
    wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_UP}])
```

## Documentation

### Documentation Requirements

All public APIs must be documented:

1. **Python docstrings**: Google-style, with types, args, returns, raises, examples
2. **C comments**: Function-level comments describing purpose and behavior
3. **API documentation**: Man-page style markdown in `doc/api/`
4. **README updates**: For user-visible changes

### Man-Page Style Documentation

API documentation follows man(3) conventions:

```markdown
# function_name(3) - wintouch

## NAME

function_name - brief description

## SYNOPSIS

```python
import wintouch

result = wintouch.function_name(arg1, arg2, *, kwarg=default)
```

## DESCRIPTION

Detailed description of functionality...

## PARAMETERS

**arg1** (type)
: Description of first argument

**arg2** (type)
: Description of second argument

**kwarg** (type, optional)
: Description of keyword argument. Default: `default`

## RETURN VALUE

Description of return value...

## ERRORS

**ValueError**
: Raised when...

**OSError**
: Raised when...

## EXAMPLES

```python
# Example code
```

## SEE ALSO

- [related_function](related_function.md)
- [External documentation](https://...)

## NOTES

Additional implementation notes...
```

### Building Documentation

Currently, documentation is plain Markdown. Future plans may include Sphinx.

## Submitting Changes

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New code has test coverage
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up-to-date with main

### Pull Request Template

```markdown
## Description

Brief description of changes...

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to change)
- [ ] Documentation update

## Testing

Describe how you tested these changes...

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or feature works
- [ ] New and existing unit tests pass locally
```

## Review Process

### Review Criteria

Pull requests are reviewed for:

1. **Correctness**: Does the code work as intended?
2. **Style**: Does it follow coding standards?
3. **Testing**: Is there adequate test coverage?
4. **Documentation**: Is the change documented?
5. **Performance**: Are there performance implications?
6. **Security**: Are there security considerations?

### Review Timeline

- Initial response: Within 3 business days
- Full review: Within 1 week
- Merge: After approval and CI passing

### Addressing Feedback

- Respond to all comments
- Push fixes as new commits (for easier review)
- Request re-review after addressing all feedback

## Release Process

### Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Checklist

1. Update version in `pyproject.toml` and `wintouch/__init__.py`
2. Update CHANGELOG (if exists)
3. Create release commit: `git commit -m "chore: release v1.2.3"`
4. Tag release: `git tag v1.2.3`
5. Push tag: `git push origin v1.2.3`
6. Create GitHub release
7. Build and upload to PyPI:
   ```bash
   python -m build
   twine upload dist/*
   ```

## Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search closed issues and PRs
3. Open a new issue with the "question" label

Thank you for contributing to wintouch!
