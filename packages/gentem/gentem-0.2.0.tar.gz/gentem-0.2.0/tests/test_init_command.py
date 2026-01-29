"""Tests for the init command module."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from gentem.commands.init import (
    run_init,
    get_project_name,
    get_description,
    get_author,
    get_project_type,
    get_python_versions,
    get_license,
    get_add_cli,
    get_add_docker,
    get_add_docs,
    get_testing_framework,
    get_linting,
    get_ci_provider,
    get_fastapi_options,
    show_preview,
    custom_style,
)


class TestGetProjectName:
    """Tests for get_project_name function."""

    def test_valid_project_name(self):
        """Test with a valid project name."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.return_value = "myproject"
            result = get_project_name()
            assert result == "myproject"

    def test_empty_then_valid_project_name(self):
        """Test with empty input then valid project name."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.side_effect = ["", "myproject"]
            with patch("gentem.commands.init.validate_project_name") as mock_val:
                mock_val.return_value = "myproject"
                result = get_project_name()
                assert result == "myproject"

    def test_invalid_then_valid_project_name(self):
        """Test with invalid project name then valid."""
        from gentem.utils.validators import ValidationError

        with patch("gentem.commands.init.questionary") as mock_q:
            # First call returns invalid, second returns valid
            mock_q.text.return_value.ask.side_effect = ["class", "myproject", "myproject"]
            with patch("gentem.commands.init.validate_project_name") as mock_val:
                mock_val.side_effect = [ValidationError("Reserved word"), "myproject"]
                result = get_project_name()
                assert result == "myproject"


class TestGetDescription:
    """Tests for get_description function."""

    def test_get_description_with_value(self):
        """Test getting a description."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.return_value = "My awesome project"
            result = get_description()
            assert result == "My awesome project"

    def test_get_description_empty(self):
        """Test getting empty description."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.return_value = None
            result = get_description()
            assert result == ""


class TestGetAuthor:
    """Tests for get_author function."""

    def test_get_author_with_value(self):
        """Test getting an author name."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.return_value = "John Doe"
            result = get_author()
            assert result == "John Doe"

    def test_get_author_empty(self):
        """Test getting empty author."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.return_value = None
            result = get_author()
            assert result == ""


class TestGetProjectType:
    """Tests for get_project_type function."""

    def test_library_type(self):
        """Test selecting library project type."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "library"
            result = get_project_type()
            assert result == "library"

    def test_cli_type(self):
        """Test selecting CLI project type."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "cli"
            result = get_project_type()
            assert result == "cli"

    def test_fastapi_type(self):
        """Test selecting FastAPI project type."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "fastapi"
            result = get_project_type()
            assert result == "fastapi"

    def test_script_type(self):
        """Test selecting script project type."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "script"
            result = get_project_type()
            assert result == "script"


class TestGetPythonVersions:
    """Tests for get_python_versions function."""

    def test_single_version(self):
        """Test selecting single Python version."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.checkbox.return_value.ask.return_value = ["3.10"]
            result = get_python_versions()
            assert result == ["3.10"]

    def test_multiple_versions(self):
        """Test selecting multiple Python versions."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.checkbox.return_value.ask.return_value = ["3.9", "3.10", "3.11"]
            result = get_python_versions()
            assert result == ["3.9", "3.10", "3.11"]

    def test_all_versions(self):
        """Test selecting all Python versions."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.checkbox.return_value.ask.return_value = ["3.9", "3.10", "3.11", "3.12"]
            result = get_python_versions()
            assert result == ["3.9", "3.10", "3.11", "3.12"]

    def test_empty_then_default(self):
        """Test empty selection returns default."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.checkbox.return_value.ask.side_effect = [[], ["3.10"]]
            result = get_python_versions()
            assert result == ["3.10"]


class TestGetLicense:
    """Tests for get_license function."""

    def test_mit_license(self):
        """Test selecting MIT license."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "mit"
            result = get_license()
            assert result == "mit"

    def test_apache_license(self):
        """Test selecting Apache license."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "apache"
            result = get_license()
            assert result == "apache"

    def test_gpl_license(self):
        """Test selecting GPL license."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "gpl"
            result = get_license()
            assert result == "gpl"

    def test_none_license(self):
        """Test selecting no license."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "none"
            result = get_license()
            assert result == "none"


class TestGetAddCli:
    """Tests for get_add_cli function."""

    def test_add_cli_true(self):
        """Test confirming CLI support."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = True
            result = get_add_cli()
            assert result is True

    def test_add_cli_false(self):
        """Test declining CLI support."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = False
            result = get_add_cli()
            assert result is False


class TestGetAddDocker:
    """Tests for get_add_docker function."""

    def test_add_docker_true(self):
        """Test confirming Docker support."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = True
            result = get_add_docker()
            assert result is True

    def test_add_docker_false(self):
        """Test declining Docker support."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = False
            result = get_add_docker()
            assert result is False


class TestGetAddDocs:
    """Tests for get_add_docs function."""

    def test_add_docs_true(self):
        """Test confirming documentation support."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = True
            result = get_add_docs()
            assert result is True

    def test_add_docs_false(self):
        """Test declining documentation support."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = False
            result = get_add_docs()
            assert result is False


class TestGetTestingFramework:
    """Tests for get_testing_framework function."""

    def test_pytest_framework(self):
        """Test selecting pytest framework."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "pytest"
            result = get_testing_framework()
            assert result == "pytest"

    def test_unittest_framework(self):
        """Test selecting unittest framework."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "unittest"
            result = get_testing_framework()
            assert result == "unittest"

    def test_no_testing(self):
        """Test selecting no testing framework."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "none"
            result = get_testing_framework()
            assert result == "none"


