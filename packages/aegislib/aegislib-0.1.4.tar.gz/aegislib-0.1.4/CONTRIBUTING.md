# Contributing to Aegis Python SDK

Thank you for your interest in contributing to Aegis! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

We expect all contributors to be respectful and professional. Please be kind and courteous in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your changes
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip or another package manager

### Installation

1. Clone the repository:

```bash
git clone https://github.com/mrsidrdx/aegis-python-sdk.git
cd aegis-python-sdk
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:

```bash
pip install -e ".[dev]"
```

## Running Tests

### Run all tests

```bash
pytest
```

### Run tests with coverage

```bash
pytest --cov=aegis --cov-report=html --cov-report=term
```

### Run specific test file

```bash
pytest tests/test_config.py
```

### Run with verbose output

```bash
pytest -v
```

### View coverage report

After running tests with coverage, open `htmlcov/index.html` in your browser.

## Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Type checking

### Format code

```bash
black aegis/ tests/
```

### Run linter

```bash
ruff check aegis/ tests/
```

### Run type checker

```bash
mypy aegis/
```

### Run all checks

```bash
make lint
```

## Making Changes

### Adding New Features

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Write tests for your feature first (TDD approach)
3. Implement your feature
4. Ensure all tests pass
5. Update documentation if necessary

### Fixing Bugs

1. Create a new branch from `main`:
   ```bash
   git checkout -b fix/bug-description
   ```

2. Write a test that reproduces the bug
3. Fix the bug
4. Ensure all tests pass

### Code Coverage

We maintain 100% test coverage. All new code must include tests.

To check coverage:

```bash
pytest --cov=aegis --cov-report=term-missing
```

## Submitting Changes

### Before Submitting

1. Ensure all tests pass:
   ```bash
   pytest
   ```

2. Ensure code is formatted:
   ```bash
   black aegis/ tests/
   ```

3. Ensure linting passes:
   ```bash
   ruff check aegis/ tests/
   ```

4. Ensure type checking passes:
   ```bash
   mypy aegis/
   ```

5. Update CHANGELOG.md with your changes

### Pull Request Process

1. Push your changes to your fork
2. Create a pull request against the `main` branch
3. Provide a clear description of the changes
4. Link any related issues
5. Wait for review and address feedback

### Pull Request Guidelines

- Keep PRs focused and small
- Include tests for all changes
- Update documentation as needed
- Follow existing code style
- Write clear commit messages

## Commit Message Format

We follow conventional commit format:

```
type(scope): subject

body

footer
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

Example:

```
feat(guard): add support for custom decision handlers

Added ability to provide custom handlers for each decision effect type,
allowing users to customize behavior beyond the default implementation.

Closes #123
```

## Questions?

If you have questions, please:

1. Check existing issues and discussions
2. Open a new issue with your question
3. Be clear and provide context

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions make Aegis better for everyone. Thank you for taking the time to contribute!
