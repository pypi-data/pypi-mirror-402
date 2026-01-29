# Copyright 2024-2025 eBay Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Template system for project initialization."""

import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import git
from rich.console import Console

from maestria.config import MaestriaTemplateConfig
from maestria.security import validate_path, is_safe_filename, SecurityError

console = Console()
logger = logging.getLogger("maestria.templates")


def get_available_templates(config: Any) -> Dict[str, MaestriaTemplateConfig]:
    """Get a dictionary of available templates.

    Args:
        config: Configuration object with template registry

    Returns:
        Dictionary of template name to template configuration
    """
    return config.maestria.template_registry


def get_template_path(template_name: str, config: Any) -> Optional[Path]:
    """Get the path to a template directory.

    For local templates, returns the actual path.
    For remote templates, clones the repository and returns the path to the cloned directory.

    Args:
        template_name: Name of the template
        config: Configuration object with template registry

    Returns:
        Path to the template directory or None if not found
    """
    # Get template configuration
    templates = get_available_templates(config)

    if template_name in templates:
        template_info = templates[template_name]
        template_type = template_info.type

        # Handle local template
        if template_type == "local":
            template_path = template_info.path
            if template_path:
                try:
                    # If path is absolute, validate it
                    if os.path.isabs(template_path):
                        path = validate_path(
                            template_path, allow_absolute=True, must_exist=True
                        )
                        return path

                    # Otherwise, check in the package directory
                    package_dir = Path(__file__).parent / "data"
                    path = validate_path(
                        template_path, base_dir=package_dir, must_exist=True
                    )
                    return path
                except SecurityError as e:
                    console.print(f"[red]Security error in template path: {e}[/red]")
                    return None

        # Handle git repository template
        elif template_type == "git":
            repo_url = template_info.repo_url
            repo_ref = template_info.ref or "main"
            template_dir = template_info.directory or ""

            if repo_url:
                # Create a temporary directory to clone the repository
                tmp_dir = tempfile.mkdtemp(prefix="maestria_template_")

                try:
                    # Clone the repository
                    console.print(f"Cloning template from [bold]{repo_url}[/bold]...")

                    # Use GitPython for more control
                    repo = git.Repo.clone_from(
                        repo_url, tmp_dir, branch=repo_ref, depth=1
                    )

                    # Get the path to the template directory
                    if template_dir:
                        template_path = Path(tmp_dir) / template_dir
                    else:
                        template_path = Path(tmp_dir)

                    if template_path.exists():
                        return template_path
                    else:
                        console.print(
                            f"[red]Template directory not found in repository: {template_dir}[/red]"
                        )
                        shutil.rmtree(tmp_dir)
                except git.GitCommandError as e:
                    console.print(f"[red]Failed to clone repository: {e}[/red]")
                    shutil.rmtree(tmp_dir)
                except Exception as e:
                    console.print(
                        f"[red]Failed to get template from repository: {e}[/red]"
                    )
                    shutil.rmtree(tmp_dir)

    # Check built-in templates as a fallback
    built_in_path = Path(__file__).parent / "data" / template_name
    if built_in_path.exists():
        return built_in_path

    return None


def cleanup_template_path(template_path: Path) -> None:
    """Clean up a template path if it's a temporary directory.

    Args:
        template_path: Path to the template directory
    """
    if template_path and str(template_path).startswith(tempfile.gettempdir()):
        try:
            shutil.rmtree(template_path)
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to clean up template directory: {e}[/yellow]"
            )


