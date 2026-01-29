"""Analyze command for the {{plugin_name}} plugin."""

import os
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from {{package_name}}.commands.main import main_command_group
from {{package_name}}.utils.analysis import analyze_project

console = Console()


@main_command_group.command()
@click.argument("project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--output", "-o", type=click.Path(file_okay=True, dir_okay=False), 
              help="Output file for the analysis results")
def analyze(project_path: str, output: str = None) -> None:
    """Analyze a Python project.
    
    This command analyzes a Python project directory and provides
    statistics and insights about the codebase.
    
    Args:
        project_path: Path to the Python project to analyze
        output: Optional file path to save the analysis results
    """
    project_dir = Path(project_path)
    
    console.print(f"[bold blue]Analyzing project at {project_dir.absolute()}[/bold blue]")
    
    try:
        # Perform analysis
        results = analyze_project(project_dir)
        
        # Display results in a table
        table = Table(title="Project Analysis Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for metric, value in results.items():
            table.add_row(metric, str(value))
        
        console.print(table)
        
        # Save results if output file specified
        if output:
            import json
            with open(output, 'w') as f:
                json.dump(results, f, indent=2)
            console.print(f"[green]Analysis results saved to {output}[/green]")
    
    except Exception as e:
        console.print(f"[bold red]Error analyzing project:[/bold red] {str(e)}")
        return