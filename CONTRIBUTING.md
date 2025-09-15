# 🤝 Contributing to Causal Memory Core

Thank you for your interest in contributing to Causal Memory Core! This document provides guidelines for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)

## 🌟 Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and follow our Code of Conduct.

### Our Standards

- **Be respectful** and inclusive in all interactions
- **Be collaborative** and help others learn and grow
- **Be constructive** when providing feedback
- **Focus on what's best** for the community and project

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- OpenAI API key (for testing)

### Setup Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Causal-Memory-Core.git
   cd Causal-Memory-Core
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. **Configure environment**:
   ```bash
   cp .env.template .env
   # Add your OPENAI_API_KEY to .env
   ```

6. **Run tests** to verify setup:
   ```bash
   python -m pytest tests/ -v
   ```

## 🔄 Development Workflow

### Branch Strategy

- `main` - Stable, production-ready code
- `develop` - Integration branch for features
- `feature/feature-name` - Individual feature development
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Critical production fixes

### Workflow Steps

1. **Create a feature branch** from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Write tests** for new functionality

4. **Run the test suite**:
   ```bash
   python run_comprehensive_tests.py
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push and create a Pull Request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## 💻 Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some project-specific guidelines:

#### Code Formatting
- **Line length**: 88 characters (Black formatter)
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Follow isort configuration
- **Docstrings**: Google style docstrings

#### Example Function
```python
def add_causal_event(
    self, 
    event_description: str, 
    timestamp: Optional[datetime] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> EventID:
    """Add a new event to the causal memory system.
    
    Args:
        event_description: Human-readable description of the event
        timestamp: When the event occurred (defaults to now)
        metadata: Additional structured data about the event
        
    Returns:
        Unique identifier for the stored event
        
    Raises:
        ValueError: If event_description is empty
        DatabaseError: If storage operation fails
    """
    if not event_description.strip():
        raise ValueError("Event description cannot be empty")
    
    # Implementation here
    return event_id
```

#### Type Hints
- Use type hints for all function parameters and return values
- Import types from `typing` module when needed
- Use `Optional[Type]` for nullable parameters

#### Error Handling
- Use specific exception types
- Include helpful error messages
- Log errors appropriately
- Clean up resources in finally blocks

### Project Structure

```
src/
├── memory_core.py          # Core memory system
├── causal_engine.py        # Causal relationship detection
├── semantic_search.py      # Semantic search functionality
├── mcp_server.py          # MCP protocol server
├── config.py              # Configuration management
└── utils/
    ├── database.py        # Database utilities
    ├── embeddings.py      # Embedding generation
    └── validation.py      # Input validation
```

## 🧪 Testing Requirements

### Test Categories

1. **Unit Tests** (`tests/test_*.py`)
   - Test individual functions and classes
   - Mock external dependencies
   - Fast execution (< 1s per test)

2. **Integration Tests** (`tests/integration/`)
   - Test component interactions
   - Use real databases (in-memory)
   - Moderate execution time

3. **End-to-End Tests** (`tests/e2e/`)
   - Test complete workflows
   - Use real OpenAI API (with rate limits)
   - Slower execution but comprehensive

### Writing Tests

#### Test Structure
```python
import pytest
from src.memory_core import CausalMemoryCore

class TestCausalMemoryCore:
    """Test suite for CausalMemoryCore functionality."""
    
    def setup_method(self):
        """Setup test environment before each test."""
        self.memory = CausalMemoryCore(database_path=":memory:")
    
    def test_add_event_success(self):
        """Test successful event addition."""
        # Arrange
        event_description = "Test event occurred"
        
        # Act
        event_id = self.memory.add_event(event_description)
        
        # Assert
        assert event_id is not None
        assert isinstance(event_id, str)
        
    def test_add_event_empty_description_raises_error(self):
        """Test that empty event description raises ValueError."""
        with pytest.raises(ValueError, match="Event description cannot be empty"):
            self.memory.add_event("")
```

#### Test Requirements
- **Descriptive names**: Test names should clearly describe what is being tested
- **AAA pattern**: Arrange, Act, Assert structure
- **Isolation**: Tests should not depend on each other
- **Coverage**: Aim for >90% code coverage
- **Documentation**: Include docstrings for test classes and complex tests

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_memory_core.py

# Run with coverage
python -m pytest --cov=src tests/

# Run integration tests only
python -m pytest tests/integration/

# Run tests with detailed output
python -m pytest -v
```

## 📝 Submitting Changes

### Pull Request Process

1. **Ensure your branch is up to date**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout feature/your-feature
   git rebase develop
   ```

2. **Run the full test suite**:
   ```bash
   python run_comprehensive_tests.py
   ```

3. **Create a Pull Request** with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Link to any related issues
   - Screenshots for UI changes (if applicable)

### PR Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code is commented appropriately
- [ ] Documentation updated if needed
- [ ] No new warnings introduced
```

## 🐛 Issue Guidelines

### Bug Reports

When reporting bugs, please include:

- **Environment details** (Python version, OS, etc.)
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Error messages** or logs
- **Minimal example** that demonstrates the issue

### Feature Requests

For new features, please provide:

- **Clear description** of the proposed feature
- **Use case** and motivation
- **Proposed implementation** approach (if any)
- **Potential impact** on existing functionality

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation needs improvement
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority:high` - Critical issues
- `priority:low` - Nice to have

## 🏆 Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes for significant contributions
- GitHub contributor graphs
- Special acknowledgments for major features

## 📞 Getting Help

If you need help or have questions:

- **GitHub Discussions** - For general questions and discussions
- **Issues** - For bugs and feature requests
- **Discord** - Real-time community chat (link in README)
- **Email** - maintainers@example.com for private concerns

## 📚 Additional Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Git Best Practices](https://git-scm.com/doc)

Thank you for contributing to Causal Memory Core! 🙏