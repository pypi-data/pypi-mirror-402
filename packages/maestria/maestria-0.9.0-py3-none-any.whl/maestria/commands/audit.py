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

"""Audit command for Maestria."""

import os
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

from maestria.environment import activate_environment, run_in_environment

console = Console()


def run_audit(
    config: Any,
    code_only: bool = False,
    deps_only: bool = False,
) -> None:
    """Run security audit on the project.

    This runs pip-audit for dependency vulnerabilities and bandit for code security issues.

    Args:
        config: Configuration object
        code_only: Only run code security scan (bandit)
        deps_only: Only run dependency vulnerability scan (pip-audit)
    """
    project_dir = config.root_dir
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    try:
        activate_environment(project_dir, venv_path=config.venv_path, verbose=verbose)
    except RuntimeError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return

    has_error = False

    if not code_only:
        has_error = _run_pip_audit(project_dir, config.venv_path, verbose) or has_error

    if not deps_only:
        has_error = _run_bandit(project_dir, config.venv_path, verbose) or has_error

    if not has_error:
        console.print(
            "\n[green bold]Security audit completed successfully![/green bold]"
        )


def _run_pip_audit(project_dir: Path, venv_path: Optional[Path], verbose: bool) -> bool:
    """Run pip-audit for dependency vulnerabilities.

    Args:
        project_dir: Project directory
        venv_path: Optional virtual environment path
        verbose: Verbose output

    Returns:
        True if errors were found, False otherwise
    """
    console.print("[bold]Running pip-audit (dependency vulnerabilities)...[/bold]")
    try:
        result = run_in_environment(
            ["pip-audit"],
            project_dir,
            venv_path=venv_path,
            verbose=verbose,
            check=False,
            capture_output=False,
        )

        if result.returncode == 0:
            console.print(
                "[green]No known vulnerabilities found in dependencies[/green]"
            )
            return False
        else:
            console.print("[yellow]Vulnerabilities found in dependencies[/yellow]")
            return True
    except Exception as e:
        console.print(f"[yellow]Warning: pip-audit failed: {str(e)}[/yellow]")
        console.print("[dim]Tip: Install pip-audit with: maestria env setup[/dim]")
        return False


def _run_bandit(project_dir: Path, venv_path: Optional[Path], verbose: bool) -> bool:
    """Run bandit for code security issues.

    Args:
        project_dir: Project directory
        venv_path: Optional virtual environment path
        verbose: Verbose output

    Returns:
        True if errors were found, False otherwise
    """
    console.print("[bold]Running bandit (code security scan)...[/bold]")
    try:
        src_dir = Path(project_dir) / "src"
        dirs_to_check = ["src"] if src_dir.exists() else ["."]

        cmd = ["bandit", "-r"] + dirs_to_check + ["-ll"]

        result = run_in_environment(
            cmd,
            project_dir,
            venv_path=venv_path,
            verbose=verbose,
            check=False,
            capture_output=False,
        )

        if result.returncode == 0:
            console.print("[green]No security issues found in code[/green]")
            return False
        else:
            console.print("[yellow]Security issues found in code[/yellow]")
            return True
    except Exception:
        console.print("[dim]Bandit not found or failed, skipping[/dim]")
        console.print("[dim]Tip: Install bandit with: maestria env setup[/dim]")
        return False
