"""Main CLI entry point for Gentem."""

import typer

from gentem import __version__

# Explicitly configure typer for better Windows support
app = typer.Typer(
    name="gentem",
    help="A Python CLI template boilerplate generator",
    add_completion=False,
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print the version of gentem."""
    if value:
        print(f"Gentem version: {__version__}")
        raise typer.Exit(0)


@app.callback(invoke_without_command=True)
def callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show the version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """A Python CLI template boilerplate generator."""
    pass


@app.command("new")
def new_command(
    project_name: str = typer.Argument(
        ...,
        help="Name of the project to create.",
    ),
    project_type: str = typer.Option(
        "library",
        "--type",
        "-t",
        help="Project type: library, cli, or script.",
    ),
    author: str = typer.Option(
        "",
        "--author",
        "-a",
        help="Author name for the project.",
    ),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Description for the project.",
    ),
    license_type: str = typer.Option(
        "mit",
        "--license",
        "-l",
        help="License type: mit, apache, gpl, or none.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the project structure without creating files.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output.",
    ),
) -> None:
    """Create a new Python project."""
    from gentem.commands.new import create_new_project

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


@app.command("fastapi")
def fastapi_command(
    project_name: str = typer.Argument(
        ...,
        help="Name of the FastAPI project to create.",
    ),
    async_mode: bool = typer.Option(
        False,
        "--async",
        "-A",
        help="Use async mode with lifespan.",
    ),
    db_type: str = typer.Option(
        "",
        "--db",
        "-D",
        help="Database type: asyncpg (for async SQLAlchemy).",
    ),
    author: str = typer.Option(
        "",
        "--author",
        "-a",
        help="Author name for the project.",
    ),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Description for the project.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the project structure without creating files.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output.",
    ),
) -> None:
    """Create a new FastAPI project with opinionated structure."""
    from gentem.commands.fastapi import create_fastapi_project

    if verbose:
        print(f"Creating FastAPI project: {project_name}")
        print(f"Async mode: {async_mode}")
        print(f"Database type: {db_type or 'none'}")

    create_fastapi_project(
        project_name=project_name,
        async_mode=async_mode,
        db_type=db_type,
        author=author,
        description=description,
        dry_run=dry_run,
        verbose=verbose,
    )


@app.command("init")
def init_command(
    skip_prompts: bool = typer.Option(
        False,
        "--skip-prompts",
        "-s",
        help="Skip prompts and use default values.",
    ),
    preset: str = typer.Option(
        "",
        "--preset",
        "-p",
        help="Preset to use: minimal, cli-tool, fastapi.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the project structure without creating files.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output.",
    ),
) -> None:
    """Interactive wizard for creating new projects."""
    from gentem.commands.init import run_init

    if verbose:
        print("Starting interactive project wizard")
        print(f"Skip prompts: {skip_prompts}")
        print(f"Preset: {preset or 'none'}")

    run_init(
        skip_prompts=skip_prompts,
        preset=preset or None,
        dry_run=dry_run,
        verbose=verbose,
    )

def main():
    app()


if __name__ == "__main__":
    main()
