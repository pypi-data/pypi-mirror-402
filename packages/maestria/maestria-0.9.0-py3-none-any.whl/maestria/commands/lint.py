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

"""Lint command for Maestria."""

import os
import platform
import tempfile
from pathlib import Path
from typing import Any

from rich.console import Console

from maestria.environment import activate_environment, run_in_environment
from maestria.security import SecurityError, validate_executable, validate_path

console = Console()


def run_linting(
    config: Any,
    check: bool = False,
) -> None:
    """Run linting on the project.

    This runs black, mypy, and other linting tools through the virtual environment.

    Args:
        config: Configuration object
        check: Whether to check code style without making changes
    """
    project_dir = config.root_dir
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    # Check if linting tools are configured
    if not _is_linting_configured(config):
        console.print(
            "[yellow]Warning: linting tools not configured in pyproject.toml[/yellow]"
        )
        console.print("Adding linting configuration...")
        _configure_linting(config)

    # Activate the environment
    try:
        activate_environment(project_dir, venv_path=config.venv_path, verbose=verbose)
    except RuntimeError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return

    # Run black
    console.print("[bold]Running black...[/bold]")
    try:
        cmd = ["black"]
        if check:
            cmd.append("--check")
        cmd.append(".")

        result = run_in_environment(
            cmd,
            project_dir,
            venv_path=config.venv_path,
            verbose=verbose,
            check=False,  # Don't raise an exception if linting fails
            capture_output=False,  # Show output directly
        )

        if result.returncode == 0:
            console.print("[green]Black formatting completed successfully[/green]")
        else:
            console.print("[yellow]Black found formatting issues[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Warning: black failed: {str(e)}[/yellow]")

    # Run mypy
    console.print("[bold]Running mypy...[/bold]")
    try:
        # Determine if we should check src or project root
        src_dir = Path(project_dir) / "src"
        dirs_to_check = ["src", "tests"] if src_dir.exists() else ["."]

        cmd = ["mypy"] + dirs_to_check

        result = run_in_environment(
            cmd,
            project_dir,
            venv_path=config.venv_path,
            verbose=verbose,
            check=False,  # Don't raise an exception if linting fails
            capture_output=False,  # Show output directly
        )

        if result.returncode == 0:
            console.print("[green]Mypy type checking completed successfully[/green]")
        else:
            console.print("[yellow]Mypy found type issues[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Warning: mypy failed: {str(e)}[/yellow]")

    # Run ruff if available
    console.print("[bold]Running ruff...[/bold]")
    try:
        cmd = ["ruff", "check", "."]

        result = run_in_environment(
            cmd,
            project_dir,
            venv_path=config.venv_path,
            verbose=verbose,
            check=False,  # Don't raise an exception if linting fails
            capture_output=False,  # Show output directly
        )

        if result.returncode == 0:
            console.print("[green]Ruff linting completed successfully[/green]")
        else:
            console.print("[yellow]Ruff found linting issues[/yellow]")
    except Exception:
        console.print("[dim]Ruff not found or failed, skipping[/dim]")


def _is_linting_configured(config: Any) -> bool:
    """Check if linting tools are configured in pyproject.toml.

    Args:
        config: Configuration object

    Returns:
        Whether linting tools are configured
    """
    # Check if linting tools are in dev dependencies
    dev_deps = config.dev_dependencies
    if (
        any(dep.startswith("black") for dep in dev_deps)
        or any(dep.startswith("mypy") for dep in dev_deps)
        or any(dep.startswith("ruff") for dep in dev_deps)
    ):
        return True

    # Check if there's a lint script
    scripts = config.scripts
    if "lint" in scripts:
        return True

    return False


