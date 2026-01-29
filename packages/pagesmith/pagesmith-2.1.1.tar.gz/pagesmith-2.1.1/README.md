[![Build Status](https://github.com/andgineer/pagesmith/workflows/CI/badge.svg)](https://github.com/andgineer/pagesmith/actions)
[![Coverage](https://raw.githubusercontent.com/andgineer/pagesmith/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/andgineer/pagesmith/blob/python-coverage-comment-action-data/htmlcov/index.html)
# pagesmith

Split HTML into pages while preserving HTML tags and respecting the original document structure.
Utilizes the blazingly fast lxml parser.

Split pure text into pages at natural break points such as paragraphs or sentences.

Detect chapters in pure text to create a Table of Contents.

# Documentation

[Pagesmith](https://andgineer.github.io/pagesmith/)


# Developers

Do not forget to run `. ./activate.sh`.

For development, you need [uv](https://github.com/astral-sh/uv) installed.

Use [pre-commit](https://pre-commit.com/#install) hooks for code quality:

    pre-commit install

## Allure test report

* [Allure report](https://andgineer.github.io/pagesmith/builds/tests/)

# Scripts

Install [invoke](https://docs.pyinvoke.org/en/stable/) preferably with [pipx](https://pypa.github.io/pipx/):

    pipx install invoke

For a list of available scripts run:

    invoke --list

For more information about a script run:

    invoke <script> --help


## Coverage report
* [Coveralls](https://coveralls.io/github/andgineer/pagesmith)

> Created with cookiecutter using [template](https://github.com/andgineer/cookiecutter-python-package)
