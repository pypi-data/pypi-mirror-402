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

"""Release command for Maestria."""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, List, Optional, Tuple

from rich.console import Console

from maestria.environment import activate_environment, run_in_environment
from maestria.utils.bump import bump_version
from maestria.utils.dependencies import (
    check_dependencies as check_deps_util,
)
from maestria.utils.dependencies import (
    verify_dependencies,
)
from maestria.utils.installer import install_dependencies as install_deps_util

console = Console()
logger = logging.getLogger(__name__)


def check_dependencies(
    project_dir: Path, venv_path: Optional[Path] = None, verbose: bool = False
) -> Tuple[bool, List[str]]:
    """Check if all required dependencies for release are installed.

    Args:
        project_dir: Path to the project directory
        venv_path: Optional virtual environment path (defaults to .venv)
        verbose: Whether to show verbose output

    Returns:
        Tuple[bool, List[str]]: (True if all dependencies are installed, list of missing dependencies)
    """
    try:
        # Use default .venv if not specified
        if venv_path is None:
            venv_path = Path(".venv")

        all_installed, missing_deps = check_deps_util(
            project_dir, venv_path, verbose=verbose
        )

        if verbose and not all_installed:
            console.print(
                f"[yellow]Missing dependencies: {', '.join(missing_deps)}[/yellow]"
            )

        return (all_installed, missing_deps)

    except Exception as e:
        logger.error(f"Error checking dependencies: {str(e)}")
        return (False, ["pytest", "bump2version", "build", "twine"])


def install_missing_dependencies(
    project_dir: Path,
    dependencies: List[str],
    venv_path: Optional[Path] = None,
    verbose: bool = False,
) -> bool:
    """Install missing dependencies using pip within the environment.

    Args:
        project_dir: Path to the project directory
        dependencies: List of dependencies to install
        venv_path: Optional virtual environment path (defaults to .venv)
        verbose: Whether to show detailed output

    Returns:
        bool: True if installation was successful, False otherwise
    """
    if not dependencies:
        return True

    console.print(
        f"[bold]Installing missing dependencies: {', '.join(dependencies)}[/bold]"
    )

    try:
        # Use default .venv if not specified
        if venv_path is None:
            venv_path = Path(".venv")

        success = install_deps_util(
            project_dir=project_dir,
            venv_path=venv_path,
            dependencies=dependencies,
            verbose=verbose,
        )

        if not success:
            console.print("[yellow]Some dependencies could not be installed.[/yellow]")
            return False

        all_verified, still_missing = verify_dependencies(
            project_dir, venv_path, dependencies, verbose=verbose
        )

        if not all_verified:
            console.print(
                f"[yellow]Some dependencies could not be verified: {', '.join(still_missing)}[/yellow]"
            )
            console.print(
                "[yellow]This might be due to Python's module cache. Consider restarting your session.[/yellow]"
            )
            return False

        console.print("[green]Dependencies installed successfully![/green]")
        return True

    except Exception as e:
        logger.error(f"Failed to install dependencies: {str(e)}")
        console.print(f"[red]Failed to install dependencies:[/red] {str(e)}")
        return False


def get_pypi_repo(config: Any) -> Optional[str]:
    """Get the PyPI repository from the config."""
    # The config now has a pypi_repo property that already handles environment variables
    return config.pypi_repo


def clean_build_dirs(project_dir: Path) -> None:
    """Clean build directories before release."""
    console.print("[bold]Cleaning build directories...[/bold]")

    # Directories to clean
    build_dirs = [
        project_dir / "dist",
        project_dir / "build",
    ]

    # Egg-info directories (using glob pattern)
    import glob

    egg_info_dirs = glob.glob(str(project_dir / "*.egg-info"))

    for path in build_dirs + egg_info_dirs:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    console.print("[green]Build directories cleaned![/green]")