def _configure_linting(config: Any) -> None:
    """Configure linting tools in pyproject.toml.

    Args:
        config: Configuration object
    """
    project_dir = config.root_dir
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    # Activate the environment
    try:
        env_info = activate_environment(
            project_dir, venv_path=config.venv_path, verbose=verbose
        )
        python_path = env_info["python_path"]
    except RuntimeError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return

    # Validate python_path before using it
    try:
        is_windows = platform.system() == "Windows"
        venv_bin_path = Path(config.venv_path) / ("Scripts" if is_windows else "bin")
        python_path = validate_executable(python_path, allowed_dirs=[venv_bin_path])
    except SecurityError as e:
        console.print(f"[red]Security validation failed for Python: {e}[/red]")
        return

    # Install linting tools in the virtual environment
    try:
        console.print("[bold]Installing linting tools...[/bold]")

        # Use our common run_in_environment helper to run pip
        run_in_environment(
            [str(python_path), "-m", "pip", "install", "black", "mypy", "ruff"],
            project_dir,
            venv_path=config.venv_path,
            verbose=verbose,
            check=True,
            capture_output=not verbose,
        )

        console.print(
            "[green]Installed black, mypy, and ruff in the virtual environment[/green]"
        )
    except Exception as e:
        console.print(f"[red]Failed to install linting tools:[/red] {str(e)}")
        return

    # Update pyproject.toml with a Python script
    update_script = """
import tomli
import tomli_w
import os
import sys

project_dir = os.getcwd()
pyproject_path = os.path.join(project_dir, "pyproject.toml")

with open(pyproject_path, "rb") as f:
    pyproject_data = tomli.load(f)

# Add linting tools to dev dependencies
if "project" not in pyproject_data:
    pyproject_data["project"] = {}
if "optional-dependencies" not in pyproject_data["project"]:
    pyproject_data["project"]["optional-dependencies"] = {}
if "dev" not in pyproject_data["project"]["optional-dependencies"]:
    pyproject_data["project"]["optional-dependencies"]["dev"] = []

# Add the dependencies if not already present
dev_deps = pyproject_data["project"]["optional-dependencies"]["dev"]
for pkg in ["black", "mypy", "ruff"]:
    if not any(dep.startswith(pkg) for dep in dev_deps):
        dev_deps.append(pkg)

# Add lint script to maestria scripts
if "tool" not in pyproject_data:
    pyproject_data["tool"] = {}
if "maestria" not in pyproject_data["tool"]:
    pyproject_data["tool"]["maestria"] = {}
if "scripts" not in pyproject_data["tool"]["maestria"]:
    pyproject_data["tool"]["maestria"]["scripts"] = {}

pyproject_data["tool"]["maestria"]["scripts"]["lint"] = "black . && mypy . && ruff check ."

# Configure black
if "black" not in pyproject_data["tool"]:
    pyproject_data["tool"]["black"] = {}
pyproject_data["tool"]["black"]["line-length"] = 88

# Configure mypy
if "mypy" not in pyproject_data["tool"]:
    pyproject_data["tool"]["mypy"] = {}
pyproject_data["tool"]["mypy"]["python_version"] = "3.10"
pyproject_data["tool"]["mypy"]["warn_return_any"] = True
pyproject_data["tool"]["mypy"]["disallow_untyped_defs"] = True

# Write the updated content back
with open(pyproject_path, "wb") as f:
    tomli_w.dump(pyproject_data, f)
    
print("Updated pyproject.toml successfully")
sys.exit(0)
"""

    try:
        # Write the script to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write(update_script)
            script_path = f.name

        try:
            # Validate script_path
            try:
                script_path_obj = validate_path(
                    script_path, allow_absolute=True, must_exist=True
                )
                script_path = str(script_path_obj)
            except SecurityError as e:
                console.print(
                    f"[red]Security validation failed for script path: {e}[/red]"
                )
                return

            # Run the script in the environment
            run_in_environment(
                [str(python_path), script_path],
                project_dir,
                venv_path=config.venv_path,
                verbose=verbose,
                check=True,
                capture_output=not verbose,
            )

            console.print(
                "[green]Updated pyproject.toml with linting configuration[/green]"
            )
        finally:
            # Clean up the temporary file
            os.unlink(script_path)

    except Exception as e:
        console.print(
            f"[red]Failed to update pyproject.toml with linting configuration:[/red] {str(e)}"
        )
        return