class TestGetLinting:
    """Tests for get_linting function."""

    def test_ruff_black(self):
        """Test selecting Ruff + Black."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "ruff-black"
            result = get_linting()
            assert result == "ruff-black"

    def test_flake8_black(self):
        """Test selecting Flake8 + Black."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "flake8-black"
            result = get_linting()
            assert result == "flake8-black"

    def test_ruff_only(self):
        """Test selecting Ruff only."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "ruff"
            result = get_linting()
            assert result == "ruff"

    def test_no_linting(self):
        """Test selecting no linting."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "none"
            result = get_linting()
            assert result == "none"


class TestGetCiProvider:
    """Tests for get_ci_provider function."""

    def test_github_actions(self):
        """Test selecting GitHub Actions."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "github"
            result = get_ci_provider()
            assert result == "github"

    def test_gitlab_ci(self):
        """Test selecting GitLab CI."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "gitlab"
            result = get_ci_provider()
            assert result == "gitlab"

    def test_no_ci(self):
        """Test selecting no CI/CD."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "none"
            result = get_ci_provider()
            assert result == "none"


class TestGetFastapiOptions:
    """Tests for get_fastapi_options function."""

    def test_fastapi_options_default(self):
        """Test FastAPI options with defaults."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = True
            mock_q.select.return_value.ask.return_value = ""
            result = get_fastapi_options()
            assert result == {"async_mode": True, "db_type": ""}

    def test_fastapi_options_with_db(self):
        """Test FastAPI options with database."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = True
            mock_q.select.return_value.ask.return_value = "asyncpg"
            result = get_fastapi_options()
            assert result == {"async_mode": True, "db_type": "asyncpg"}

    def test_fastapi_options_no_async(self):
        """Test FastAPI options without async mode."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = False
            mock_q.select.return_value.ask.return_value = "sqlite"
            result = get_fastapi_options()
            assert result == {"async_mode": False, "db_type": "sqlite"}


class TestShowPreview:
    """Tests for show_preview function."""

    def test_show_preview_confirm(self):
        """Test preview with confirmation."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = True
            result = show_preview(
                project_name="myproject",
                project_type="library",
                description="My project",
                author="John Doe",
                license_type="mit",
                python_versions=["3.10", "3.11"],
                add_cli=True,
                add_docker=False,
                add_docs=True,
                testing_framework="pytest",
                linting="ruff-black",
                ci_provider="github",
            )
            assert result is True

    def test_show_preview_cancel(self):
        """Test preview with cancellation."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = False
            result = show_preview(
                project_name="myproject",
                project_type="library",
                description="",
                author="",
                license_type="mit",
                python_versions=["3.10"],
                add_cli=False,
                add_docker=False,
                add_docs=False,
                testing_framework="pytest",
                linting="ruff",
                ci_provider="none",
            )
            assert result is False


