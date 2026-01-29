"""Tests for the {{plugin_name}} plugin."""

import pytest
from click.testing import CliRunner

from {{package_name}} import Plugin
from {{package_name}}.commands.hello import hello
from {{package_name}}.commands.analyze import analyze


class TestPluginRegistration:
    """Test plugin registration functionality."""

    def test_plugin_name(self):
        """Test that the plugin name is set correctly."""
        assert Plugin.name == "{{plugin_name_short}}"
        assert isinstance(Plugin.description, str)

    def test_command_registration(self):
        """Test that commands are registered correctly."""
        commands = Plugin.get_commands()
        assert Plugin.name in commands
        assert callable(commands[Plugin.name])

    def test_hook_registration(self):
        """Test that hooks are registered correctly."""
        hooks = Plugin.get_hooks()
        assert "pre_command" in hooks
        assert "post_command" in hooks
        assert len(hooks["pre_command"]) > 0
        assert len(hooks["post_command"]) > 0
        
        # Check that all hooks are callable
        for hook_name, hook_list in hooks.items():
            for hook in hook_list:
                assert callable(hook)


class TestCommands:
    """Test plugin commands."""

    def test_hello_command(self):
        """Test the hello command."""
        runner = CliRunner()
        result = runner.invoke(hello, ["Test"])
        assert result.exit_code == 0
        assert "Hello, Test" in result.output
        
        # Test with formal option
        result = runner.invoke(hello, ["Test", "--formal"])
        assert result.exit_code == 0
        assert "Greetings, Mr/Ms Test" in result.output

    def test_analyze_command(self, tmp_path):
        """Test the analyze command with a temporary directory."""
        # Create a test file in the temporary directory
        test_file = tmp_path / "test.py"
        test_file.write_text("print('Hello, world!')")
        
        # Run analyze command
        runner = CliRunner()
        result = runner.invoke(analyze, [str(tmp_path)])
        assert result.exit_code == 0
        assert "Project Analysis Results" in result.output
        assert "Python lines of code" in result.output
        
        # Test with output file
        output_file = tmp_path / "analysis.json"
        result = runner.invoke(analyze, [str(tmp_path), "--output", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()


class TestUtilities:
    """Test plugin utilities."""

    def test_format_greeting(self):
        """Test the format_greeting function."""
        from {{package_name}}.utils.formatting import format_greeting
        
        # Test normal greeting
        greeting = format_greeting("Test")
        assert "Hello, Test" in greeting
        assert "{{plugin_name_short}}" in greeting
        
        # Test formal greeting
        formal_greeting = format_greeting("Test", formal=True)
        assert "Greetings, Mr/Ms Test" in formal_greeting
        assert "{{plugin_name_short}}" in formal_greeting
        
    def test_analyze_project(self, tmp_path):
        """Test the analyze_project function."""
        from {{package_name}}.utils.analysis import analyze_project
        
        # Create a test file in the temporary directory
        test_file = tmp_path / "test.py"
        test_file.write_text("print('Hello, world!')")
        
        # Create a README file
        readme_file = tmp_path / "README.md"
        readme_file.write_text("# Test Project")
        
        # Run analysis
        results = analyze_project(tmp_path)
        
        assert isinstance(results, dict)
        assert "Total files" in results
        assert results["Total files"] == 2
        assert "Python lines of code" in results
        assert results["Python lines of code"] == 1
        assert "Has README.md" in results
        assert results["Has README.md"] is True