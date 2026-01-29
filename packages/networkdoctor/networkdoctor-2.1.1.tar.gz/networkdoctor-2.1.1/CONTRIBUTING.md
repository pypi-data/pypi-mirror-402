# Contributing to NetworkDoctor

**Created by: frankvena25**

Thank you for your interest in contributing to NetworkDoctor! This project is open-source and we welcome contributions from the community.

## Owner Control

**Project Owner:** frankvena25  
**Maintainer:** frankvena25

As the project owner, I (frankvena25) maintain final control over:
- Pull Request reviews and merges
- Release scheduling and versioning
- Roadmap and feature prioritization
- Community guidelines and standards

## How to Contribute

### 1. Fork the Repository

Fork the repository on GitHub to create your own copy.

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes
git checkout -b fix/your-bug-name
```

### 3. Make Your Changes

- Write clean, documented code
- Follow PEP 8 style guidelines
- Add type hints where appropriate
- Write meaningful commit messages

### 4. Add Tests

Ensure your changes have test coverage:

```bash
pytest tests/
pytest --cov=networkdoctor tests/
```

### 5. Update Documentation

- Update README.md if adding new features
- Add docstrings to new functions/classes
- Update CHANGELOG.md if applicable

### 6. Submit a Pull Request

1. Push your branch to your fork
2. Create a Pull Request on GitHub
3. Fill out the PR template with:
   - Description of changes
   - Related issues (if any)
   - Testing performed
   - Screenshots (if UI changes)

## Pull Request Process

1. **Review**: All PRs will be reviewed by the maintainer (frankvena25)
2. **Testing**: PRs must pass all existing tests
3. **Code Quality**: Code must meet style and quality standards
4. **Documentation**: PRs must include appropriate documentation
5. **Approval**: PRs require maintainer approval before merging

## Code Style

- **PEP 8**: Follow Python PEP 8 style guide
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Write docstrings for all functions and classes (Google style)
- **Line Length**: Maximum 120 characters per line
- **Function Length**: Keep functions under 300 lines
- **Imports**: Group imports (stdlib, third-party, local) and use absolute imports

Example:

```python
"""Module docstring here."""
from typing import List, Dict, Any
import asyncio


class ExampleClass:
    """Class docstring."""
    
    async def example_method(self, param: List[str]) -> Dict[str, Any]:
        """
        Method docstring.
        
        Args:
            param: Description of param
            
        Returns:
            Description of return value
        """
        pass
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=networkdoctor tests/

# Run specific test file
pytest tests/test_core.py

# Run with verbose output
pytest -v tests/
```

### Writing Tests

- Use pytest for all tests
- Follow naming convention: `test_*.py`
- Test both success and failure cases
- Mock external dependencies
- Aim for >80% code coverage

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/networkdoctor.git
cd networkdoctor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .
pip install pytest pytest-cov black flake8 mypy

# Install in development mode
pip install -e .
```

## Reporting Issues

When reporting issues:

1. Use GitHub Issues
2. Include:
   - Description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version)
   - Error messages/logs

## Feature Requests

For feature requests:

1. Open a GitHub Issue
2. Use the "Feature Request" template
3. Describe the use case and benefits
4. Be patient - features are prioritized by the maintainer

## Roadmap

The project roadmap is maintained by frankvena25. Check the GitHub Projects or Issues for current priorities.

## Community Guidelines

- Be respectful and professional
- Help others when possible
- Follow the code of conduct
- Focus on constructive feedback

## Questions?

- Open a GitHub Discussion
- Check existing Issues/PRs
- Review documentation in `docs/`

Thank you for contributing to NetworkDoctor! 🩺🌐