class TestRunInit:
    """Tests for run_init function."""

    def test_run_init_minimal_preset_library(self):
        """Test run_init with minimal preset for library."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.side_effect = [
                "myproject",  # project_name
                "",  # description
                "",  # author
            ]
            mock_q.select.return_value.ask.side_effect = [
                "mit",  # license
            ]
            mock_q.confirm.return_value.ask.return_value = True

            with patch("gentem.commands.init.create_new_project") as mock_create:
                run_init(skip_prompts=False, preset="minimal")
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["project_name"] == "myproject"
                assert call_kwargs["project_type"] == "library"

    def test_run_init_cli_tool_preset(self):
        """Test run_init with cli-tool preset."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.side_effect = [
                "mycli",
                "My CLI tool",
                "John Doe",
            ]
            mock_q.select.return_value.ask.side_effect = [
                "mit",  # license
            ]
            mock_q.confirm.return_value.ask.return_value = True

            with patch("gentem.commands.init.create_new_project") as mock_create:
                run_init(skip_prompts=False, preset="cli-tool")
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["project_type"] == "cli"

    def test_run_init_fastapi_preset(self):
        """Test run_init with fastapi preset."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.side_effect = [
                "myapi",
                "My FastAPI API",
                "John Doe",
            ]
            mock_q.select.return_value.ask.side_effect = [
                "mit",  # license
                True,  # async mode
                "asyncpg",  # db type
            ]
            mock_q.confirm.return_value.ask.return_value = True

            # create_fastapi_project is imported inside the function
            with patch("gentem.commands.fastapi.create_fastapi_project") as mock_create:
                run_init(skip_prompts=False, preset="fastapi")
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["project_name"] == "myapi"

    def test_run_init_unknown_preset(self):
        """Test run_init with unknown preset."""
        with patch("gentem.commands.init.print") as mock_print:
            run_init(preset="unknown")
            mock_print.assert_called()
            # Check that an error message was printed
            assert any("Unknown preset" in str(call) for call in mock_print.call_args_list)

    def test_run_init_dry_run_library(self):
        """Test run_init with dry_run option for library."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.side_effect = [
                "myproject",
                "",
                "",
            ]
            mock_q.select.return_value.ask.side_effect = [
                "mit",
            ]
            mock_q.confirm.return_value.ask.return_value = True

            with patch("gentem.commands.init.create_new_project") as mock_create:
                run_init(skip_prompts=True, preset="minimal", dry_run=True)
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["dry_run"] is True

    def test_run_init_verbose(self):
        """Test run_init with verbose output."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.side_effect = [
                "myproject",
                "",
                "",
            ]
            mock_q.select.return_value.ask.side_effect = [
                "mit",
            ]
            mock_q.confirm.return_value.ask.return_value = True

            with patch("gentem.commands.init.create_new_project") as mock_create:
                with patch("gentem.commands.init.print") as mock_print:
                    run_init(skip_prompts=True, preset="minimal", verbose=True)
                    mock_create.assert_called_once()
                    # Check that verbose prints were made
                    assert any("Creating project" in str(call) for call in mock_print.call_args_list)

    def test_run_init_cancelled(self):
        """Test run_init when user cancels."""
        with patch("gentem.commands.init.questionary") as mock_q:
            mock_q.text.return_value.ask.side_effect = [
                "myproject",
                "",
                "",
            ]
            mock_q.select.return_value.ask.side_effect = [
                "mit",  # license
                "library",  # project type
                "pytest",  # testing framework
                "ruff-black",  # linting
                "none",  # CI provider
            ]
            mock_q.checkbox.return_value.ask.return_value = ["3.10"]
            mock_q.confirm.return_value.ask.side_effect = [
                False,  # project creation cancelled
            ]
            # Additional prompts for non-script projects
            mock_q.confirm.return_value.ask.side_effect = [
                False,  # CLI support
                False,  # Docker support
                False,  # docs support
                False,  # project creation cancelled
            ]

            with patch("gentem.commands.init.create_new_project") as mock_create:
                with patch("gentem.commands.init.print") as mock_print:
                    run_init(skip_prompts=False, verbose=False)
                    mock_create.assert_not_called()
                    # Check that cancellation message was printed
                    assert any("cancelled" in str(call).lower() for call in mock_print.call_args_list)


class TestCustomStyle:
    """Tests for custom_style."""

    def test_custom_style_exists(self):
        """Test that custom_style is defined."""
        assert custom_style is not None
        # Style is a prompt_toolkit Style object
        from prompt_toolkit.styles import Style as PromptStyle
        assert isinstance(custom_style, PromptStyle)
