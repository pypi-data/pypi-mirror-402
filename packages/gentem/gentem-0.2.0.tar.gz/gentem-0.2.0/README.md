# Gentem

![Python Version](https://img.shields.io/pypi/pyversions/gentem)
![License](https://img.shields.io/pypi/l/gentem)
![PyPI Version](https://img.shields.io/pypi/v/gentem)
![PyPI Status](https://img.shields.io/pypi/status/gentem)

![Downloads](https://img.shields.io/pypi/dm/gentem)
![Last Commit](https://img.shields.io/github/last-commit/knightlesssword/gentem)
![Contributors](https://img.shields.io/github/contributors/knightlesssword/gentem)


A Python CLI template boilerplate generator for quickly scaffolding Python projects.

## Features

- **Project Scaffolding**: Generate Python projects with a single command
- **Multiple Project Types**: Support for library, CLI tool, and script projects
- **FastAPI Templates**: Pre-configured FastAPI project templates with optional database support
- **Opinionated Structure**: Best practices baked into every template
- **Interactive Preview**: `--dry-run` option to preview before creating files

## Installation

```bash
pip install gentem
```

Or install from source:

```bash
git clone https://github.com/knightlesssword/gentem.git
cd gentem
pip install -e .
```

## Usage

### Creating a New Project

```bash
# Create a library project
gentem new mylib --type library

# Create a CLI tool project
gentem new mycli --type cli

# Create a simple script project
gentem new myscript --type script

# With author and description
gentem new mylib --type library --author "John Doe" --description "My library"

# With license
gentem new mylib --type library --license mit
gentem new mylib --type library --license apache
gentem new mylib --type library --license gpl

# Preview without creating files
gentem new mylib --type library --dry-run
```

### Creating a FastAPI Project

```bash
# Create a basic FastAPI project
gentem fastapi myapi

# Create with async mode and lifespan
gentem fastapi myapi --async

# Create with database support (asyncpg)
gentem fastapi myapi --db asyncpg

# Combine options
gentem fastapi myapi --async --db asyncpg --author "John Doe"
```

## Project Structure

### Library Template
```
mylib/
├── src/
│   └── mylib/
│       ├── __init__.py
│       └── core.py
├── tests/
│   ├── __init__.py
│   └── test_core.py
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

### FastAPI Template
```
myapi/
├── src/
│   └── myapi/
│       ├── __init__.py
│       ├── main.py              # FastAPI application
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py        # Settings
│       │   └── exceptions.py    # Custom exceptions
│       ├── deps/
│       │   └── __init__.py      # Dependencies
│       ├── utils/
│       │   └── __init__.py      # Utility functions
│       ├── v1/
│       │   ├── __init__.py
│       │   └── apis/
│       │       ├── __init__.py
│       │       └── routes.py    # API routes
│       ├── services/
│       │   └── __init__.py      # Business logic
│       ├── schemas/
│       │   └── __init__.py      # Pydantic schemas
│       └── models/
│           └── __init__.py      # SQLAlchemy models
├── .env
├── requirements.txt
├── .gitignore
└── README.md
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check --fix .

# Type checking
mypy .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