def run_tests(
    project_dir: Path, venv_path: Optional[Path] = None, verbose: bool = False
) -> bool:
    """Run tests before release.

    Args:
        project_dir: Path to the project directory
        venv_path: Optional virtual environment path
        verbose: Whether to show verbose output (passed to underlying functions)

    Returns:
        bool: True if tests passed or user chose to continue, False otherwise
    """
    console.print("[bold]Running tests before release...[/bold]")

    try:
        # Import the run_tests function from the test module
        from maestria.commands.test import run_tests as run_project_tests

        # Create a minimal config object with all required attributes
        class MinimalConfig:
            def __init__(self, root_dir, venv_path):
                self.root_dir = root_dir
                self.venv_path = venv_path
                self.dev_dependencies = ["pytest", "pytest-cov"]
                self.scripts = {"test": "pytest"}
                self.version = "0.1.0"  # Default version
                self.pypi_repo = None  # No default PyPI repo

        config = MinimalConfig(project_dir, venv_path)

        # Set verbose flag in environment if needed
        if verbose and os.environ.get("MAESTRIA_VERBOSE") != "1":
            os.environ["MAESTRIA_VERBOSE"] = "1"

        # Run tests using the existing implementation with coverage
        run_project_tests(config, run_all=True)
        return True

    except Exception as e:
        console.print(f"[red]Tests failed. Aborting release:[/red] {str(e)}")

        if (
            not console.input("[yellow]Tests failed. Continue anyway? [y/N][/yellow] ")
            .lower()
            .startswith("y")
        ):
            return False

        return True


def run_bump_version(
    project_dir: Path,
    bump: str,
    venv_path: Optional[Path] = None,
    verbose: bool = False,
) -> Optional[str]:
    """Run the bump2version command to bump the version.

    Args:
        project_dir: Path to the project directory
        bump: The version bump type (patch, minor, major)
        venv_path: Optional virtual environment path (defaults to .venv)
        verbose: Whether to show detailed output

    Returns:
        Optional[str]: The new version if successful, None otherwise
    """
    console.print(f"[bold]Bumping {bump} version...[/bold]")

    # Use default .venv if not specified
    if venv_path is None:
        venv_path = Path(".venv")

    result = bump_version(project_dir, venv_path, bump, verbose=verbose)

    if result:
        old_version, new_version = result
        return new_version
    else:
        console.print(
            "[yellow]bump2version failed. Make sure .bumpversion.cfg exists.[/yellow]\n"
            "Example .bumpversion.cfg content:\n"
            "[bumpversion]\n"
            "current_version = 0.1.0\n"
            "commit = True\n"
            "tag = True\n\n"
            "[bumpversion:file:pyproject.toml]\n"
            'search = version = "{current_version}"\n'
            'replace = version = "{new_version}"'
        )
        return None


