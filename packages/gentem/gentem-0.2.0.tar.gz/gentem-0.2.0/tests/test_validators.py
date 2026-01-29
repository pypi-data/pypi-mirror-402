"""Tests for the validators module."""

import pytest

from gentem.utils.validators import (
    validate_project_name,
    validate_python_identifier,
    validate_license_type,
    validate_project_type,
    validate_db_type,
    ValidationError,
)


class TestValidatePythonIdentifier:
    """Tests for validate_python_identifier function."""

    def test_valid_identifiers(self):
        """Test valid Python identifiers."""
        assert validate_python_identifier("myproject") is True
        assert validate_python_identifier("my_project") is True
        assert validate_python_identifier("_private") is True
        assert validate_python_identifier("MyClass") is True
        assert validate_python_identifier("project123") is True

    def test_invalid_identifiers(self):
        """Test invalid Python identifiers."""
        assert validate_python_identifier("123project") is False
        assert validate_python_identifier("my-project") is False
        assert validate_python_identifier("my.project") is False
        assert validate_python_identifier("") is False


class TestValidateProjectName:
    """Tests for validate_project_name function."""

    def test_valid_project_names(self):
        """Test valid project names."""
        assert validate_project_name("myproject") == "myproject"
        assert validate_project_name("my_project") == "my_project"
        assert validate_project_name("project123") == "project123"

    def test_invalid_project_names(self):
        """Test invalid project names."""
        with pytest.raises(ValidationError) as exc_info:
            validate_project_name("")
        assert "cannot be empty" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            validate_project_name("123project")
        assert "not a valid Python project name" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            validate_project_name("my-project")
        assert "not a valid Python project name" in str(exc_info.value)

    def test_reserved_words(self):
        """Test that reserved words are rejected."""
        for word in ["class", "def", "import", "return", "if", "else"]:
            with pytest.raises(ValidationError) as exc_info:
                validate_project_name(word)
            assert "reserved word" in str(exc_info.value)


class TestValidateLicenseType:
    """Tests for validate_license_type function."""

    def test_valid_licenses(self):
        """Test valid license types."""
        assert validate_license_type("mit") == "mit"
        assert validate_license_type("MIT") == "mit"
        assert validate_license_type("apache") == "apache"
        assert validate_license_type("gpl") == "gpl"
        assert validate_license_type("none") == "none"
        assert validate_license_type("") == ""

    def test_invalid_licenses(self):
        """Test invalid license types."""
        with pytest.raises(ValidationError) as exc_info:
            validate_license_type("custom")
        assert "Invalid license type" in str(exc_info.value)


class TestValidateProjectType:
    """Tests for validate_project_type function."""

    def test_valid_project_types(self):
        """Test valid project types."""
        assert validate_project_type("library") == "library"
        assert validate_project_type("cli") == "cli"
        assert validate_project_type("script") == "script"
        assert validate_project_type("LIBRARY") == "library"

    def test_invalid_project_types(self):
        """Test invalid project types."""
        with pytest.raises(ValidationError) as exc_info:
            validate_project_type("app")
        assert "Invalid project type" in str(exc_info.value)


class TestValidateDbType:
    """Tests for validate_db_type function."""

    def test_valid_db_types(self):
        """Test valid database types."""
        assert validate_db_type("") is None
        assert validate_db_type("asyncpg") == "asyncpg"
        assert validate_db_type("sqlite") == "sqlite"
        assert validate_db_type("postgres") == "asyncpg"
        assert validate_db_type("postgresql") == "asyncpg"

    def test_invalid_db_types(self):
        """Test invalid database types."""
        with pytest.raises(ValidationError) as exc_info:
            validate_db_type("mysql")
        assert "Invalid database type" in str(exc_info.value)
