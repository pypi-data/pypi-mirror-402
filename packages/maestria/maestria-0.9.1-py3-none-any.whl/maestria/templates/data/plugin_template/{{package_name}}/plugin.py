"""Main plugin implementation for {{plugin_name}}."""

from typing import Dict, List, Callable, Any, Optional
import click
from pathlib import Path

from maestria.plugins import MaestriaPlugin

from {{package_name}}.commands.main import main_command_group
from {{package_name}}.hooks import pre_command_hook, post_command_hook


class Plugin(MaestriaPlugin):
    """Maestria plugin implementation for {{plugin_name}}.
    
    This plugin provides additional functionality for Maestria projects.
    It registers commands, hooks, and templates.
    """
    
    # Plugin metadata
    name = "{{plugin_name_short}}"
    description = "A Maestria plugin for {{plugin_name_short}} functionality"
    
    @classmethod
    def get_commands(cls) -> Dict[str, Callable]:
        """Get plugin commands.
        
        Returns:
            Dictionary mapping command names to command implementations.
        """
        return {
            cls.name: main_command_group
        }
    
    @classmethod
    def get_hooks(cls) -> Dict[str, List[Callable]]:
        """Get plugin hooks.
        
        Returns:
            Dictionary mapping hook names to lists of hook implementations.
        """
        return {
            "pre_command": [pre_command_hook],
            "post_command": [post_command_hook],
        }
    
    @classmethod
    def get_templates(cls) -> Dict[str, Dict[str, Any]]:
        """Get plugin templates.
        
        Returns:
            Dictionary mapping template names to template configurations.
        """
        # Path to template data directory
        template_dir = Path(__file__).parent / "templates" / "data"
        
        if not template_dir.exists():
            return {}
        
        return {
            f"{cls.name}_template": {
                "type": "local",
                "path": str(template_dir),
                "description": f"Template for {cls.name} projects"
            }
        }