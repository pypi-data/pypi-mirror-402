"""Tests for the Maestria CLI."""

import re
from unittest.mock import Mock, patch

import click
from click.testing import CliRunner

from maestria.cli import cli, main, print_version, register_plugin_commands


def strip_ansi(text: str) -> str:
    """Strip ANSI color codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def test_version():
    """Test the version option."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "Maestria version" in strip_ansi(result.output)


def test_help():
    """Test the help option."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Maestria: A thin, modern Python project management tool" in result.output

    # Check for all main commands
    commands = [
        "init",
        "env",
        "run",
        "install",
        "test",
        "lint",
        "audit",
        "build",
        "release",
    ]
    for command in commands:
        assert command in result.output


def test_cli_no_command():
    """Test CLI without any command shows help."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Maestria: A thin, modern Python project management tool" in result.output


def test_cli_verbose():
    """Test verbose flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--verbose"])
    assert result.exit_code == 0
    # When no command is given, help is shown
    assert "Maestria" in result.output


@patch("maestria.commands.init.initialize_project")
def test_init_command(mock_init):
    """Test init command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "test-project"])
    assert result.exit_code == 0
    mock_init.assert_called_once_with("test-project", "basic", "3.10")


@patch("maestria.commands.init.initialize_project")
def test_init_command_with_template(mock_init):
    """Test init command with custom template."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["init", "test-project", "--template", "plugin_template"]
    )
    assert result.exit_code == 0
    mock_init.assert_called_once_with("test-project", "plugin_template", "3.10")


@patch("maestria.commands.init.initialize_project")
def test_init_command_with_python_version(mock_init):
    """Test init command with custom Python version."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "test-project", "--python", "3.11"])
    assert result.exit_code == 0
    mock_init.assert_called_once_with("test-project", "basic", "3.11")


@patch("maestria.cli.load_config")
@patch("maestria.commands.env.setup_environment")
def test_env_setup_command(mock_setup, mock_config):
    """Test env setup command."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["env", "setup"])
    assert result.exit_code == 0
    mock_setup.assert_called_once()


@patch("maestria.cli.load_config")
@patch("maestria.commands.env.update_environment")
def test_env_update_command(mock_update, mock_config):
    """Test env update command."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["env", "update"])
    assert result.exit_code == 0
    mock_update.assert_called_once()


@patch("maestria.cli.load_config")
@patch("maestria.commands.env.show_environment_info")
def test_env_info_command(mock_info, mock_config):
    """Test env info command."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["env", "info"])
    assert result.exit_code == 0
    mock_info.assert_called_once()


@patch("maestria.cli.load_config")
@patch("maestria.commands.run.run_script")
def test_run_command(mock_run, mock_config):
    """Test run command."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "dev"])
    assert result.exit_code == 0
    mock_run.assert_called_once()


@patch("maestria.cli.load_config")
@patch("maestria.commands.run.run_script")
def test_run_command_with_args(mock_run, mock_config):
    """Test run command with arguments."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "dev", "--", "--port", "8000"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0]
    # Args are passed as a tuple
    assert "--port" in call_args[2] or "--port" in str(call_args[2])
    assert "8000" in call_args[2] or "8000" in str(call_args[2])


@patch("maestria.cli.load_config")
@patch("maestria.commands.test.run_tests")
def test_test_command(mock_test, mock_config):
    """Test test command."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["test"])
    assert result.exit_code == 0
    mock_test.assert_called_once()


@patch("maestria.cli.load_config")
@patch("maestria.commands.test.run_tests")
def test_test_command_with_all(mock_test, mock_config):
    """Test test command with --all flag."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["test", "--all"])
    assert result.exit_code == 0
    call_args = mock_test.call_args
    assert call_args[1]["run_all"] is True


@patch("maestria.cli.load_config")
@patch("maestria.commands.test.run_tests")
def test_test_command_with_specific_tests(mock_test, mock_config):
    """Test test command with specific test files."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["test", "tests/test_foo.py", "tests/test_bar.py"])
    assert result.exit_code == 0
    call_args = mock_test.call_args
    assert "tests/test_foo.py" in call_args[1]["pytest_args"]
    assert "tests/test_bar.py" in call_args[1]["pytest_args"]


@patch("maestria.cli.load_config")
@patch("maestria.commands.lint.run_linting")
def test_lint_command(mock_lint, mock_config):
    """Test lint command."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["lint"])
    assert result.exit_code == 0
    mock_lint.assert_called_once()


@patch("maestria.cli.load_config")
@patch("maestria.commands.lint.run_linting")
def test_lint_command_with_check(mock_lint, mock_config):
    """Test lint command with --check flag."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["lint", "--check"])
    assert result.exit_code == 0
    call_args = mock_lint.call_args
    assert call_args[1]["check"] is True


@patch("maestria.cli.load_config")
@patch("maestria.commands.audit.run_audit")
def test_audit_command(mock_audit, mock_config):
    """Test audit command."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["audit"])
    assert result.exit_code == 0
    mock_audit.assert_called_once()


@patch("maestria.cli.load_config")
@patch("maestria.commands.audit.run_audit")
def test_audit_command_code_only(mock_audit, mock_config):
    """Test audit command with --code-only flag."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["audit", "--code-only"])
    assert result.exit_code == 0
    call_args = mock_audit.call_args
    assert call_args[1]["code_only"] is True


