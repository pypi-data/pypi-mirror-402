"""Maestria plugin: {{plugin_name}}."""

from typing import Dict, List, Callable, Any, Optional
import importlib.metadata

from {{package_name}}.plugin import Plugin

try:
    __version__ = importlib.metadata.version("{{plugin_name}}")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = ["Plugin"]