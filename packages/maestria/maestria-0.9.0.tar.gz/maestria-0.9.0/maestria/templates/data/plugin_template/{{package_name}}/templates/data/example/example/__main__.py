"""Main entry point for the example project."""

import click
from {{plugin_name}} import __version__ as plugin_version


@click.command()
def main():
    """Run the example."""
    click.echo(f"Example project using {{plugin_name}} v{plugin_version}")
    click.echo("This demonstrates how to use the {{plugin_name_short}} plugin.")


if __name__ == "__main__":
    main()