@patch("maestria.cli.load_config")
@patch("maestria.commands.audit.run_audit")
def test_audit_command_deps_only(mock_audit, mock_config):
    """Test audit command with --deps-only flag."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["audit", "--deps-only"])
    assert result.exit_code == 0
    call_args = mock_audit.call_args
    assert call_args[1]["deps_only"] is True


@patch("maestria.cli.load_config")
@patch("maestria.commands.build.build_project")
def test_build_command(mock_build, mock_config):
    """Test build command."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["build"])
    assert result.exit_code == 0
    mock_build.assert_called_once()


@patch("maestria.cli.load_config")
@patch("maestria.commands.install.install_dependencies")
def test_install_command(mock_install, mock_config):
    """Test install command installs dev dependencies by default."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["install"])
    assert result.exit_code == 0
    mock_install.assert_called_once()
    call_args = mock_install.call_args
    assert call_args[1]["dev"] is True
    assert call_args[1]["editable"] is True


@patch("maestria.cli.load_config")
@patch("maestria.commands.install.install_dependencies")
def test_install_command_with_prod_only(mock_install, mock_config):
    """Test install command with --prod-only flag."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["install", "--prod-only"])
    assert result.exit_code == 0
    call_args = mock_install.call_args
    assert call_args[1]["dev"] is False


@patch("maestria.cli.load_config")
@patch("maestria.commands.install.install_dependencies")
def test_install_command_with_update(mock_install, mock_config):
    """Test install command with --update flag."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["install", "--update"])
    assert result.exit_code == 0
    call_args = mock_install.call_args
    assert call_args[1]["update"] is True


@patch("maestria.cli.load_config")
@patch("maestria.commands.install.install_dependencies")
def test_install_command_with_no_editable(mock_install, mock_config):
    """Test install command with --no-editable flag."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["install", "--no-editable"])
    assert result.exit_code == 0
    call_args = mock_install.call_args
    assert call_args[1]["editable"] is False


@patch("maestria.cli.load_config")
@patch("maestria.commands.release.release_project")
def test_release_command(mock_release, mock_config):
    """Test release command."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["release"])
    assert result.exit_code == 0
    mock_release.assert_called_once()
    call_args = mock_release.call_args
    assert call_args[1]["bump"] == "patch"


@patch("maestria.cli.load_config")
@patch("maestria.commands.release.release_project")
def test_release_command_with_bump(mock_release, mock_config):
    """Test release command with --bump flag."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["release", "--bump", "minor"])
    assert result.exit_code == 0
    call_args = mock_release.call_args
    assert call_args[1]["bump"] == "minor"


@patch("maestria.cli.load_config")
@patch("maestria.commands.release.release_project")
def test_release_command_with_install_deps(mock_release, mock_config):
    """Test release command with --install-deps flag."""
    mock_config.return_value = Mock()
    runner = CliRunner()
    result = runner.invoke(cli, ["release", "--install-deps"])
    assert result.exit_code == 0
    call_args = mock_release.call_args
    assert call_args[1]["install_deps"] is True


@patch("maestria.cli.get_plugin_commands")
def test_register_plugin_commands(mock_get_commands):
    """Test registering plugin commands."""
    mock_cmd = click.Command("test-plugin")
    mock_get_commands.return_value = {"test-plugin": mock_cmd}

    register_plugin_commands()

    # Check that command was added
    assert "test-plugin" in [cmd.name for cmd in cli.commands.values()]


@patch("maestria.cli.get_plugin_commands")
def test_register_plugin_commands_function(mock_get_commands):
    """Test registering plugin commands from functions."""

    def test_func():
        pass

    mock_get_commands.return_value = {"test-func": test_func}

    # Remove existing command if present
    if "test-func" in cli.commands:
        del cli.commands["test-func"]

    register_plugin_commands()

    # Check that command was added
    commands_list = list(cli.commands.keys())
    assert "test-func" in commands_list


@patch("maestria.cli.run_hook")
@patch("maestria.cli.register_plugin_commands")
def test_main_success(mock_register, mock_hook):
    """Test main function success."""
    with patch("maestria.cli.cli"):
        result = main()
        assert result == 0
        mock_register.assert_called_once()
        assert mock_hook.call_count == 2


@patch("maestria.cli.register_plugin_commands")
def test_main_exception(mock_register):
    """Test main function with exception."""
    mock_register.side_effect = Exception("Test error")
    result = main()
    assert result == 1


def test_print_version_callback():
    """Test print_version callback."""
    ctx = Mock()
    ctx.resilient_parsing = False
    param = Mock()

    print_version(ctx, param, True)
    ctx.exit.assert_called_once()


def test_print_version_callback_no_value():
    """Test print_version callback when value is False."""
    ctx = Mock()
    param = Mock()

    result = print_version(ctx, param, False)
    assert result is None
    ctx.exit.assert_not_called()
