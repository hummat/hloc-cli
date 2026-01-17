# Contributing to hloc-cli

Thanks for your interest in contributing! This document covers development setup and guidelines.

## Development Setup

### Prerequisites

- Python 3.8+
- [Hierarchical-Localization (hloc)](https://github.com/cvg/Hierarchical-Localization) installed

### Quick Start

```bash
# Clone the repository
git clone https://github.com/hummat/hloc-cli.git
cd hloc-cli

# Install
pip install -e .

# Run
hloc --help
```

## Code Style

- Follow existing patterns in `hloc_cli.py`
- Type hints encouraged
- Keep the CLI interface simple and consistent with hloc conventions

## Pull Request Process

1. **Create an issue first** for non-trivial changes
2. **Fork and branch** from `main`
3. **Make your changes** following the style guide
4. **Test manually** with various hloc workflows
5. **Submit PR** using the template

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Keep the first line under 72 characters
- Reference issues: "Fix matching options (#42)"

## Questions?

- Open a [Discussion](https://github.com/hummat/hloc-cli/discussions) for questions
- Check existing [Issues](https://github.com/hummat/hloc-cli/issues) for known problems