def process_template_files(directory: Path, context: Dict[str, str]) -> None:
    """Process template files and directories for variable substitution.

    Args:
        directory: Directory containing template files
        context: Dictionary of template variables
    """
    # File extensions to process
    text_extensions = [
        ".py",
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".json",
        ".toml",
        ".ini",
        ".cfg",
        ".html",
        ".css",
        ".js",
    ]
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    if verbose:
        console.print("[dim]Template context variables:[/dim]")
        for key, value in context.items():
            console.print(f"[dim]  {key} = {value}[/dim]")

    # First, handle directory name replacements
    package_name = context.get("package_name", "")
    project_slug = context.get("project_slug", "")
    plugin_name_short = context.get("plugin_name_short", "")

    if verbose:
        console.print(f"[dim]Processing template files in directory: {directory}[/dim]")
        console.print(f"[dim]Package name: {package_name}[/dim]")
        console.print(f"[dim]Project slug: {project_slug}[/dim]")

    if package_name:
        # Rename directories with template variables in their names
        for root, dirs, files in list(os.walk(directory, topdown=False)):
            for dir_name in dirs:
                if (
                    "{{package_name}}" in dir_name
                    or "{{plugin_name_short}}" in dir_name
                    or "{{project_slug}}" in dir_name
                ):
                    old_path = Path(root) / dir_name

                    # Replace template variables in directory name
                    new_name = dir_name.replace("{{package_name}}", package_name)
                    new_name = new_name.replace("{{project_slug}}", project_slug)
                    new_name = new_name.replace(
                        "{{plugin_name_short}}", plugin_name_short
                    )
                    new_path = Path(root) / new_name

                    if verbose:
                        console.print(
                            f"[dim]Found template directory: {old_path}[/dim]"
                        )
                        console.print(f"[dim]Will rename to: {new_path}[/dim]")

                    # Rename the directory with security validation
                    try:
                        if not is_safe_filename(new_name):
                            console.print(
                                f"[yellow]Warning: Unsafe directory name skipped: {new_name}[/yellow]"
                            )
                            continue

                        validated_new_path = validate_path(
                            new_path, base_dir=directory, allow_absolute=True
                        )

                        # First check if the target directory already exists
                        if not validated_new_path.exists():
                            os.rename(old_path, validated_new_path)
                            console.print(
                                f"Renamed directory: {old_path} -> {validated_new_path}"
                            )
                        elif verbose:
                            console.print(
                                f"[dim]Target directory already exists: {validated_new_path}[/dim]"
                            )
                    except SecurityError as e:
                        console.print(
                            f"[yellow]Security warning: Could not rename directory {old_path}: {e}[/yellow]"
                        )
                    except Exception as e:
                        console.print(
                            f"[yellow]Warning: Could not rename directory {old_path}: {e}[/yellow]"
                        )

    # Process file contents for variable replacement
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file

            # Check if file is a text file
            if file_path.suffix in text_extensions:
                try:
                    # Read file content
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Replace template variables
                    new_content = content
                    replacements_made = False

                    for key, value in context.items():
                        template_var = "{{" + key + "}}"
                        if template_var in new_content:
                            if verbose:
                                console.print(
                                    f"[dim]Replacing '{template_var}' with '{value}' in {file_path}[/dim]"
                                )
                            new_content = new_content.replace(template_var, value)
                            replacements_made = True

                    # Write updated content
                    if replacements_made:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                            if verbose:
                                console.print(
                                    f"[dim]Updated file with replacements: {file_path}[/dim]"
                                )
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not process template file {file_path}: {e}[/yellow]"
                    )


