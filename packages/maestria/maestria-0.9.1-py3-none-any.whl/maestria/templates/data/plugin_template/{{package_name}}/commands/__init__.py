"""Commands for the {{plugin_name}} plugin."""

from {{package_name}}.commands.main import main_command_group
from {{package_name}}.commands.hello import hello
from {{package_name}}.commands.analyze import analyze

__all__ = ["main_command_group", "hello", "analyze"]