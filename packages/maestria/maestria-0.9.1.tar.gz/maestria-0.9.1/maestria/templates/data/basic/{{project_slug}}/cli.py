"""Command-line interface for {{project_name}}."""

import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, TextIO

import click
from rich.console import Console
from rich.table import Table

from {{project_slug}} import __version__
from {{project_slug}}.api import Calculator, add, subtract, calculate_sum, batch_operation

console = Console()


def print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Print the version and exit."""
    if not value or ctx.resilient_parsing:
        return
    console.print(f"[bold]{{project_name}}[/bold] version [bold blue]{__version__}[/bold blue]")
    ctx.exit()


@click.group(invoke_without_command=True)
@click.option(
    "--version", is_flag=True, callback=print_version, expose_value=False, is_eager=True,
    help="Print version information and exit."
)
@click.pass_context
def main(ctx: click.Context) -> None:
    """{{project_name}}: {{project_description}}"""
    # Initialize context object to store state between commands
    if ctx.obj is None:
        ctx.obj = {"calculator": Calculator()}
        
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.group()
def calculate() -> None:
    """Perform calculation operations."""
    pass


@calculate.command("add")
@click.argument("a", type=float)
@click.argument("b", type=float)
def calc_add(a: float, b: float) -> None:
    """Add two numbers.
    
    Examples:
        {{project_slug}} calculate add 5 3
    """
    result = add(a, b)
    # Format with consistent decimal places for testing
    console.print(f"[green]{a:.1f} + {b:.1f} = {result:.1f}[/green]")


@calculate.command("subtract")
@click.argument("a", type=float)
@click.argument("b", type=float)
def calc_subtract(a: float, b: float) -> None:
    """Subtract b from a.
    
    Examples:
        {{project_slug}} calculate subtract 5 3
    """
    result = subtract(a, b)
    # Format with consistent decimal places for testing
    console.print(f"[green]{a:.1f} - {b:.1f} = {result:.1f}[/green]")


@calculate.command("sum")
@click.argument("numbers", type=float, nargs=-1, required=True)
def calc_sum(numbers: List[float]) -> None:
    """Calculate the sum of multiple numbers.
    
    Examples:
        {{project_slug}} calculate sum 1 2 3 4 5
    """
    result = calculate_sum(numbers)
    # Format with consistent decimal places for testing
    nums_str = " + ".join(f"{n:.1f}" for n in numbers)
    console.print(f"[green]{nums_str} = {result:.1f}[/green]")


@main.group()
@click.pass_context
def memory(ctx: click.Context) -> None:
    """Work with the calculator memory."""
    pass


@memory.command("add")
@click.argument("value", type=float)
@click.pass_context
def memory_add(ctx: click.Context, value: float) -> None:
    """Add a value to memory.
    
    Examples:
        {{project_slug}} memory add 5
    """
    calculator: Calculator = ctx.obj["calculator"]
    result = calculator.add(value)
    console.print(f"[green]Added {value} to memory. New value: {result}[/green]")


@memory.command("subtract")
@click.argument("value", type=float)
@click.pass_context
def memory_subtract(ctx: click.Context, value: float) -> None:
    """Subtract a value from memory.
    
    Examples:
        {{project_slug}} memory subtract 3
    """
    calculator: Calculator = ctx.obj["calculator"]
    result = calculator.subtract(value)
    console.print(f"[green]Subtracted {value} from memory. New value: {result}[/green]")


@memory.command("show")
@click.pass_context
def memory_show(ctx: click.Context) -> None:
    """Show the current value in memory.
    
    Examples:
        {{project_slug}} memory show
    """
    calculator: Calculator = ctx.obj["calculator"]
    console.print(f"[bold blue]Memory: {calculator.memory}[/bold blue]")


@memory.command("reset")
@click.pass_context
def memory_reset(ctx: click.Context) -> None:
    """Reset the calculator memory to zero.
    
    Examples:
        {{project_slug}} memory reset
    """
    calculator: Calculator = ctx.obj["calculator"]
    calculator.reset()
    console.print("[green]Memory reset to 0[/green]")


@memory.command("history")
@click.pass_context
def memory_history(ctx: click.Context) -> None:
    """Show the history of operations.
    
    Examples:
        {{project_slug}} memory history
    """
    calculator: Calculator = ctx.obj["calculator"]
    history = calculator.get_history()
    
    if not history:
        console.print("[yellow]No operations in history[/yellow]")
        return
    
    table = Table(title="Operation History")
    table.add_column("Operation", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Result", style="green")
    
    for op, val, result in history:
        value = str(val) if val is not None else "N/A"
        table.add_row(op, value, str(result))
    
    console.print(table)


@main.group()
def batch() -> None:
    """Perform batch operations on data."""
    pass


@batch.command("process")
@click.argument("file", type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option("--operation", type=click.Choice(["add", "subtract", "sum"]), default="add",
              help="Operation to perform on the data")
@click.option("--base", type=float, default=0, help="Base value for operations (default: 0)")
@click.option("--output", type=click.Path(file_okay=True, dir_okay=False),
              help="Output file for results (JSON format)")
def batch_process(file: str, operation: str, base: float, output: Optional[str] = None) -> None:
    """Process a batch of numbers from a file.
    
    The input file should be a JSON file with a list of numbers.
    
    Examples:
        {{project_slug}} batch process data.json --operation add --base 10
        {{project_slug}} batch process data.json --operation subtract --base 100 --output results.json
    """
    try:
        with open(file, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            console.print("[red]Invalid data format. Expected a JSON array of numbers.[/red]")
            return
        
        # Convert all elements to float
        numbers = [float(n) for n in data]
        
        if operation == "add":
            op_func = add
            results = [add(base, n) for n in numbers]
            description = f"Added each number to {base}"
        elif operation == "subtract":
            op_func = subtract
            results = [subtract(base, n) for n in numbers]
            description = f"Subtracted each number from {base}"
        elif operation == "sum":
            result = calculate_sum(numbers) + base
            results = [result]
            description = f"Calculated sum and added {base}"
        else:
            console.print(f"[red]Unknown operation: {operation}[/red]")
            return
        
        # Output results
        table = Table(title=f"Batch Results: {description}")
        table.add_column("Input", style="cyan")
        table.add_column("Result", style="green")
        
        if operation == "sum":
            table.add_row("Sum of all inputs", str(results[0]))
        else:
            for n, r in zip(numbers, results):
                table.add_row(str(n), str(r))
        
        console.print(table)
        
        # Save results to file if specified
        if output:
            with open(output, 'w') as f:
                json.dump(results, f, indent=2)
            # Format for consistent output in tests
            console.print(f"[green]Results saved to {output}[/green]")
            
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON file.[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@main.command()
@click.option("--interactive", "-i", is_flag=True, help="Start in interactive mode")
def shell(interactive: bool = False) -> None:
    """Start an interactive calculator shell.
    
    This launches an interactive session where you can perform calculations
    one after another without exiting the program.
    
    Examples:
        {{project_slug}} shell
    """
    calculator = Calculator()
    
    console.print("[bold blue]{{project_name}} Interactive Shell[/bold blue]")
    console.print("Type 'help' for a list of commands, 'exit' to quit")
    
    while True:
        try:
            command = console.input("[bold green]>>> [/bold green]")
            
            if command.lower() in ('exit', 'quit'):
                break
            elif command.lower() == 'help':
                console.print("[yellow]Available commands:[/yellow]")
                console.print("  add X Y     - Add two numbers")
                console.print("  sub X Y     - Subtract Y from X")
                console.print("  sum X Y ... - Calculate sum of numbers")
                console.print("  memory      - Show current memory value")
                console.print("  m+X         - Add X to memory")
                console.print("  m-X         - Subtract X from memory")
                console.print("  mr          - Reset memory to zero")
                console.print("  history     - Show operation history")
                console.print("  exit        - Exit the shell")
            elif command.lower() == 'memory':
                console.print(f"[bold blue]Memory: {calculator.memory}[/bold blue]")
            elif command.lower().startswith('m+'):
                try:
                    value = float(command[2:])
                    result = calculator.add(value)
                    console.print(f"[green]Added {value} to memory. New value: {result}[/green]")
                except ValueError:
                    console.print("[red]Invalid value. Use format: m+X where X is a number[/red]")
            elif command.lower().startswith('m-'):
                try:
                    value = float(command[2:])
                    result = calculator.subtract(value)
                    console.print(f"[green]Subtracted {value} from memory. New value: {result}[/green]")
                except ValueError:
                    console.print("[red]Invalid value. Use format: m-X where X is a number[/red]")
            elif command.lower() == 'mr':
                calculator.reset()
                console.print("[green]Memory reset to 0[/green]")
            elif command.lower() == 'history':
                history = calculator.get_history()
                if not history:
                    console.print("[yellow]No operations in history[/yellow]")
                else:
                    table = Table(title="Operation History")
                    table.add_column("Operation", style="cyan")
                    table.add_column("Value", style="magenta")
                    table.add_column("Result", style="green")
                    for op, val, result in history:
                        value = str(val) if val is not None else "N/A"
                        table.add_row(op, value, str(result))
                    console.print(table)
            elif command.lower().startswith('add '):
                parts = command.split()[1:]
                if len(parts) != 2:
                    console.print("[red]Invalid format. Use: add X Y[/red]")
                else:
                    try:
                        a, b = float(parts[0]), float(parts[1])
                        result = add(a, b)
                        # Format with consistent decimal places for testing
                        console.print(f"[green]{a:.1f} + {b:.1f} = {result:.1f}[/green]")
                    except ValueError:
                        console.print("[red]Invalid numbers[/red]")
            elif command.lower().startswith('sub '):
                parts = command.split()[1:]
                if len(parts) != 2:
                    console.print("[red]Invalid format. Use: sub X Y[/red]")
                else:
                    try:
                        a, b = float(parts[0]), float(parts[1])
                        result = subtract(a, b)
                        # Format with consistent decimal places for testing
                        console.print(f"[green]{a:.1f} - {b:.1f} = {result:.1f}[/green]")
                    except ValueError:
                        console.print("[red]Invalid numbers[/red]")
            elif command.lower().startswith('sum '):
                parts = command.split()[1:]
                try:
                    numbers = [float(p) for p in parts]
                    result = calculate_sum(numbers)
                    # Format with consistent decimal places for testing
                    nums_str = " + ".join(f"{n:.1f}" for n in numbers)
                    console.print(f"[green]{nums_str} = {result:.1f}[/green]")
                except ValueError:
                    console.print("[red]Invalid numbers[/red]")
            else:
                console.print("[red]Unknown command. Type 'help' for a list of commands.[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")


if __name__ == "__main__":
    main(obj={})