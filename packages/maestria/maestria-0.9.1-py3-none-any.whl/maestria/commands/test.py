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

"""Test command for Maestria."""

import os
import subprocess
from typing import Any, List, Optional

from rich.console import Console

from maestria.environment import activate_environment, run_in_environment

console = Console()


def run_tests(
    config: Any,
    run_all: bool = False,
    pytest_args: Optional[List[str]] = None,
) -> None:
    """Run tests.

    This runs pytest directly through the virtual environment.
    All pytest_args are passed directly to pytest.

    Args:
        config: Configuration object
        run_all: Whether to run all tests with coverage
        pytest_args: List of arguments to pass to pytest (e.g., ["-v", "-s", "tests/"])
    """
    project_dir = config.root_dir
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    # Activate the virtual environment
    try:
        env_info = activate_environment(
            project_dir, venv_path=config.venv_path, verbose=verbose
        )
        python_path = env_info["python_path"]
    except RuntimeError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return

    # Check if pytest is actually installed in the venv
    try:
        subprocess.run(
            [str(python_path), "-c", "import pytest"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        pytest_installed = True
    except subprocess.CalledProcessError:
        pytest_installed = False

    # If pytest is not installed, check config and install if needed
    if not pytest_installed:
        if not _is_pytest_configured(config):
            console.print(
                "[yellow]Warning: pytest not configured in pyproject.toml[/yellow]"
            )
            console.print("Adding pytest configuration...")
        else:
            console.print(
                "[yellow]Warning: pytest is configured but not installed[/yellow]"
            )
            console.print("Installing pytest...")
        _configure_pytest(config)

    # Determine the command to run
    if run_all:
        cmd = [
            str(python_path),
            "-m",
            "pytest",
            "--cov",
            "--cov-report=term",
            "--cov-report=html",
        ]
    else:
        cmd = [str(python_path), "-m", "pytest"]

    # Add pytest arguments if provided
    if pytest_args:
        cmd.extend(pytest_args)

    # Run the tests
    console.print(f"[bold]Running tests: {' '.join(str(c) for c in cmd)}[/bold]")
    try:
        result = run_in_environment(
            cmd,
            project_dir,
            venv_path=config.venv_path,
            verbose=verbose,
            check=False,  # Don't raise an exception if tests fail
            capture_output=False,  # Show output directly
        )

        if result.returncode == 0:
            console.print("[green]Tests passed![/green]")
        else:
            console.print(f"[red]Tests failed with exit code {result.returncode}[/red]")
    except Exception as e:
        console.print(f"[red]Error running tests: {str(e)}[/red]")
        console.print(
            "Make sure you have run 'maestria env setup' to set up your environment."
        )


def _is_pytest_configured(config: Any) -> bool:
    """Check if pytest is configured in pyproject.toml.

    Args:
        config: Configuration object

    Returns:
        Whether pytest is configured
    """
    # Check if pytest is in dev dependencies
    dev_deps = config.dev_dependencies
    if any(dep.startswith("pytest") for dep in dev_deps):
        return True

    # Check if there's a test script
    scripts = config.scripts
    if "test" in scripts:
        return True

    return False


def _configure_pytest(config: Any) -> None:
    """Configure pytest in pyproject.toml.

    Args:
        config: Configuration object
    """
    project_dir = config.root_dir
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    # Install pytest and pytest-cov in the virtual environment using uv
    try:
        # Use uv pip install instead of python -m pip install
        # This works even if pip isn't installed in the venv
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(config.venv_path),
                "pytest",
                "pytest-cov",
            ],
            cwd=project_dir,
            check=True,
            capture_output=not verbose,
            text=True,
        )

        console.print(
            "[green]Installed pytest and pytest-cov in the virtual environment[/green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to install pytest and pytest-cov:[/red] {str(e)}")
        return
    except FileNotFoundError:
        console.print("[red]UV not found. Please install uv first.[/red]")
        return
    except Exception as e:
        console.print(f"[red]Failed to install pytest and pytest-cov:[/red] {str(e)}")
        return

    # Add the dependencies to pyproject.toml directly
    try:
        import tomli
        import tomli_w

        pyproject_path = project_dir / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)

        # Add pytest to dev dependencies
        if "project" not in pyproject_data:
            pyproject_data["project"] = {}
        if "optional-dependencies" not in pyproject_data["project"]:
            pyproject_data["project"]["optional-dependencies"] = {}
        if "dev" not in pyproject_data["project"]["optional-dependencies"]:
            pyproject_data["project"]["optional-dependencies"]["dev"] = []

        # Add the dependencies if not already present
        dev_deps = pyproject_data["project"]["optional-dependencies"]["dev"]
        for pkg in ["pytest", "pytest-cov"]:
            if not any(dep.startswith(pkg) for dep in dev_deps):
                dev_deps.append(pkg)

        # Add test script to maestria scripts
        if "tool" not in pyproject_data:
            pyproject_data["tool"] = {}
        if "maestria" not in pyproject_data["tool"]:
            pyproject_data["tool"]["maestria"] = {}
        if "scripts" not in pyproject_data["tool"]["maestria"]:
            pyproject_data["tool"]["maestria"]["scripts"] = {}

        pyproject_data["tool"]["maestria"]["scripts"]["test"] = "pytest"

        # Write the updated content back
        with open(pyproject_path, "wb") as f:
            tomli_w.dump(pyproject_data, f)

        console.print("[green]Updated pyproject.toml with pytest configuration[/green]")

    except Exception as e:
        console.print(
            f"[red]Failed to update pyproject.toml with pytest "
            f"configuration:[/red] {str(e)}"
        )
        return
