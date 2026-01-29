"""Interactive wizard for creating projects with guided prompts."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import questionary
from questionary import Style
from rich import print
from rich.panel import Panel

from gentem.commands.new import create_new_project
from gentem.utils.validators import (
    ValidationError,
    validate_license_type,
    validate_project_name,
)


# Custom questionary style
custom_style = Style([
    ("qmark", "fg:#673AB7 bold"),
    ("answer", "fg:#2196F3 bold"),
    ("pointer", "fg:#673AB7 bold"),
    ("highlighted", "fg:#673AB7 bold"),
    ("selected", "fg:#4CAF50 bold"),
    ("separator", "fg:#6B6B6B"),
    ("instruction", "fg:#9E9E9E"),
    ("text", "fg:#FFFFFF"),
])


def get_project_name() -> str:
    """Prompt for project name."""
    while True:
        name = questionary.text(
            "Project name:",
            style=custom_style,
            validate=lambda x: bool(x.strip()) or "Project name cannot be empty"
        ).ask()
        
        if name:
            try:
                validate_project_name(name)
                return name
            except ValidationError as e:
                print(f"[red]Error: {e}[/]")


def get_description() -> str:
    """Prompt for project description."""
    return questionary.text(
        "Description (optional):",
        style=custom_style,
    ).ask() or ""


def get_author() -> str:
    """Prompt for author name."""
    return questionary.text(
        "Author name (optional):",
        style=custom_style,
    ).ask() or ""


def get_project_type() -> str:
    """Prompt for project type."""
    return questionary.select(
        "Project type:",
        choices=[
            {"name": "Library", "value": "library"},
            {"name": "CLI Tool", "value": "cli"},
            {"name": "REST API (FastAPI)", "value": "fastapi"},
            {"name": "Script", "value": "script"},
        ],
        style=custom_style,
    ).ask()


def get_python_versions() -> list[str]:
    """Prompt for Python versions."""
    versions = questionary.checkbox(
        "Python versions to support:",
        choices=[
            {"name": "3.9", "value": "3.9", "checked": True},
            {"name": "3.10", "value": "3.10", "checked": True},
            {"name": "3.11", "value": "3.11", "checked": True},
            {"name": "3.12", "value": "3.12", "checked": False},
        ],
        style=custom_style,
        validate=lambda x: len(x) >= 1 or "Select at least one Python version"
    ).ask()
    
    return versions or ["3.10"]


def get_license() -> str:
    """Prompt for license type."""
    return questionary.select(
        "License:",
        choices=[
            {"name": "MIT", "value": "mit"},
            {"name": "Apache 2.0", "value": "apache"},
            {"name": "GPL v3", "value": "gpl"},
            {"name": "BSD 3-Clause", "value": "bsd"},
            {"name": "None", "value": "none"},
        ],
        style=custom_style,
    ).ask()


def get_add_cli() -> bool:
    """Prompt for CLI support."""
    return questionary.confirm(
        "Add CLI support?",
        style=custom_style,
        default=False
    ).ask()


def get_add_docker() -> bool:
    """Prompt for Docker support."""
    return questionary.confirm(
        "Add Docker support?",
        style=custom_style,
        default=False
    ).ask()


def get_add_docs() -> bool:
    """Prompt for documentation support."""
    return questionary.confirm(
        "Add documentation (MkDocs)?",
        style=custom_style,
        default=False
    ).ask()


def get_testing_framework() -> str:
    """Prompt for testing framework."""
    return questionary.select(
        "Testing framework:",
        choices=[
            {"name": "pytest", "value": "pytest"},
            {"name": "unittest", "value": "unittest"},
            {"name": "None", "value": "none"},
        ],
        style=custom_style,
    ).ask()


def get_linting() -> str:
    """Prompt for linting/formatting tools."""
    return questionary.select(
        "Linting/Formatting:",
        choices=[
            {"name": "Ruff + Black", "value": "ruff-black"},
            {"name": "Flake8 + Black", "value": "flake8-black"},
            {"name": "Ruff only", "value": "ruff"},
            {"name": "None", "value": "none"},
        ],
        style=custom_style,
    ).ask()


def get_ci_provider() -> str:
    """Prompt for CI/CD provider."""
    return questionary.select(
        "CI/CD provider:",
        choices=[
            {"name": "GitHub Actions", "value": "github"},
            {"name": "GitLab CI", "value": "gitlab"},
            {"name": "None", "value": "none"},
        ],
        style=custom_style,
    ).ask()


def get_fastapi_options() -> dict:
    """Prompt for FastAPI-specific options."""
    async_mode = questionary.confirm(
        "Use async mode with lifespan?",
        style=custom_style,
        default=True
    ).ask()
    
    db_type = questionary.select(
        "Database support:",
        choices=[
            {"name": "None", "value": ""},
            {"name": "AsyncPG (PostgreSQL)", "value": "asyncpg"},
            {"name": "SQLite", "value": "sqlite"},
        ],
        style=custom_style,
    ).ask()
    
    return {
        "async_mode": async_mode,
        "db_type": db_type or "",
    }


def show_preview(
    project_name: str,
    project_type: str,
    description: str,
    author: str,
    license_type: str,
    python_versions: list[str],
    add_cli: bool,
    add_docker: bool,
    add_docs: bool,
    testing_framework: str,
    linting: str,
    ci_provider: str,
    fastapi_options: Optional[dict] = None,
) -> bool:
    """Show a preview of the project configuration and ask for confirmation."""
    print("\n")
    
    preview_lines = [
        f"[bold]Project Name:[/] {project_name}",
        f"[bold]Type:[/] {project_type}",
    ]
    
    if description:
        preview_lines.append(f"[bold]Description:[/] {description}")
    
    preview_lines.extend([
        f"[bold]Author:[/] {author or 'Not specified'}",
        f"[bold]License:[/] {license_type.upper()}",
        f"[bold]Python Versions:[/] {', '.join(python_versions)}",
        f"[bold]CLI Support:[/] {'Yes' if add_cli else 'No'}",
        f"[bold]Docker Support:[/] {'Yes' if add_docker else 'No'}",
        f"[bold]Documentation:[/] {'Yes' if add_docs else 'No'}",
        f"[bold]Testing:[/] {testing_framework}",
        f"[bold]Linting:[/] {linting}",
        f"[bold]CI/CD:[/] {ci_provider}",
    ])
    
    if project_type == "fastapi" and fastapi_options:
        preview_lines.extend([
            f"[bold]Async Mode:[/] {'Yes' if fastapi_options.get('async_mode') else 'No'}",
            f"[bold]Database:[/] {fastapi_options.get('db_type') or 'None'}",
        ])
    
    preview_text = "\n".join(preview_lines)
    
    print(Panel(
        f"[bold cyan]Project Configuration[/]\n\n{preview_text}",
        title="Gentem",
        expand=False,
    ))
    
    return questionary.confirm(
        "\nCreate this project?",
        style=custom_style,
        default=True
    ).ask()


def run_init(
    skip_prompts: bool = False,
    preset: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Run the interactive project creation wizard.
    
    Args:
        skip_prompts: Skip prompts and use defaults.
        preset: Use a preset configuration.
        dry_run: Preview without creating files.
        verbose: Show verbose output.
    """
    print("\n")
    print(Panel(
        "[bold cyan]Welcome to Gentem![/]\n"
        "Let's create a new Python project together.",
        title="Gentem",
        expand=False,
        border_style="cyan",
    ))
    print("\n")
    
    if preset:
        # Apply preset
        if preset == "minimal":
            project_type = "library"
            add_cli = False
            add_docker = False
            add_docs = False
            testing_framework = "pytest"
            linting = "ruff"
            ci_provider = "none"
            python_versions = ["3.10", "3.11"]
        elif preset == "cli-tool":
            project_type = "cli"
            add_cli = True
            add_docker = False
            add_docs = False
            testing_framework = "pytest"
            linting = "ruff-black"
            ci_provider = "github"
            python_versions = ["3.10", "3.11", "3.12"]
        elif preset == "fastapi":
            project_type = "fastapi"
            add_cli = False
            add_docker = True
            add_docs = True
            testing_framework = "pytest"
            linting = "ruff-black"
            ci_provider = "github"
            python_versions = ["3.10", "3.11", "3.12"]
        else:
            print(f"[red]Unknown preset: {preset}[/]")
            return
        
        # Get required info
        project_name = get_project_name()
        description = get_description()
        author = get_author()
        license_type = get_license()
        
        if project_type == "fastapi":
            fastapi_options = get_fastapi_options()
        else:
            fastapi_options = None
        
        if not skip_prompts:
            should_create = show_preview(
                project_name=project_name,
                project_type=project_type,
                description=description,
                author=author,
                license_type=license_type,
                python_versions=python_versions,
                add_cli=add_cli,
                add_docker=add_docker,
                add_docs=add_docs,
                testing_framework=testing_framework,
                linting=linting,
                ci_provider=ci_provider,
                fastapi_options=fastapi_options,
            )
            if not should_create:
                print("[yellow]Project creation cancelled.[/]")
                return
    else:
        # Interactive mode
        project_name = get_project_name()
        description = get_description()
        author = get_author()
        project_type = get_project_type()
        python_versions = get_python_versions()
        license_type = get_license()
        
        # FastAPI-specific options
        if project_type == "fastapi":
            fastapi_options = get_fastapi_options()
        else:
            fastapi_options = None
        
        # Additional options
        if project_type != "script":
            add_cli = get_add_cli()
            add_docker = get_add_docker()
            add_docs = get_add_docs()
        else:
            add_cli = False
            add_docker = False
            add_docs = False
        
        testing_framework = get_testing_framework()
        linting = get_linting()
        ci_provider = get_ci_provider()
        
        # Show preview
        if not skip_prompts:
            should_create = show_preview(
                project_name=project_name,
                project_type=project_type,
                description=description,
                author=author,
                license_type=license_type,
                python_versions=python_versions,
                add_cli=add_cli,
                add_docker=add_docker,
                add_docs=add_docs,
                testing_framework=testing_framework,
                linting=linting,
                ci_provider=ci_provider,
                fastapi_options=fastapi_options,
            )
            if not should_create:
                print("[yellow]Project creation cancelled.[/]")
                return
    
    # Create the project
    if project_type == "fastapi":
        # Use fastapi command
        from gentem.commands.fastapi import create_fastapi_project
        
        if verbose:
            print(f"Creating FastAPI project: {project_name}")
            print(f"Async mode: {fastapi_options.get('async_mode', False)}")
            print(f"Database type: {fastapi_options.get('db_type', '')}")
        
        create_fastapi_project(
            project_name=project_name,
            async_mode=fastapi_options.get("async_mode", False) if fastapi_options else False,
            db_type=fastapi_options.get("db_type", "") if fastapi_options else "",
            author=author,
            description=description,
            dry_run=dry_run,
            verbose=verbose,
        )
    else:
        # Use new command
        if verbose:
            print(f"Creating project: {project_name}")
            print(f"Project type: {project_type}")
        
        create_new_project(
            project_name=project_name,
            project_type=project_type,
            author=author,
            description=description,
            license_type=license_type,
            dry_run=dry_run,
            verbose=verbose,
        )
    
    # Note: Additional features (Docker, docs, CI/CD) would be added here
    # as part of the gentem add command implementation
    if add_docker or add_docs or ci_provider != "none":
        print("\n[yellow]Note: Additional features (Docker, docs, CI/CD) will be available via 'gentem add' command.[/]")
