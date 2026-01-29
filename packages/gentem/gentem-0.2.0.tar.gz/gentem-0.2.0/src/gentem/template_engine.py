"""Template engine for Gentem using Jinja2."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import (
    BaseLoader,
    Environment,
    FileSystemLoader,
    TemplateSyntaxError,
    UndefinedError,
)
from rich import print
from rich.panel import Panel
from rich.tree import Tree


class TemplateEngine:
    """Jinja2 template engine for generating project files."""

    def __init__(self, template_dir: Optional[str] = None) -> None:
        """Initialize the template engine.

        Args:
            template_dir: Base directory for templates. If not provided,
                         uses the gentem templates directory.
        """
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # Find the package directory
            package_dir = Path(__file__).parent.parent
            self.template_dir = package_dir / "templates"

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def get_template(self, template_path: str) -> "jinja2.Template":
        """Get a template by path.

        Args:
            template_path: Path to the template relative to template_dir.

        Returns:
            The Jinja2 template.

        Raises:
            FileNotFoundError: If template not found.
        """
        try:
            return self.env.get_template(template_path)
        except TemplateSyntaxError as e:
            raise TemplateSyntaxError(
                f"Syntax error in template {template_path}: {e.message}",
                lineno=e.lineno,
            ) from e
        except UndefinedError as e:
            raise UndefinedError(
                f"Undefined variable in template {template_path}: {e.message}"
            ) from e

    def render_template(
        self,
        template_path: str,
        context: Dict[str, Any],
    ) -> str:
        """Render a template with the given context.

        Args:
            template_path: Path to the template relative to template_dir.
            context: Variables to pass to the template.

        Returns:
            The rendered template content.
        """
        template = self.get_template(template_path)
        return template.render(**context)

    def render_file(
        self,
        template_path: str,
        context: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """Render a template to a file.

        Args:
            template_path: Path to the template relative to template_dir.
            context: Variables to pass to the template.
            output_path: Path to write the rendered file.
        """
        content = self.render_template(template_path, context)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        output_path.write_text(content, encoding="utf-8")

    def list_templates(self, subdir: Optional[str] = None) -> list[str]:
        """List all templates in a subdirectory.

        Args:
            subdir: Subdirectory within template_dir to list.

        Returns:
            List of template paths.
        """
        search_dir = self.template_dir
        if subdir:
            search_dir = search_dir / subdir

        if not search_dir.exists():
            return []

        templates = []
        for root, _, files in os.walk(search_dir):
            for file in files:
                if file.endswith((".j2", ".jinja2")):
                    rel_path = Path(root).relative_to(self.template_dir)
                    templates.append(str(rel_path / file))

        return sorted(templates)

    def preview_tree(
        self,
        template_paths: list[str],
        context: Dict[str, Any],
    ) -> Tree:
        """Preview the file tree that would be generated.

        Args:
            template_paths: List of template paths to render.
            context: Variables to pass to the templates.

        Returns:
            A Rich Tree showing the file structure.
        """
        tree = Tree("Project Structure", guide_style="bold.cyan")

        for template_path in template_paths:
            # Get the output path (remove .j2 extension)
            output_path = template_path
            if output_path.endswith((".j2", ".jinja2")):
                output_path = output_path[:-3]  # Remove .j2

            # Render the path with context
            try:
                rendered_path = self.render_template(
                    f"_paths/{output_path}.path.j2", context
                )
            except Exception:
                # Fallback to template path
                rendered_path = output_path

            # Add to tree
            parts = Path(rendered_path).parts
            current = tree
            for i, part in enumerate(parts):
                is_last = i == len(parts) - 1
                if is_last:
                    current.add(f"[cyan]{part}[/]")
                else:
                    # Find or create branch
                    found = False
                    for child in current.children:
                        if child.label and str(child.label).strip("[]") == part:
                            current = child
                            found = True
                            break
                    if not found:
                        current = current.add(f"[bold]{part}/[/]")

        return tree


# Global template engine instance
_engine: Optional[TemplateEngine] = None


def get_template_engine() -> TemplateEngine:
    """Get the global template engine instance."""
    global _engine
    if _engine is None:
        _engine = TemplateEngine()
    return _engine
