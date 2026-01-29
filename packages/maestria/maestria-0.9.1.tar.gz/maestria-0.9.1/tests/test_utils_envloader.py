"""Tests for environment loader utilities."""

import os
import subprocess
import sys
from unittest.mock import patch

import pytest

from maestria.utils.envloader import load_and_validate_env, main


class TestLoadAndValidateEnv:

    def test_venv_not_exists(self, tmp_path):
        venv_path = tmp_path / ".venv"

        result = load_and_validate_env(tmp_path, venv_path, verbose=False)

        assert result is False

    def test_python_not_exists(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_path.mkdir()

        result = load_and_validate_env(tmp_path, venv_path, verbose=False)

        assert result is False

    def test_all_dependencies_present(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0)

        with patch("subprocess.run", side_effect=mock_run):
            result = load_and_validate_env(tmp_path, venv_path, verbose=False)

            assert result is True

    def test_missing_dependencies_install_with_uv(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        call_count = [0]

        def mock_run(cmd, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 4:
                raise subprocess.CalledProcessError(1, cmd)
            return subprocess.CompletedProcess(cmd, 0)

        with patch("subprocess.run", side_effect=mock_run):
            with patch("shutil.which", return_value="/usr/bin/uv"):
                result = load_and_validate_env(tmp_path, venv_path, verbose=False)

                assert result is True

    def test_missing_dependencies_install_with_pip(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        call_count = [0]

        def mock_run(cmd, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 4:
                raise subprocess.CalledProcessError(1, cmd)
            return subprocess.CompletedProcess(cmd, 0)

        with patch("subprocess.run", side_effect=mock_run):
            with patch("shutil.which", return_value=None):
                result = load_and_validate_env(tmp_path, venv_path, verbose=False)

                assert result is True

    def test_failed_to_install_dependencies(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        def mock_run(cmd, **kwargs):
            raise subprocess.CalledProcessError(1, cmd)

        with patch("subprocess.run", side_effect=mock_run):
            with patch("shutil.which", return_value=None):
                result = load_and_validate_env(tmp_path, venv_path, verbose=False)

                assert result is False

    def test_verbose_mode(self, tmp_path, caplog):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0)

        with patch("subprocess.run", side_effect=mock_run):
            result = load_and_validate_env(tmp_path, venv_path, verbose=True)

            assert result is True

    def test_windows_paths(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / "Scripts"
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / "python.exe"
        python_bin.touch()

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0)

        with patch("sys.platform", "win32"):
            with patch("subprocess.run", side_effect=mock_run):
                result = load_and_validate_env(tmp_path, venv_path, verbose=False)

                assert result is True


class TestMain:

    def test_main_success(self, tmp_path, monkeypatch, capsys):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        monkeypatch.setenv("VENV_PATH", str(venv_path))

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0)

        with patch("subprocess.run", side_effect=mock_run):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert "Environment ready" in captured.out

    def test_main_failure(self, tmp_path, monkeypatch):
        venv_path = tmp_path / ".venv"

        monkeypatch.setenv("VENV_PATH", str(venv_path))

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_verbose_mode(self, tmp_path, monkeypatch, capsys):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        monkeypatch.setenv("VENV_PATH", str(venv_path))
        monkeypatch.setenv("MAESTRIA_VERBOSE", "1")

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0)

        with patch("subprocess.run", side_effect=mock_run):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

    def test_main_default_venv_path(self, tmp_path, capsys):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            def mock_run(cmd, **kwargs):
                return subprocess.CompletedProcess(cmd, 0)

            with patch("subprocess.run", side_effect=mock_run):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 0
        finally:
            os.chdir(orig_cwd)
