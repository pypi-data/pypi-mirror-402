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

"""Initialize a new Python project."""

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.prompt import Confirm, Prompt

from maestria.security import SecurityError, sanitize_user_input, validate_path
from maestria.templates import apply_template, get_available_templates

console = Console()

# Set up logger
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("maestria")


def run_command(
    cmd: Union[List[str], str], cwd: Optional[Path] = None, **kwargs: Any
) -> subprocess.CompletedProcess:
    """Run a command with verbose logging if enabled.

    Args:
        cmd: Command to run (list or string)
        cwd: Working directory
        **kwargs: Additional arguments for subprocess.run

    Returns:
        CompletedProcess instance with command results
    """
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    if cwd is not None:
        try:
            cwd = validate_path(cwd, allow_absolute=True, must_exist=True)
        except SecurityError as e:
            raise ValueError(f"Invalid working directory: {e}") from e

    if verbose:
        if isinstance(cmd, list):
            cmd_str = " ".join(str(c) for c in cmd)
        else:
            cmd_str = cmd
        console.print(f"[dim]Running command: {cmd_str}[/dim]")

    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, **kwargs)

    if verbose:
        if result.stdout and result.stdout.strip():
            console.print(f"[dim]Command output:\n{result.stdout.strip()}[/dim]")
        if result.stderr and result.stderr.strip():
            console.print(f"[dim]Command error output:\n{result.stderr.strip()}[/dim]")

    return result


def init_git_repo(project_dir: Path, repo_url: Optional[str] = None) -> bool:
    """Initialize a git repository for the project.

    Args:
        project_dir: Path to project directory
        repo_url: Optional remote repository URL

    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize git repository
        run_command(["git", "init"], cwd=project_dir, check=True)
        console.print("[green]Initialized git repository[/green]")

        # Create .gitignore if it doesn't exist
        gitignore_path = project_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, "w") as f:
                f.write("""# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""")
            console.print("[green]Created .gitignore file[/green]")

        # Add all files
        run_command(["git", "add", "."], cwd=project_dir, check=True)

        # Initial commit
        run_command(
            ["git", "commit", "-m", "Initial commit with Maestria"],
            cwd=project_dir,
            check=True,
        )
        console.print("[green]Created initial commit[/green]")

        # Add remote if provided
        if repo_url:
            run_command(
                ["git", "remote", "add", "origin", repo_url],
                cwd=project_dir,
                check=True,
            )
            console.print(f"[green]Added remote repository: {repo_url}[/green]")

            # Set branch to main
            run_command(["git", "branch", "-M", "main"], cwd=project_dir, check=True)

        return True
    except subprocess.CalledProcessError as e:
        console.print(
            f"[yellow]Warning: Error initializing git repository: {e}[/yellow]"
        )
        logger.debug(f"Git init error: {e.stdout}\n{e.stderr}")
        return False
    except Exception as e:
        console.print(
            f"[yellow]Warning: Could not initialize git repository: {e}[/yellow]"
        )
        logger.debug(f"Git init exception: {str(e)}")
        return False