def release_project(
    config: Any,
    bump: str = "patch",
    install_deps: bool = False,
) -> None:
    """Release a new version of the project.

    This performs version bumping, tagging, building, and publishing to PyPI,
    following the same flow as the classic Makefile-based approach.

    Required dependencies:
        - pytest: For running tests
        - bump2version: For version bumping
        - build: For building distributions
        - twine: For publishing to PyPI

    Args:
        config: Configuration object
        bump: The version bump type (patch, minor, major)
        install_deps: Whether to automatically install missing dependencies
    """
    project_dir = Path(config.root_dir)
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    # Step 0: Activate environment first (done once at the beginning)
    try:
        # Activate environment first
        env_info = activate_environment(
            project_dir, venv_path=config.venv_path, verbose=verbose
        )
        python_path = env_info["python_path"]
    except RuntimeError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        console.print(
            "[red]Virtual environment not found. Please run 'maestria env setup' first.[/red]"
        )
        return

    # Step 1: Check for required dependencies
    all_deps_installed, missing_deps = check_dependencies(
        project_dir, venv_path=config.venv_path, verbose=verbose
    )

    if not all_deps_installed:
        deps_str = ", ".join(missing_deps)

        if install_deps:
            # Try to install missing dependencies
            if not install_missing_dependencies(
                project_dir, missing_deps, venv_path=config.venv_path, verbose=verbose
            ):
                console.print(
                    "[red]Failed to automatically install missing dependencies.[/red]\n"
                    f"Please install them manually with: python -m pip install {deps_str}"
                )
                return
        else:
            # Just inform the user about missing dependencies
            console.print(
                f"[red]Missing required dependencies: {deps_str}[/red]\n"
                f"Please install them with: python -m pip install {deps_str}\n"
                "Or run with [bold]--install-deps[/bold] flag to install them automatically."
            )
            return

    # Step 2: Get PyPI repo information
    pypi_repo = get_pypi_repo(config)
    if not pypi_repo:
        console.print(
            "[yellow]Warning: PyPI repository not configured. Using default.[/yellow]"
        )
        # Ask user if they want to continue
        repo_input = console.input(
            "[yellow]Enter PyPI repository name or press Enter to use default: [/yellow]"
        )
        if repo_input.strip():
            pypi_repo = repo_input.strip()

    # Step 3: Clean build directories
    clean_build_dirs(project_dir)

    # Step 4: Run tests
    if not run_tests(project_dir, venv_path=config.venv_path, verbose=verbose):
        return

    # Step 5: Bump version
    current_version = config.version
    console.print(f"[bold]Current version: {current_version}[/bold]")

    new_version = run_bump_version(
        project_dir, bump, venv_path=config.venv_path, verbose=verbose
    )
    if not new_version:
        console.print("[red]Failed to bump version. Aborting release.[/red]")
        return

    console.print(
        f"[green]Version bumped from {current_version} to {new_version}[/green]"
    )

    # Step 6: Push to origin main
    console.print("[bold]Pushing changes to origin main...[/bold]")
    try:
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        console.print("[green]Changes pushed to origin main![/green]")
    except subprocess.CalledProcessError as e:
        console.print(
            f"[red]Failed to push changes:[/red] {e.stderr if hasattr(e, 'stderr') else str(e)}"
        )
        if (
            not console.input("[yellow]Continue anyway? [y/N][/yellow] ")
            .lower()
            .startswith("y")
        ):
            return

    # Step 7: Build distributions
    console.print("[bold]Building distributions...[/bold]")
    try:
        # Build wheel and sdist using the activated environment's python
        run_in_environment(
            [
                str(python_path),
                "-m",
                "build",
                "--sdist",
                "--wheel",
                "--outdir",
                "dist",
                ".",
            ],
            project_dir,
            venv_path=config.venv_path,
            verbose=verbose,
            check=True,
            capture_output=not verbose,
        )
        console.print("[green]Built wheel and sdist packages successfully![/green]")

    except (
        subprocess.CalledProcessError,
        RuntimeError,
        ValueError,
        IOError,
        OSError,
    ) as e:
        console.print(f"[red]Failed to build project:[/red] {str(e)}")
        return

    # Step 8: Upload to PyPI
    if (
        console.input("[yellow]Publish to PyPI? [y/N][/yellow] ")
        .lower()
        .startswith("y")
    ):
        console.print("[bold]Publishing to PyPI...[/bold]")
        try:
            # Upload wheel and sdist
            twine_cmd = [str(python_path), "-m", "twine", "upload", "--verbose"]

            if pypi_repo:
                twine_cmd.extend(["-r", pypi_repo])

            twine_cmd.extend(
                [
                    str(project_dir / "dist" / "*.whl"),
                    str(project_dir / "dist" / "*.tar.gz"),
                ]
            )

            run_in_environment(
                twine_cmd,
                project_dir,
                venv_path=config.venv_path,
                verbose=verbose,
                check=True,
                capture_output=not verbose,
            )
            console.print("[green]Wheel and sdist published successfully![/green]")

        except (
            subprocess.CalledProcessError,
            RuntimeError,
            ValueError,
            IOError,
            OSError,
        ) as e:
            console.print(f"[red]Failed to publish project:[/red] {str(e)}")
            return

    # Step 9: Push tags
    console.print("[bold]Pushing tags to origin...[/bold]")
    try:
        subprocess.run(
            ["git", "push", "origin", "--tags"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        console.print("[green]Tags pushed to origin![/green]")
    except subprocess.CalledProcessError as e:
        console.print(
            f"[red]Failed to push tags:[/red] {e.stderr if hasattr(e, 'stderr') else str(e)}"
        )

    console.print(
        f"[bold green]Release {new_version} completed successfully![/bold green]"
    )
