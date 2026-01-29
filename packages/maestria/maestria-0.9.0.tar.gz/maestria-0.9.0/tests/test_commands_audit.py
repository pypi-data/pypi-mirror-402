"""Tests for the audit command."""

from pathlib import Path
from unittest.mock import Mock, patch

from maestria.commands.audit import (
    _run_bandit,
    _run_pip_audit,
    run_audit,
)


class TestRunAudit:
    """Tests for the run_audit function."""

    @patch("maestria.commands.audit._run_bandit")
    @patch("maestria.commands.audit._run_pip_audit")
    @patch("maestria.commands.audit.activate_environment")
    @patch("maestria.commands.audit.console")
    def test_run_audit_success(
        self, mock_console, mock_activate, mock_pip_audit, mock_bandit
    ):
        """Test successful audit."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_pip_audit.return_value = False
        mock_bandit.return_value = False

        run_audit(mock_config)

        mock_pip_audit.assert_called_once()
        mock_bandit.assert_called_once()
        assert any(
            "completed successfully" in str(call).lower()
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.audit._run_bandit")
    @patch("maestria.commands.audit._run_pip_audit")
    @patch("maestria.commands.audit.activate_environment")
    @patch("maestria.commands.audit.console")
    def test_run_audit_with_errors(
        self, mock_console, mock_activate, mock_pip_audit, mock_bandit
    ):
        """Test audit with errors found."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_pip_audit.return_value = True
        mock_bandit.return_value = False

        run_audit(mock_config)

        assert not any(
            "completed successfully" in str(call).lower()
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.audit._run_bandit")
    @patch("maestria.commands.audit._run_pip_audit")
    @patch("maestria.commands.audit.activate_environment")
    @patch("maestria.commands.audit.console")
    def test_run_audit_code_only(
        self, mock_console, mock_activate, mock_pip_audit, mock_bandit
    ):
        """Test audit with code-only flag."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_bandit.return_value = False

        run_audit(mock_config, code_only=True)

        mock_pip_audit.assert_not_called()
        mock_bandit.assert_called_once()

    @patch("maestria.commands.audit._run_bandit")
    @patch("maestria.commands.audit._run_pip_audit")
    @patch("maestria.commands.audit.activate_environment")
    @patch("maestria.commands.audit.console")
    def test_run_audit_deps_only(
        self, mock_console, mock_activate, mock_pip_audit, mock_bandit
    ):
        """Test audit with deps-only flag."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_pip_audit.return_value = False

        run_audit(mock_config, deps_only=True)

        mock_pip_audit.assert_called_once()
        mock_bandit.assert_not_called()

    @patch("maestria.commands.audit.activate_environment")
    @patch("maestria.commands.audit.console")
    def test_run_audit_env_activation_failure(self, mock_console, mock_activate):
        """Test audit when environment activation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.side_effect = RuntimeError("Venv not found")

        run_audit(mock_config)

        assert any("Error" in str(call) for call in mock_console.print.call_args_list)


class TestRunPipAudit:
    """Tests for the _run_pip_audit function."""

    @patch("maestria.commands.audit.run_in_environment")
    @patch("maestria.commands.audit.console")
    def test_run_pip_audit_no_vulnerabilities(self, mock_console, mock_run):
        """Test pip-audit with no vulnerabilities."""
        mock_run.return_value = Mock(returncode=0)

        result = _run_pip_audit(Path("/path/to/project"), venv_path=None, verbose=False)

        assert result is False
        assert any(
            "No known vulnerabilities" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.audit.run_in_environment")
    @patch("maestria.commands.audit.console")
    def test_run_pip_audit_with_vulnerabilities(self, mock_console, mock_run):
        """Test pip-audit with vulnerabilities found."""
        mock_run.return_value = Mock(returncode=1)

        result = _run_pip_audit(Path("/path/to/project"), venv_path=None, verbose=False)

        assert result is True
        assert any(
            "Vulnerabilities found" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.audit.run_in_environment")
    @patch("maestria.commands.audit.console")
    def test_run_pip_audit_failure(self, mock_console, mock_run):
        """Test pip-audit when it fails to run."""
        mock_run.side_effect = Exception("pip-audit not found")

        result = _run_pip_audit(Path("/path/to/project"), venv_path=None, verbose=False)

        assert result is False
        assert any(
            "failed" in str(call).lower() for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.audit.run_in_environment")
    @patch("maestria.commands.audit.console")
    def test_run_pip_audit_verbose(self, mock_console, mock_run):
        """Test pip-audit in verbose mode."""
        mock_run.return_value = Mock(returncode=0)

        _run_pip_audit(Path("/path/to/project"), venv_path=None, verbose=True)

        mock_run.assert_called_once()


class TestRunBandit:
    """Tests for the _run_bandit function."""

    @patch("maestria.commands.audit.run_in_environment")
    @patch("maestria.commands.audit.console")
    @patch("pathlib.Path.exists")
    def test_run_bandit_no_issues(self, mock_exists, mock_console, mock_run):
        """Test bandit with no security issues."""
        mock_exists.return_value = False
        mock_run.return_value = Mock(returncode=0)

        result = _run_bandit(Path("/path/to/project"), venv_path=None, verbose=False)

        assert result is False
        assert any(
            "No security issues" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.audit.run_in_environment")
    @patch("maestria.commands.audit.console")
    @patch("pathlib.Path.exists")
    def test_run_bandit_with_issues(self, mock_exists, mock_console, mock_run):
        """Test bandit with security issues found."""
        mock_exists.return_value = False
        mock_run.return_value = Mock(returncode=1)

        result = _run_bandit(Path("/path/to/project"), venv_path=None, verbose=False)

        assert result is True
        assert any(
            "Security issues found" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.audit.run_in_environment")
    @patch("maestria.commands.audit.console")
    @patch("pathlib.Path.exists")
    def test_run_bandit_with_src_dir(self, mock_exists, mock_console, mock_run):
        """Test bandit with src directory."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0)

        _run_bandit(Path("/path/to/project"), venv_path=None, verbose=False)

        call_args = mock_run.call_args[0][0]
        assert "src" in call_args

    @patch("maestria.commands.audit.run_in_environment")
    @patch("maestria.commands.audit.console")
    def test_run_bandit_failure(self, mock_console, mock_run):
        """Test bandit when it fails to run."""
        mock_run.side_effect = Exception("bandit not found")

        result = _run_bandit(Path("/path/to/project"), venv_path=None, verbose=False)

        assert result is False
        assert any(
            "skipping" in str(call).lower()
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.audit.run_in_environment")
    @patch("maestria.commands.audit.console")
    @patch("pathlib.Path.exists")
    def test_run_bandit_verbose(self, mock_exists, mock_console, mock_run):
        """Test bandit in verbose mode."""
        mock_exists.return_value = False
        mock_run.return_value = Mock(returncode=0)

        _run_bandit(Path("/path/to/project"), venv_path=None, verbose=True)

        mock_run.assert_called_once()
