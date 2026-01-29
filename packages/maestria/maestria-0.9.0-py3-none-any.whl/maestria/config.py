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

"""Configuration management for Maestria."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import pydantic
import tomli
from rich.console import Console

console = Console()


class MaestriaTemplateConfig(pydantic.BaseModel):
    """Template configuration."""

    type: str = "local"
    path: Optional[str] = None
    repo_url: Optional[str] = None
    ref: str = "main"
    directory: Optional[str] = None


class TeamConstants(pydantic.BaseModel):
    """Team-specific constants."""

    pypi_repo: Optional[str] = None
    docker_hub_account: Optional[str] = None


class MaestriaConfig(pydantic.BaseModel):
    """Maestria-specific configuration."""

    template_registry: Dict[str, MaestriaTemplateConfig] = {}
    hooks: Dict[str, List[str]] = {"pre_command": [], "post_command": []}
    src_layout: bool = False  # Default to flat layout
    constants: TeamConstants = TeamConstants()


class MaestriaProjectConfig:
    """Maestria project configuration loaded from pyproject.toml."""

    def __init__(self, path: Optional[Path] = None, venv_path: Optional[Path] = None):
        self.path = path
        self.data = {}
        self.maestria = MaestriaConfig()

        # Set venv_path - if not provided, default to .venv in root_dir
        self._venv_path = venv_path

        if path and path.exists():
            try:
                with open(path, "rb") as f:
                    self.data = tomli.load(f)

                # Load Maestria-specific configuration
                maestria_config = self.data.get("tool", {}).get("maestria", {})
                if maestria_config:
                    # Convert template registry entries to model objects
                    template_registry = {}
                    for name, config in maestria_config.get(
                        "template_registry", {}
                    ).items():
                        template_registry[name] = MaestriaTemplateConfig(**config)

                    hooks = maestria_config.get("hooks", {})

                    # Load team constants from config
                    constants_data = maestria_config.get("constants", {})
                    constants = TeamConstants(**constants_data)

                    # Also check environment variables (they override config file)
                    if "PYPI_REPO" in os.environ:
                        constants.pypi_repo = os.environ["PYPI_REPO"]
                    if "DOCKER_HUB_ACCOUNT" in os.environ:
                        constants.docker_hub_account = os.environ["DOCKER_HUB_ACCOUNT"]

                    self.maestria = MaestriaConfig(
                        template_registry=template_registry,
                        hooks=hooks,
                        constants=constants,
                    )
            except Exception as e:
                console.print(f"[yellow]Error loading configuration:[/yellow] {e}")

    @property
    def name(self) -> str:
        """Get the project name."""
        # First try to get from the data
        project_name = self.data.get("project", {}).get("name")
        if project_name:
            return project_name

        # Fallback: try to get from path if available
        if self.path:
            return os.path.basename(self.path.parent)

        # Last resort: try getcwd or use a default name
        try:
            return os.path.basename(os.getcwd())
        except (FileNotFoundError, OSError):
            return "maestria-project"

    @property
    def version(self) -> str:
        """Get the project version."""
        return self.data.get("project", {}).get("version", "0.1.0")

    @property
    def python_version(self) -> str:
        """Get the Python version."""
        requires_python = self.data.get("project", {}).get("requires-python", ">=3.10")
        # Extract a specific version from requires-python if possible
        # This is a simplistic implementation; could be improved
        if requires_python.startswith(">="):
            return requires_python[2:].split(",")[0]
        return "3.10"

    @property
    def description(self) -> str:
        """Get the project description."""
        return self.data.get("project", {}).get("description", "")

    @property
    def authors(self) -> List[Dict[str, str]]:
        """Get the project authors."""
        return self.data.get("project", {}).get("authors", [])

    @property
    def dependencies(self) -> List[str]:
        """Get project dependencies."""
        return self.data.get("project", {}).get("dependencies", [])

    @property
    def dev_dependencies(self) -> List[str]:
        """Get development dependencies."""
        optional_deps = self.data.get("project", {}).get("optional-dependencies", {})
        return optional_deps.get("dev", [])

    @property
    def scripts(self) -> Dict[str, Union[str, Dict[str, str]]]:
        """Get scripts configuration."""
        # Check for maestria scripts
        return self.data.get("tool", {}).get("maestria", {}).get("scripts", {})

    @property
    def pypi_repo(self) -> Optional[str]:
        """Get PyPI repository from constants."""
        return self.maestria.constants.pypi_repo

    @property
    def docker_hub_account(self) -> Optional[str]:
        """Get Docker Hub account from constants."""
        return self.maestria.constants.docker_hub_account

    @property
    def author(self) -> Optional[str]:
        """Get author from project metadata."""
        authors = self.authors
        if authors and len(authors) > 0:
            return authors[0].get("name")
        return None

    @property
    def author_email(self) -> Optional[str]:
        """Get author email from project metadata."""
        authors = self.authors
        if authors and len(authors) > 0:
            return authors[0].get("email")
        return None

    def get_git_info(self) -> Dict[str, Optional[str]]:
        """Get Git repository information.

        This derives the information from git configuration rather than
        requiring it to be specified in configuration.

        Returns:
            Dict containing 'org' and 'repo' keys with their values.
        """
        import re
        import subprocess

        result = {"org": None, "repo": None}

        try:
            # Get the remote URL
            remote_url = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=self.root_dir,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Parse org and repo from URL
            # Handle different formats:
            # - https://github.com/org/repo.git
            # - git@HOST:org/repo.git (SSH format)
            if remote_url:
                if remote_url.startswith("https://"):
                    # HTTPS format
                    match = re.search(r"https://[^/]+/([^/]+)/([^/.]+)", remote_url)
                    if match:
                        result["org"], result["repo"] = match.groups()
                elif "@" in remote_url and ":" in remote_url:
                    # SSH format
                    match = re.search(r"[^:]+:([^/]+)/([^/.]+)", remote_url)
                    if match:
                        result["org"], result["repo"] = match.groups()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Not a git repository or git not installed
            pass

        return result

    @property
    def root_dir(self) -> Path:
        """Get the project root directory."""
        if self.path is None:
            return Path.cwd()
        return self.path.parent

    @property
    def venv_path(self) -> Path:
        """Get the virtual environment path."""
        if self._venv_path is not None:
            venv = Path(self._venv_path)
            # If relative path, make it relative to root_dir
            if not venv.is_absolute():
                return self.root_dir / venv
            return venv
        # Default to .venv in root_dir
        return self.root_dir / ".venv"


def find_config(project_dir: Optional[Path] = None) -> Optional[Path]:
    """Find the pyproject.toml configuration file.

    Looks for pyproject.toml in the project directory and parent directories.

    Args:
        project_dir: Starting directory to search from. If None, uses current working directory.

    Returns:
        Path to pyproject.toml if found, None otherwise.
    """
    current = Path(project_dir).resolve() if project_dir else Path.cwd().resolve()

    # First check if project_dir itself is a pyproject.toml file
    if current.is_file() and current.name == "pyproject.toml":
        return current

    # Otherwise search up the directory tree
    while current.parent != current:
        config_path = current / "pyproject.toml"
        if config_path.exists():
            return config_path
        current = current.parent

    return None


def load_config(
    project_dir: Optional[Path] = None, venv_path: Optional[Path] = None
) -> MaestriaProjectConfig:
    """Load the Maestria configuration from pyproject.toml.

    Args:
        project_dir: Project directory to search for configuration.
                    If None, uses current working directory.
        venv_path: Virtual environment path. If None, defaults to .venv in project_dir.

    Returns:
        MaestriaProjectConfig instance with loaded configuration.
    """
    config_path = find_config(project_dir)

    if config_path is None:
        console.print(
            "[yellow]Warning:[/yellow] No pyproject.toml found. Using default configuration."
        )
        return MaestriaProjectConfig(venv_path=venv_path)

    return MaestriaProjectConfig(config_path, venv_path=venv_path)
