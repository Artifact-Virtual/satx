# Contributing to SATx

Thank you for your interest in contributing to SATx! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your changes
5. Make your changes
6. Test your changes
7. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Docker and Docker Compose (optional, for containerized development)
- RTL-SDR or compatible SDR hardware (for testing SDR functionality)

### Setup Instructions

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/satx.git
cd satx

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
python tests/run_all_tests.py
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug Fixes**: Fix issues in existing code
- **New Features**: Add new functionality
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Performance**: Optimize existing code
- **Refactoring**: Improve code quality without changing functionality

### Finding Issues to Work On

- Check the [Issues](https://github.com/Artifact-Virtual/satx/issues) page
- Look for issues labeled `good first issue` or `help wanted`
- Comment on an issue to indicate you're working on it
- Ask questions if you need clarification

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line Length**: Maximum 100 characters (not the standard 79)
- **Indentation**: 4 spaces (no tabs)
- **Docstrings**: Use Google style docstrings
- **Type Hints**: Encouraged for function signatures
- **Imports**: Organized in groups (standard library, third-party, local)

### Code Quality Tools

We use the following tools to maintain code quality:

- **Black**: Code formatting (line length 100)
- **Flake8**: Linting
- **MyPy**: Type checking
- **isort**: Import sorting
- **pylint**: Additional linting

Run all checks before submitting:

```bash
# Format code
black . --line-length 100

# Sort imports
isort .

# Run linters
flake8 .
pylint scripts/ models/ web/

# Type checking
mypy scripts/ models/ web/
```

### Documentation Standards

- All public functions, classes, and modules must have docstrings
- Use Google-style docstrings
- Include examples in docstrings where helpful
- Keep README.md and other documentation up to date
- Add inline comments for complex logic

Example docstring:

```python
def predict_passes(latitude: float, longitude: float, elevation: float) -> list:
    """Predict satellite passes for a given ground station location.
    
    Args:
        latitude: Ground station latitude in degrees (-90 to 90)
        longitude: Ground station longitude in degrees (-180 to 180)
        elevation: Ground station elevation in meters above sea level
        
    Returns:
        List of pass predictions, each containing:
            - satellite_name (str): Name of the satellite
            - aos (datetime): Acquisition of signal time
            - los (datetime): Loss of signal time
            - max_elevation (float): Maximum elevation in degrees
            
    Raises:
        ValueError: If coordinates are out of valid ranges
        
    Example:
        >>> passes = predict_passes(40.7128, -74.0060, 10)
        >>> print(passes[0]['satellite_name'])
        'ISS (ZARYA)'
    """
    pass
```

## Testing Guidelines

### Test Coverage Requirements

- All new code must include tests
- Aim for at least 80% code coverage
- Critical paths should have 100% coverage
- Test edge cases and error conditions

### Running Tests

```bash
# Run all tests
python tests/run_all_tests.py

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term
```

### Writing Tests

- Use descriptive test names: `test_predict_passes_with_invalid_coordinates()`
- Follow the Arrange-Act-Assert pattern
- Use fixtures for common setup
- Mock external dependencies (APIs, hardware, file system when appropriate)
- Test both success and failure cases

Example test:

```python
import pytest
from scripts.predict_passes import predict_passes

def test_predict_passes_returns_list():
    """Test that predict_passes returns a list of predictions."""
    # Arrange
    lat, lon, elev = 40.7128, -74.0060, 10
    
    # Act
    passes = predict_passes(lat, lon, elev)
    
    # Assert
    assert isinstance(passes, list)
    assert len(passes) > 0
    
def test_predict_passes_invalid_latitude_raises_error():
    """Test that invalid latitude raises ValueError."""
    # Arrange
    lat, lon, elev = 91.0, -74.0060, 10  # Invalid latitude
    
    # Act & Assert
    with pytest.raises(ValueError, match="latitude"):
        predict_passes(lat, lon, elev)
```

## Pull Request Process

### Before Submitting

1. **Update your branch** with the latest changes from main:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all tests** and ensure they pass:
   ```bash
   python tests/run_all_tests.py
   ```

3. **Run code quality checks**:
   ```bash
   black . --line-length 100 --check
   flake8 .
   mypy scripts/ models/ web/
   ```

4. **Update documentation** if needed

5. **Add or update tests** for your changes

### Submitting a Pull Request

1. **Create a descriptive title**:
   - Good: "Add Doppler correction for VHF frequencies"
   - Bad: "Fix bug"

2. **Write a clear description**:
   - What changes were made?
   - Why were these changes necessary?
   - How were the changes tested?
   - Any breaking changes or migration notes?

3. **Link related issues**:
   - Use "Fixes #123" or "Closes #456" in the description

4. **Keep changes focused**:
   - One feature or fix per pull request
   - Avoid mixing refactoring with feature additions

5. **Respond to feedback**:
   - Address review comments promptly
   - Push additional commits to the same branch
   - Request re-review when ready

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (or documented if unavoidable)
```

## Reporting Bugs

### Before Reporting

1. **Check existing issues** to avoid duplicates
2. **Verify the bug** in the latest version
3. **Gather information** about your environment

### Bug Report Template

```markdown
**Description**
Clear and concise description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. Configure setting '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- SATx Version: [e.g., 1.0.0]
- SDR Hardware: [e.g., RTL-SDR V3]

**Logs**
Relevant log output or error messages.

**Additional Context**
Any other relevant information.
```

## Suggesting Enhancements

### Enhancement Proposal Template

```markdown
**Feature Description**
Clear description of the proposed feature.

**Motivation**
Why is this feature needed? What problem does it solve?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
What other approaches were considered?

**Additional Context**
Mockups, examples, or other relevant information.
```

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussions
- **Pull Requests**: Code review and collaboration

### Getting Help

- Check the [documentation](docs/)
- Search existing issues and discussions
- Ask questions in GitHub Discussions
- Be patient and respectful

### Recognition

Contributors are recognized in:
- The project README
- Release notes
- The CHANGELOG

## License

By contributing to SATx, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to SATx! Your efforts help make satellite observation more accessible to everyone.
