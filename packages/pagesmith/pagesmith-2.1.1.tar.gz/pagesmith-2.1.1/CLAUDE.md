# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pagesmith is a Python library for splitting HTML and text into pages while preserving document structure and content integrity. It uses the fast lxml parser for HTML processing and provides utilities for:

- Splitting HTML into pages while preserving HTML tags and document structure
- Splitting pure text into pages at natural break points (paragraphs, sentences)
- Detecting chapters in text to create Table of Contents

## Development Setup

**Important**: Always run `. ./activate.sh` before development. This script requires [uv](https://github.com/astral-sh/uv) to be installed.

The project uses:
- `uv` for dependency management and virtual environment
- `invoke` for task automation
- `pytest` for testing with Allure reports
- `ruff` for linting (configured in pyproject.toml)
- `mypy` for type checking
- `pre-commit` for code quality hooks

## Common Commands

### Environment Setup
```bash
source ./activate.sh  # Sets up or activates virtual environment using uv
```

**IMPORTANT**: Always activate the virtual environment before running any commands. Use `source ./activate.sh` before each command.

### Testing
```bash
source ./activate.sh && python -m pytest                    # Run all tests
source ./activate.sh && python -m pytest tests/test_*.py    # Run specific test files
source ./activate.sh && python -m pytest --doctest-modules  # Run doctests (configured in pytest.ini)
```

### Code Quality
```bash
source ./activate.sh && invoke pre           # Run pre-commit checks on all files
```

**IMPORTANT**: Always use `invoke pre` or `pre-commit run --all-files` for code quality checks. Never run ruff or mypy directly.

### Documentation
```bash
invoke docs-en  # Preview English docs (opens Chrome at localhost:8000)
invoke docs-ru  # Preview Russian docs
```

### Version Management
```bash
invoke version      # Show current version
invoke ver-bug      # Bump bug version
invoke ver-feature  # Bump feature version
invoke ver-release  # Bump release version
```

## Architecture Overview

### Core Components

The library is organized around three main classes:

1. **`PageSplitter`** (`src/pagesmith/page_splitter.py`): Splits plain text into pages at natural breakpoints like paragraphs and sentences. Uses configurable target length with error tolerance.

2. **`HtmlPageSplitter`** (`src/pagesmith/html_page_splitter.py`): Splits HTML content into pages while preserving tag structure and document integrity. Operates on lxml element trees.

3. **`ChapterDetector`** (`src/pagesmith/chapter_detector.py`): Detects chapter headings in text using regex patterns to create Table of Contents with titles and positions.

### Supporting Modules

- **`parser.py`**: Contains HTML parsing utilities including `parse_partial_html()` and `etree_to_str()`. Handles malformed HTML gracefully and uses special tag renaming to avoid lxml's built-in handling of `html`, `head`, `body` tags.

- **`refine_html.py`**: HTML refinement utilities (also has Beautiful Soup variant in `refine_html_beautiful_soup.py`).

### Key Design Patterns

- **Fake Root Wrapping**: The parser wraps HTML fragments in a `pagesmith-root` element to create a single tree structure, making processing easier.

- **Error Tolerance**: Both page splitters use configurable error tolerance (default 25%) around target page lengths for flexible page breaks.

- **Iterator Pattern**: Page splitters return iterators for memory-efficient processing of large documents.

- **Special Tag Handling**: The parser renames special HTML tags (html→pagesmith-html, etc.) to prevent lxml's automatic document structure handling.

## Testing

Tests are located in `tests/` and use pytest with Allure reporting. Test files follow the pattern `test_*.py`. The project has comprehensive test coverage including:

- Unit tests for all main components
- Integration tests for HTML and text splitting
- Chapter detection tests
- Parser edge case handling

Allure reports are generated in `allure-results/` directory.

## Build and Packaging

The project uses modern Python packaging with:
- `pyproject.toml` for configuration
- `src/pagesmith/` layout
- Hatchling as build backend
- Version managed in `src/pagesmith/__about__.py`
