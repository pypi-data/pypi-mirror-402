"""Main command group for the {{plugin_name}} plugin."""

import click
from rich.console import Console

console = Console()


@click.group(name="{{plugin_name_short}}", invoke_without_command=True)
@click.pass_context
def main_command_group(ctx: click.Context) -> None:
    """{{plugin_name_short}} plugin commands for Maestria."""
    if ctx.invoked_subcommand is None:
        console.print("[bold blue]{{plugin_name_short}} Plugin[/bold blue]")
        console.print(
            f"Run 'maestria {{plugin_name_short}} --help' for available commands."
        )

        # Display plugin information
        console.print("\n[bold]Available Commands:[/bold]")
        commands = []
        for command in main_command_group.commands.values():
            commands.append(f"- {command.name}: {command.help}")

        for cmd_info in sorted(commands):
            console.print(cmd_info)
