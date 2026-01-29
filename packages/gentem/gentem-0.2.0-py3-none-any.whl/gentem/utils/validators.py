"""Input validators for Gentem."""

import re
from pathlib import Path
from typing import Optional


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_python_identifier(name: str) -> bool:
    """Check if the name is a valid Python identifier."""
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
    return bool(re.match(pattern, name))


def validate_project_name(name: str) -> str:
    """Validate and return the project name.

    Args:
        name: The project name to validate.

    Returns:
        The validated project name.

    Raises:
        ValidationError: If the name is invalid.
    """
    if not name:
        raise ValidationError("Project name cannot be empty.")

    if not validate_python_identifier(name):
        raise ValidationError(
            f"'{name}' is not a valid Python project name. "
            "Use only letters, numbers, and underscores, starting with a letter or underscore."
        )

    # Check for Python reserved words
    reserved_words = {
        "and", "as", "assert", "async", "await", "break", "class", "continue",
        "def", "del", "elif", "else", "except", "finally", "for", "from",
        "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
        "or", "pass", "raise", "return", "try", "while", "with", "yield", "True",
        "False", "None",
    }

    if name.lower() in reserved_words:
        raise ValidationError(
            f"'{name}' is a Python reserved word and cannot be used as a project name."
        )

    return name


def validate_license_type(license_type: str) -> str:
    """Validate and normalize the license type.

    Args:
        license_type: The license type to validate.

    Returns:
        The normalized license type.

    Raises:
        ValidationError: If the license type is invalid.
    """
    valid_licenses = {"mit", "apache", "gpl", "bsd", "none", ""}

    normalized = license_type.lower().strip()
    if normalized not in valid_licenses:
        raise ValidationError(
            f"Invalid license type: '{license_type}'. "
            f"Valid options are: {', '.join(sorted(valid_licenses))}"
        )

    return normalized


def validate_project_type(project_type: str) -> str:
    """Validate and normalize the project type.

    Args:
        project_type: The project type to validate.

    Returns:
        The normalized project type.

    Raises:
        ValidationError: If the project type is invalid.
    """
    valid_types = {"library", "cli", "script"}

    normalized = project_type.lower().strip()
    if normalized not in valid_types:
        raise ValidationError(
            f"Invalid project type: '{project_type}'. "
            f"Valid options are: {', '.join(sorted(valid_types))}"
        )

    return normalized


def validate_db_type(db_type: str) -> Optional[str]:
    """Validate the database type.

    Args:
        db_type: The database type to validate.

    Returns:
        The normalized database type or None.

    Raises:
        ValidationError: If the database type is invalid.
    """
    if not db_type:
        return None

    valid_db_types = {"asyncpg", "sqlite", "postgres", "postgresql"}

    normalized = db_type.lower().strip()
    if normalized not in valid_db_types:
        raise ValidationError(
            f"Invalid database type: '{db_type}'. "
            f"Valid options are: {', '.join(sorted(valid_db_types))} or empty for none."
        )

    # Normalize postgres/postgresql to asyncpg for now
    if normalized in {"postgres", "postgresql"}:
        normalized = "asyncpg"

    return normalized


def validate_output_path(path: str, dry_run: bool = False) -> Path:
    """Validate the output path.

    Args:
        path: The path to validate.
        dry_run: Whether this is a dry run.

    Returns:
        The validated Path object.

    Raises:
        ValidationError: If the path is invalid.
    """
    output_path = Path(path)

    if output_path.exists() and not dry_run:
        raise ValidationError(
            f"Directory '{output_path}' already exists. "
            "Please choose a different project name or remove the existing directory."
        )

    return output_path
