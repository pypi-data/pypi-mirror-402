"""Tests for the interactive shell mode."""

import pytest
from unittest.mock import patch
from click.testing import CliRunner

from {{project_slug}}.cli import main


class TestInteractiveShell:
    """Test the interactive shell functionality."""

    def test_shell_startup(self):
        """Test that the shell starts up correctly."""
        runner = CliRunner()
        
        # Simulate user entering 'exit'
        with patch('rich.console.Console.input', return_value='exit'):
            result = runner.invoke(main, ["shell"])
            
            assert result.exit_code == 0
            assert "Interactive Shell" in result.output
            assert "Type 'help'" in result.output

    def test_help_command(self):
        """Test that the help command works."""
        runner = CliRunner()
        
        # Simulate user entering 'help' then 'exit'
        with patch('rich.console.Console.input', side_effect=['help', 'exit']):
            result = runner.invoke(main, ["shell"])
            
            assert result.exit_code == 0
            assert "Available commands" in result.output
            assert "add" in result.output
            assert "sub" in result.output
            assert "sum" in result.output
            assert "memory" in result.output

    def test_add_command(self):
        """Test the add command in the shell."""
        runner = CliRunner()
        
        # Simulate user entering 'add 5 3' then 'exit'
        with patch('rich.console.Console.input', side_effect=['add 5 3', 'exit']):
            result = runner.invoke(main, ["shell"])
            
            assert result.exit_code == 0
            # Check for the numbers and result in any format
            assert "5" in result.output
            assert "3" in result.output
            assert "8" in result.output

    def test_sub_command(self):
        """Test the sub command in the shell."""
        runner = CliRunner()
        
        # Simulate user entering 'sub 10 4' then 'exit'
        with patch('rich.console.Console.input', side_effect=['sub 10 4', 'exit']):
            result = runner.invoke(main, ["shell"])
            
            assert result.exit_code == 0
            # Check for the numbers and result in any format
            assert "10" in result.output
            assert "4" in result.output
            assert "6" in result.output

    def test_sum_command(self):
        """Test the sum command in the shell."""
        runner = CliRunner()
        
        # Simulate user entering 'sum 1 2 3 4 5' then 'exit'
        with patch('rich.console.Console.input', side_effect=['sum 1 2 3 4 5', 'exit']):
            result = runner.invoke(main, ["shell"])
            
            assert result.exit_code == 0
            # Check that all numbers and the result appear somewhere in the output
            assert "1" in result.output
            assert "2" in result.output
            assert "3" in result.output
            assert "4" in result.output
            assert "5" in result.output
            assert "15" in result.output

    def test_memory_commands(self):
        """Test memory commands in the shell."""
        runner = CliRunner()
        
        # Simulate a sequence of memory operations
        commands = [
            'm+5',       # Add 5 to memory
            'memory',    # Show memory
            'm-2',       # Subtract 2 from memory
            'memory',    # Show memory
            'mr',        # Reset memory
            'memory',    # Verify reset
            'exit'       # Exit the shell
        ]
        
        with patch('rich.console.Console.input', side_effect=commands):
            result = runner.invoke(main, ["shell"])
            
            assert result.exit_code == 0
            # More flexible assertions to handle decimal formats
            assert "Added 5" in result.output or "Added 5.0" in result.output
            assert "Memory: 5" in result.output or "Memory: 5.0" in result.output
            assert "Subtracted 2" in result.output or "Subtracted 2.0" in result.output
            assert "Memory: 3" in result.output or "Memory: 3.0" in result.output
            assert "Memory reset to 0" in result.output
            assert "Memory: 0" in result.output

    def test_history_command(self):
        """Test the history command in the shell."""
        runner = CliRunner()
        
        # Simulate operations and then check history
        commands = [
            'm+10',       # Add 10 to memory
            'm-5',        # Subtract 5 from memory
            'history',    # Check history
            'exit'        # Exit the shell
        ]
        
        with patch('rich.console.Console.input', side_effect=commands):
            result = runner.invoke(main, ["shell"])
            
            assert result.exit_code == 0
            assert "Operation History" in result.output
            assert "add" in result.output
            assert "10" in result.output
            assert "subtract" in result.output
            assert "5" in result.output

    def test_invalid_command(self):
        """Test handling of invalid commands."""
        runner = CliRunner()
        
        # Simulate user entering an invalid command then 'exit'
        with patch('rich.console.Console.input', side_effect=['invalid_command', 'exit']):
            result = runner.invoke(main, ["shell"])
            
            assert result.exit_code == 0
            assert "Unknown command" in result.output

    def test_invalid_format(self):
        """Test handling of commands with invalid format."""
        runner = CliRunner()
        
        # Simulate user entering commands with invalid formats
        commands = [
            'add 5',      # Missing second operand
            'sub',        # Missing operands
            'sum abc',    # Invalid number
            'exit'        # Exit the shell
        ]
        
        with patch('rich.console.Console.input', side_effect=commands):
            result = runner.invoke(main, ["shell"])
            
            assert result.exit_code == 0
            assert "Invalid format" in result.output or "Invalid numbers" in result.output