def apply_template(
    template_name: str, output_dir: Path, config: Any, context: Dict[str, str]
) -> bool:
    """Apply a template to create a new project.

    This applies Maestria's template system to create a new project
    with the appropriate structure and configuration.

    Args:
        template_name: Name of the template to use
        output_dir: Directory where the project will be created
        config: Configuration object with template registry
        context: Dictionary of template variables

    Returns:
        True if successful, False otherwise
    """
    template_path = get_template_path(template_name, config)

    if not template_path:
        console.print(f"[red]Template {template_name} not found.[/red]")
        templates = get_available_templates(config)
        if templates:
            console.print(f"Available templates: {', '.join(templates.keys())}")
        return False

    try:
        # Validate output_dir to prevent path traversal
        try:
            validated_output_dir = validate_path(
                output_dir, allow_absolute=True, must_exist=False
            )
        except SecurityError as e:
            console.print(f"[red]Security error in output directory: {e}[/red]")
            return False

        # Create project directory if it doesn't exist
        # Use project_dir from context which preserves original name with hyphens
        project_dir_name = context.get(
            "project_dir", context.get("project_slug", "project")
        )

        if not is_safe_filename(project_dir_name):
            console.print(
                f"[red]Invalid project directory name: {project_dir_name}[/red]"
            )
            return False

        project_dir = validated_output_dir / project_dir_name

        try:
            project_dir = validate_path(
                project_dir, base_dir=validated_output_dir, allow_absolute=True
            )
        except SecurityError as e:
            console.print(f"[red]Security error in project directory: {e}[/red]")
            return False

        if not project_dir.exists():
            project_dir.mkdir(parents=True, exist_ok=True)

        # Get src_layout setting (default to False for flat layout)
        src_layout = False
        if hasattr(config, "maestria") and hasattr(config.maestria, "src_layout"):
            src_layout = config.maestria.src_layout

        # Copy template files with appropriate structure
        for item in template_path.iterdir():
            # Special handling for src directory based on layout preference
            if item.name == "src" and not src_layout:
                # For flat layout, copy contents of src/project_slug directly to project root
                src_pkg_dir = item / context.get("project_slug", "project")
                if src_pkg_dir.exists() and src_pkg_dir.is_dir():
                    # Copy from src/project_slug/* to project/*
                    for sub_item in src_pkg_dir.iterdir():
                        if sub_item.is_dir():
                            shutil.copytree(
                                sub_item,
                                project_dir / sub_item.name,
                                dirs_exist_ok=True,
                            )
                        else:
                            shutil.copy2(sub_item, project_dir / sub_item.name)
                else:
                    # Copy from src/* to project/*
                    for sub_item in item.iterdir():
                        if sub_item.is_dir():
                            shutil.copytree(
                                sub_item,
                                project_dir / sub_item.name,
                                dirs_exist_ok=True,
                            )
                        else:
                            shutil.copy2(sub_item, project_dir / sub_item.name)
            elif item.is_dir():
                shutil.copytree(item, project_dir / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, project_dir / item.name)

        # Process template files
        process_template_files(project_dir, context)

        # Create a basic virtual environment for the project
        try:
            subprocess.run(
                ["uv", "venv", ".venv"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print("[green]Created virtual environment[/green]")
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not create virtual environment: {e}[/yellow]"
            )

        # Update pyproject.toml to reflect layout preference if needed
        if not src_layout:
            try:
                # Use regular Python to update pyproject.toml
                update_script = """
import tomli
import tomli_w

try:
    with open('pyproject.toml', 'rb') as f:
        doc = tomli.load(f)
except Exception:
    doc = {}
    
if 'tool' not in doc:
    doc['tool'] = {}
if 'maestria' not in doc['tool']:
    doc['tool']['maestria'] = {}
    
doc['tool']['maestria']['src_layout'] = False

with open('pyproject.toml', 'wb') as f:
    tomli_w.dump(doc, f)
"""
                # Write a temporary script
                script_path = project_dir / "update_config.py"
                with open(script_path, "w") as f:
                    f.write(update_script)

                # Run the script
                subprocess.run(
                    ["python", "update_config.py"],
                    cwd=project_dir,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # Clean up the script
                os.remove(script_path)
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not update pyproject.toml with layout setting: {e}[/yellow]"
                )

        # Cleanup template path if it was a temporary clone
        cleanup_template_path(template_path)

        return True
    except Exception as e:
        console.print(f"[red]Failed to create project from template:[/red] {e}")
        # Cleanup template path if it was a temporary clone
        cleanup_template_path(template_path)
        return False
