# Repository Guidelines

This file provides guidance to AI coding agents when working with code in this repository.

## Conventions

Read relevant `docs/agent/` files before proceeding:
- `workflow.md` — **read before starting any feature** (issues, branching, PRs)

---

## Project Overview

**hloc-cli** is a CLI wrapper for the [Hierarchical-Localization (hloc)](https://github.com/cvg/Hierarchical-Localization) package. It provides a tyro-based command-line interface for common hloc workflows.

## Commands

```bash
# Run
hloc --help

# Install
pip install -e .
```

## Project Structure

- `hloc_cli.py` — main CLI entry point using tyro
- `pyproject.toml` — project config

## Dependencies

- `tyro` — CLI argument parsing
- `loguru` — logging
- `hloc` — upstream Hierarchical-Localization package

## Code Style

- Follow existing patterns in `hloc_cli.py`
- Type hints encouraged
- Keep CLI consistent with hloc conventions

## Code Workflow

1. **Before editing**: read files first; understand existing code
2. **After code changes**: test CLI manually with various workflows
3. **Commits**: short imperative summary; use `feat:`/`fix:`/`docs:` prefixes
