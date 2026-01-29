"""Tests for the {{project_name}} CLI."""

from click.testing import CliRunner
import pytest

from {{project_slug}}.cli import main
from {{project_slug}}.api import Calculator


def test_main():
    """Test the main CLI function with no arguments."""
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "{{project_name}}" in result.output


def test_version():
    """Test the --version flag."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


def test_calculate_add():
    """Test the calculate add command."""
    runner = CliRunner()
    result = runner.invoke(main, ["calculate", "add", "5", "3"])
    assert result.exit_code == 0
    # Check for the numbers and result in any format
    assert "5" in result.output
    assert "3" in result.output
    assert "8" in result.output


def test_calculate_subtract():
    """Test the calculate subtract command."""
    runner = CliRunner()
    result = runner.invoke(main, ["calculate", "subtract", "5", "3"])
    assert result.exit_code == 0
    # Check for the numbers and result in any format
    assert "5" in result.output
    assert "3" in result.output
    assert "2" in result.output


def test_calculate_sum():
    """Test the calculate sum command."""
    runner = CliRunner()
    result = runner.invoke(main, ["calculate", "sum", "1", "2", "3", "4", "5"])
    assert result.exit_code == 0
    assert "15" in result.output


def test_memory_operations():
    """Test memory operations."""
    runner = CliRunner()
    obj = {"calculator": Calculator()}
    
    # Add to memory
    result = runner.invoke(main, ["memory", "add", "5"], obj=obj)
    assert result.exit_code == 0
    assert "Added 5" in result.output or "Added 5.0" in result.output
    
    # Subtract from memory
    result = runner.invoke(main, ["memory", "subtract", "2"], obj=obj)
    assert result.exit_code == 0
    assert "Subtracted 2" in result.output or "Subtracted 2.0" in result.output
    
    # Show memory value
    result = runner.invoke(main, ["memory", "show"], obj=obj)
    assert result.exit_code == 0
    assert "Memory: 3" in result.output or "Memory: 3.0" in result.output
    
    # Reset memory
    result = runner.invoke(main, ["memory", "reset"], obj=obj)
    assert result.exit_code == 0
    assert "Memory reset to 0" in result.output
    
    # Verify memory is reset
    result = runner.invoke(main, ["memory", "show"], obj=obj)
    assert result.exit_code == 0
    assert "Memory: 0" in result.output