def gather_project_info(name: str) -> Dict[str, str]:
    """Gather project information from user.

    Args:
        name: Default project name

    Returns:
        Dictionary with project information
    """
    console.print("[bold blue]Project Information[/bold blue]")

    # Get git config info for defaults
    author_name = "Your Name"
    author_email = ""  # Will be populated from git config or user prompt
    try:
        git_name = run_command(
            ["git", "config", "user.name"], check=True
        ).stdout.strip()
        git_email = run_command(
            ["git", "config", "user.email"], check=True
        ).stdout.strip()
        # Use git config if available
        if git_name:
            author_name = git_name
        if git_email:
            author_email = git_email
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Use safe hardcoded defaults - no environment variables
        pass

    # Prompt for project information
    project_description = Prompt.ask(
        "Project description", default="A Python project created with Maestria"
    )

    author_name = Prompt.ask("Author name", default=author_name)
    author_email = Prompt.ask("Author email", default=author_email)

    # Sanitize author inputs to prevent path traversal
    try:
        author_name = sanitize_user_input(author_name, "Author name")
        author_email = sanitize_user_input(author_email, "Author email")
    except SecurityError as e:
        console.print(f"[red]Invalid input: {e}[/red]")
        return {}

    # Determine Python package name (remove -py suffix if present)
    default_package_name = name.lower()
    if default_package_name.endswith("-py"):
        default_package_name = default_package_name[:-3]
    default_package_name = default_package_name.replace("-", "_").replace(" ", "_")

    package_name = Prompt.ask(
        "Python package name (must be valid Python identifier)",
        default=default_package_name,
    )

    # Git repository setup
    use_git = Confirm.ask("Initialize git repository?", default=True)
    repo_url = None

    if use_git:
        add_remote = Confirm.ask("Connect to remote git repository?", default=False)
        if add_remote:
            console.print(
                "[bold]Note:[/bold] Make sure you've already created an empty repository on your Git hosting service (GitHub, GitLab, etc.)."
            )
            repo_url = Prompt.ask("Git repository URL", default="")

    return {
        "project_description": project_description,
        "author_name": author_name,
        "author_email": author_email,
        "package_name": package_name,
        "use_git": use_git,
        "repo_url": repo_url if repo_url else None,
    }


def initialize_project(name: str, template: str, python_version: str) -> None:
    """Initialize a new Python project.

    This creates a new Python project using Maestria's template system
    for the initial files and proper Python packaging configuration.

    Args:
        name: Name of the project
        template: Template to use
        python_version: Python version to use
    """
    from maestria.config import load_config

    # Create the project directory
    output_dir = Path.cwd()
    project_dir = output_dir / name

    if project_dir.exists():
        console.print(f"[yellow]Directory already exists: {project_dir}[/yellow]")
        if not console.input("Do you want to continue? [y/N] ").lower().startswith("y"):
            return

    console.print(
        f"Creating project [bold]{name}[/bold] using template [bold]{template}[/bold]..."
    )

    # Load configuration
    config = load_config()

    # Get project information from user
    project_info = gather_project_info(name)

    # Extract git-related info
    use_git = project_info.pop("use_git")
    repo_url = project_info.pop("repo_url")

    # Get package name from user input or fallback to default
    package_name = project_info.pop(
        "package_name", name.lower().replace(" ", "_").replace("-", "_")
    )
    project_slug = package_name

    # For plugin template, add plugin-specific context variables
    if template == "plugin_template":
        plugin_name_short = (
            name.lower()
            .replace("maestria-", "")
            .replace("maestria_", "")
            .replace("-plugin", "")
            .replace("_plugin", "")
        )
        plugin_name_short = plugin_name_short.replace("-", "_")

        # Prepare context for the plugin template
        context = {
            "project_name": name,
            "project_slug": project_slug,
            "project_dir": name,
            **project_info,
            "python_version": python_version,
            "version": "0.1.0",
            "plugin_name": name,
            "plugin_name_short": plugin_name_short,
            "package_name": package_name,
        }
    else:
        # Standard context for other templates
        context = {
            "project_name": name,
            "project_slug": project_slug,
            "project_dir": name,
            **project_info,
            "python_version": python_version,
            "version": "0.1.0",
            "package_name": package_name,
        }

    # Apply the template
    success = apply_template(template, output_dir, config, context)

    if success:
        # Initialize git repository if requested
        if use_git:
            git_success = init_git_repo(project_dir, repo_url)

            if git_success and repo_url:
                # Add push instructions
                console.print("\n[bold]To push to the remote repository:[/bold]")
                console.print(f"  cd {name}")
                console.print("  git push -u origin main")

        console.print(f"[green]Project created successfully at {project_dir}[/green]")
        console.print("\n[bold blue]Next Steps:[/bold blue]")
        console.print(f"1. cd {name}")
        console.print("2. maestria env setup")

        # If using git with remote but haven't pushed yet
        if use_git and repo_url:
            console.print("3. git push -u origin main")
    else:
        available_templates = get_available_templates(config)
        if available_templates:
            console.print(
                f"Available templates: {', '.join(available_templates.keys())}"
            )
        else:
            console.print("[red]No templates available.[/red]")
            console.print(
                "Please add templates to the [tool.maestria.template_registry] section in pyproject.toml."
            )
