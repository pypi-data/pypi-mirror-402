"""Hello command for the {{plugin_name}} plugin."""

import click
from rich.console import Console

from {{package_name}}.commands.main import main_command_group
from {{package_name}}.utils.formatting import format_greeting

console = Console()


@main_command_group.command()
@click.argument("name")
@click.option("--formal", is_flag=True, help="Use formal greeting")
def hello(name: str, formal: bool = False) -> None:
    """Say hello to someone.
    
    This command demonstrates a simple greeting functionality.
    
    Args:
        name: The name to greet
        formal: Whether to use a formal greeting
    """
    greeting = format_greeting(name, formal)
    console.print(f"[green]{greeting}[/green]")