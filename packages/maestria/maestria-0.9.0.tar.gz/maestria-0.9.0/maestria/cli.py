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

"""CLI entry point for Maestria."""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console

from maestria import __version__
from maestria.config import load_config
from maestria.context import MaestriaContext
from maestria.plugins import get_plugin_commands, run_hook

console = Console()


def ensure_uv_installed() -> bool:
    """Ensure UV is installed globally.

    Returns:
        True if UV is available, False otherwise
    """
    try:
        subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except FileNotFoundError:
        console.print("[yellow]UV not found. Attempting to install UV...[/yellow]")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "uv"],
                check=True,
                capture_output=True,
                text=True,
            )
            console.print("[green]Successfully installed UV![/green]")
            return True
        except Exception:
            console.print("[red]Failed to install UV.[/red]")
            console.print("Maestria requires UV (Ultraviolet) to function properly.")
            console.print(
                "Please install UV using: [bold]pip install uv[/bold] or visit: https://github.com/astral-sh/uv"
            )
            return False
    except subprocess.CalledProcessError:
        return True  # UV exists but --version failed, assume it's usable


def print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Print the version and exit."""
    if not value or ctx.resilient_parsing:
        return
    console.print(f"[bold]Maestria[/bold] version [bold blue]{__version__}[/bold blue]")
    ctx.exit()


@click.group(invoke_without_command=True)
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Print version information and exit.",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Enable verbose output with detailed logs."
)
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Project directory (defaults to current directory).",
)
@click.option(
    "--venv-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Virtual environment path (defaults to .venv in project directory).",
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: bool = False,
    project_dir: Optional[Path] = None,
    venv_path: Optional[Path] = None,
) -> None:
    """Maestria: A thin, modern Python project management tool."""
    # Ensure UV is installed before proceeding
    # Skip check for --version and --help
    if ctx.invoked_subcommand is not None:
        if not ensure_uv_installed():
            ctx.exit(1)

    # Create and store MaestriaContext
    ctx.ensure_object(MaestriaContext)
    ctx.obj = MaestriaContext(
        project_dir=project_dir or Path.cwd(), venv_path=venv_path, verbose=verbose
    )

    if "VIRTUAL_ENV" in os.environ:
        del os.environ["VIRTUAL_ENV"]
    if "CONDA_DEFAULT_ENV" in os.environ:
        del os.environ["CONDA_DEFAULT_ENV"]

    # Set up environment variable for commands that run in subprocesses
    if verbose:
        os.environ["MAESTRIA_VERBOSE"] = "1"
        console.print("[dim]Verbose mode enabled[/dim]")
        console.print(f"[dim]Project directory: {ctx.obj.project_dir}[/dim]")
        console.print(f"[dim]Virtual environment: {ctx.obj.venv_path}[/dim]")

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("name")
@click.option(
    "--template",
    default="basic",
    help="Template to use for the new project. Can be a built-in template or a team template configured in pyproject.toml.",
)
@click.option(
    "--python", default="3.10", help="Python version to use for the new project."
)
def init(name: str, template: str, python: str) -> None:
    """Initialize a new Python project.

    This creates a new Python project using Maestria's template system.
    """
    from maestria.commands.init import initialize_project

    initialize_project(name, template, python)


@cli.group()
def env() -> None:
    """Manage the Python environment."""
    pass


@env.command(name="setup")
@click.pass_context
def env_setup(ctx: click.Context) -> None:
    """Set up the development environment.

    This creates a virtual environment using uv and installs dependencies.
    """
    from maestria.commands.env import setup_environment

    qpy_ctx: MaestriaContext = ctx.obj
    config = load_config(qpy_ctx.project_dir, venv_path=qpy_ctx.venv_path)
    setup_environment(config)


@env.command(name="update")
@click.pass_context
def env_update(ctx: click.Context) -> None:
    """Update the development environment.

    This updates dependencies in the virtual environment.
    """
    from maestria.commands.env import update_environment

    qpy_ctx: MaestriaContext = ctx.obj
    config = load_config(qpy_ctx.project_dir, venv_path=qpy_ctx.venv_path)
    update_environment(config)


@env.command(name="info")
@click.pass_context
def env_info(ctx: click.Context) -> None:
    """Show information about the current environment.

    Use the global --verbose flag to show all installed packages:
        maestria --verbose env info
    """
    from maestria.commands.env import show_environment_info

    qpy_ctx: MaestriaContext = ctx.obj
    config = load_config(qpy_ctx.project_dir, venv_path=qpy_ctx.venv_path)
    show_environment_info(config)


@cli.command()
@click.argument("script")
@click.argument("args", nargs=-1)
@click.pass_context
def run(ctx: click.Context, script: str, args: Optional[List[str]] = None) -> None:
    """Run a script defined in pyproject.toml.

    This executes scripts defined in the pyproject.toml configuration.
    """
    from maestria.commands.run import run_script

    qpy_ctx: MaestriaContext = ctx.obj
    config = load_config(qpy_ctx.project_dir, venv_path=qpy_ctx.venv_path)
    run_script(config, script, args or [])


@cli.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.option("--all", "run_all", is_flag=True, help="Run all tests with coverage.")
@click.argument("pytest_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def test(ctx: click.Context, run_all: bool, pytest_args: tuple) -> None:
    """Run tests.

    This runs pytest directly through the configured virtual environment.
    All arguments after 'test' are passed directly to pytest.

    Examples:
        maestria test                    # Run all tests
        maestria test --all              # Run with coverage
        maestria test -v -s              # Run with pytest -v -s flags
        maestria test tests/test_foo.py  # Run specific test file
        maestria test -k test_name       # Run tests matching pattern
    """
    from maestria.commands.test import run_tests

    qpy_ctx: MaestriaContext = ctx.obj
    config = load_config(qpy_ctx.project_dir, venv_path=qpy_ctx.venv_path)
    run_tests(config, run_all=run_all, pytest_args=list(pytest_args))


@cli.command()
@click.option("--check", is_flag=True, help="Check code style without making changes.")
@click.pass_context
def lint(ctx: click.Context, check: bool) -> None:
    """Lint and format code.

    This runs linting tools through the configured virtual environment.
    """
    from maestria.commands.lint import run_linting

    qpy_ctx: MaestriaContext = ctx.obj
    config = load_config(qpy_ctx.project_dir, venv_path=qpy_ctx.venv_path)
    run_linting(config, check=check)


@cli.command()
@click.option("--code-only", is_flag=True, help="Only run code security scan (bandit).")
@click.option(
    "--deps-only",
    is_flag=True,
    help="Only run dependency vulnerability scan (pip-audit).",
)
@click.pass_context
def audit(ctx: click.Context, code_only: bool, deps_only: bool) -> None:
    """Run security audit on the project.

    This runs pip-audit for dependency vulnerabilities and bandit for code security issues.
    """
    from maestria.commands.audit import run_audit

    qpy_ctx: MaestriaContext = ctx.obj
    config = load_config(qpy_ctx.project_dir, venv_path=qpy_ctx.venv_path)
    run_audit(config, code_only=code_only, deps_only=deps_only)


@cli.command()
@click.pass_context
def build(ctx: click.Context) -> None:
    """Build the project.

    This builds the project using Python's build module.
    """
    from maestria.commands.build import build_project

    qpy_ctx: MaestriaContext = ctx.obj
    config = load_config(qpy_ctx.project_dir, venv_path=qpy_ctx.venv_path)
    build_project(config)


@cli.command()
@click.option(
    "--prod-only",
    is_flag=True,
    default=False,
    help="Install only production dependencies (excludes dev dependencies).",
)
@click.option("--update", is_flag=True, default=False, help="Update existing packages.")
@click.option(
    "--no-editable",
    is_flag=True,
    default=False,
    help="Skip editable installation of the current package (rarely needed).",
)
@click.pass_context
def install(
    ctx: click.Context,
    prod_only: bool = False,
    update: bool = False,
    no_editable: bool = False,
) -> None:
    """Install dependencies.

    This installs dependencies from pyproject.toml in the virtual environment.
    By default, installs ALL dependencies (production + development) in editable mode.

    This default is ideal for development workflows where you need testing tools,
    linters, and build utilities.

    Use --prod-only to install only production dependencies.
    Use --update to upgrade existing packages to their latest versions.
    Use --no-editable to skip editable mode (rarely needed for development).
    """
    from maestria.commands.install import install_dependencies

    qpy_ctx: MaestriaContext = ctx.obj
    config = load_config(qpy_ctx.project_dir, venv_path=qpy_ctx.venv_path)
    install_dependencies(
        config, dev=not prod_only, update=update, editable=not no_editable
    )


@cli.command()
@click.option(
    "--bump",
    type=click.Choice(["patch", "minor", "major"]),
    default="patch",
    help="Version bump type.",
)
@click.option(
    "--install-deps",
    is_flag=True,
    default=False,
    help="Automatically install missing dependencies.",
)
@click.pass_context
def release(ctx: click.Context, bump: str, install_deps: bool = False) -> None:
    """Release a new version.

    This performs version bumping, tagging, and publishing.

    The release process requires several dependencies:
    - pytest: For running tests
    - bump2version: For version bumping
    - build: For building distribution packages
    - twine: For uploading packages to PyPI

    Use the --install-deps flag to automatically install missing dependencies.
    """
    from maestria.commands.release import release_project

    qpy_ctx: MaestriaContext = ctx.obj
    config = load_config(qpy_ctx.project_dir, venv_path=qpy_ctx.venv_path)
    release_project(config, bump=bump, install_deps=install_deps)


def register_plugin_commands() -> None:
    """Register commands from plugins."""
    plugin_commands = get_plugin_commands()

    for cmd_name, cmd_func in plugin_commands.items():
        if isinstance(cmd_func, click.Command):
            # If it's already a Click command, add it directly
            cli.add_command(cmd_func, name=cmd_name)
        else:
            # If it's a function, create a Click command from it
            cmd = click.command(name=cmd_name)(cmd_func)
            cli.add_command(cmd, name=cmd_name)


def main() -> int:
    """Run the CLI."""
    try:
        # Register plugin commands
        register_plugin_commands()

        # Run pre-command hooks
        run_hook("pre_command")

        # Run the CLI
        cli()

        # Run post-command hooks
        run_hook("post_command")

        return 0
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
