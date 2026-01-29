"""Hooks for the {{plugin_name}} plugin."""

from typing import Any, Dict, Optional
import time
from rich.console import Console

console = Console()
_start_time: Optional[float] = None


def pre_command_hook(*args: Any, **kwargs: Any) -> None:
    """Run before a command is executed.

    This hook runs before any Maestria command and can be used
    to perform setup tasks or modify command behavior.

    Args:
        *args: Variable arguments passed from the command
        **kwargs: Keyword arguments passed from the command
    """
    global _start_time
    _start_time = time.time()

    # Uncomment the following line to show a message when the hook runs
    # console.print("[dim]{{plugin_name_short}} pre-command hook executed[/dim]")


def post_command_hook(*args: Any, **kwargs: Any) -> None:
    """Run after a command is executed.

    This hook runs after any Maestria command and can be used
    to perform cleanup tasks or log information.

    Args:
        *args: Variable arguments passed from the command
        **kwargs: Keyword arguments passed from the command
    """
    global _start_time
    if _start_time is not None:
        elapsed = time.time() - _start_time

        # Uncomment the following line to show execution time
        # console.print(f"[dim]Command executed in {elapsed:.2f}s[/dim]")

    # Reset start time
    _start_time = None
