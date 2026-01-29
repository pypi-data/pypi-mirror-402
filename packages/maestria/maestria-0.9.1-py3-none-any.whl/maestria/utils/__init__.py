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

"""Common utilities for Maestria."""

import configparser
import os
import sys
from pathlib import Path
from typing import List, Optional


def get_venv_bin_dir(venv_path: Path) -> Path:
    """Get the bin/Scripts directory of a virtual environment.

    Args:
        venv_path: Path to the virtual environment

    Returns:
        Path to bin/ (Unix) or Scripts/ (Windows) directory

    Example:
        >>> venv_bin = get_venv_bin_dir(Path(".venv"))
        >>> # On Unix: .venv/bin
        >>> # On Windows: .venv/Scripts
    """
    return venv_path / ("Scripts" if sys.platform == "win32" else "bin")


def get_venv_python(venv_path: Path) -> Path:
    """Get the Python executable path in a virtual environment.

    Args:
        venv_path: Path to the virtual environment

    Returns:
        Path to python executable (with .exe on Windows)

    Example:
        >>> python = get_venv_python(Path(".venv"))
        >>> # On Unix: .venv/bin/python
        >>> # On Windows: .venv/Scripts/python.exe
    """
    bin_dir = get_venv_bin_dir(venv_path)
    return bin_dir / ("python.exe" if sys.platform == "win32" else "python")


def get_venv_executable(
    venv_path: Path, name: str, windows_ext: Optional[str] = None
) -> Path:
    """Get path to an executable in a virtual environment.

    Args:
        venv_path: Path to the virtual environment
        name: Name of the executable (without extension)
        windows_ext: Extension to use on Windows (e.g., ".exe"), or None for no extension

    Returns:
        Path to the executable

    Example:
        >>> bump = get_venv_executable(Path(".venv"), "bump2version", ".exe")
        >>> # On Unix: .venv/bin/bump2version
        >>> # On Windows: .venv/Scripts/bump2version.exe
    """
    bin_dir = get_venv_bin_dir(venv_path)
    if sys.platform == "win32" and windows_ext:
        return bin_dir / f"{name}{windows_ext}"
    return bin_dir / name


def normalize_venv_path(project_dir: Path, venv_path: Path) -> Path:
    """Normalize venv_path to absolute path relative to project_dir.

    Args:
        project_dir: Path to the project directory
        venv_path: Path to the virtual environment (relative or absolute)

    Returns:
        Absolute path to the virtual environment

    Example:
        >>> venv = normalize_venv_path(Path("/project"), Path(".venv"))
        >>> # Returns: /project/.venv
    """
    if not venv_path.is_absolute():
        return project_dir / venv_path
    return venv_path


def get_pip_config_paths() -> List[Path]:
    """Get possible pip configuration file paths in order of priority.

    Returns:
        List of paths to check for pip configuration files

    Example:
        >>> paths = get_pip_config_paths()
        >>> # Returns: [~/.pip/pip.conf, ~/.config/pip/pip.conf, etc.]
    """
    paths = []

    if sys.platform == "win32":
        if "APPDATA" in os.environ:
            paths.append(Path(os.environ["APPDATA"]) / "pip" / "pip.ini")
        paths.append(Path.home() / "pip" / "pip.ini")
    else:
        paths.append(Path.home() / ".pip" / "pip.conf")
        if "XDG_CONFIG_HOME" in os.environ:
            paths.append(Path(os.environ["XDG_CONFIG_HOME"]) / "pip" / "pip.conf")
        else:
            paths.append(Path.home() / ".config" / "pip" / "pip.conf")

    paths.append(Path("/etc/pip.conf"))

    return paths


def parse_pip_config() -> dict:
    """Parse pip configuration files and extract index URLs.

    Returns:
        Dictionary with 'index_url' and 'extra_index_urls' keys

    Example:
        >>> config = parse_pip_config()
        >>> # Returns: {'index_url': 'https://pypi.org/simple', 'extra_index_urls': [...]}
    """
    config: dict = {"index_url": None, "extra_index_urls": []}

    for config_path in get_pip_config_paths():
        if not config_path.exists():
            continue

        parser = configparser.ConfigParser()
        try:
            parser.read(config_path)

            if parser.has_section("global"):
                if parser.has_option("global", "index-url"):
                    config["index_url"] = parser.get("global", "index-url")

                if parser.has_option("global", "extra-index-url"):
                    extra_urls = parser.get("global", "extra-index-url")
                    urls = [
                        url.strip() for url in extra_urls.split("\n") if url.strip()
                    ]
                    config["extra_index_urls"].extend(urls)
        except Exception:
            continue

    return config


def get_uv_index_args() -> List[str]:
    """Get UV index URL arguments based on pip configuration.

    Returns:
        List of UV command-line arguments for index URLs

    Example:
        >>> args = get_uv_index_args()
        >>> # Returns: ['--index-url', 'https://pypi.org/simple', '--extra-index-url', ...]
    """
    args = []
    pip_config = parse_pip_config()

    if pip_config["index_url"]:
        args.extend(["--index-url", pip_config["index_url"]])

    for extra_url in pip_config["extra_index_urls"]:
        args.extend(["--extra-index-url", extra_url])

    return args
