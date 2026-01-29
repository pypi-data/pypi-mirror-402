"""Tests for package installer utilities."""

import os
import subprocess
import sys
from unittest.mock import patch

import pytest

from maestria.utils.installer import install_dependencies, main


class TestInstallDependencies:

    def test_python_not_found(self, tmp_path):
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"

        result = install_dependencies(project_dir, venv_path)

        assert result is False

    def test_specific_dependencies_with_uv_success(self, tmp_path):
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        with patch("shutil.which", return_value="/usr/bin/uv"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0)

                result = install_dependencies(
                    project_dir,
                    venv_path,
                    dependencies=["pytest", "black"],
                    verbose=False,
                )

                assert result is True
                assert mock_run.call_count >= 2

    def test_specific_dependencies_with_uv_failure(self, tmp_path):
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        with patch("shutil.which", return_value="/usr/bin/uv"):
            call_count = [0]

            def mock_run_side_effect(cmd, **kwargs):
                call_count[0] += 1
                if call_count[0] > 1:
                    raise subprocess.CalledProcessError(1, cmd)
                return subprocess.CompletedProcess(cmd, 0)

            with patch("subprocess.run", side_effect=mock_run_side_effect):
                result = install_dependencies(
                    project_dir, venv_path, dependencies=["pytest"], verbose=False
                )

                assert result is False

    def test_install_from_pyproject_with_uv(self, tmp_path):
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        with patch("shutil.which", return_value="/usr/bin/uv"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0)

                result = install_dependencies(
                    project_dir, venv_path, dependencies=None, dev=False, verbose=False
                )

                assert result is True

    def test_install_dev_dependencies_with_uv(self, tmp_path):
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        with patch("shutil.which", return_value="/usr/bin/uv"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0)

                result = install_dependencies(
                    project_dir, venv_path, dev=True, verbose=False
                )

                assert result is True

    def test_install_with_update_flag(self, tmp_path):
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        with patch("shutil.which", return_value="/usr/bin/uv"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0)

                result = install_dependencies(
                    project_dir, venv_path, update=True, verbose=False
                )

                assert result is True

    def test_install_without_uv_fails(self, tmp_path):
        """Test that installation fails when UV is not available."""
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        with patch("shutil.which", return_value=None):
            result = install_dependencies(project_dir, venv_path, verbose=False)

            assert result is False

    def test_install_specific_deps_without_uv_fails(self, tmp_path):
        """Test that specific dependency installation fails when UV is not available."""
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        with patch("shutil.which", return_value=None):
            result = install_dependencies(
                project_dir, venv_path, dependencies=["pytest"], verbose=False
            )

            assert result is False

    def test_verbose_mode(self, tmp_path):
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        with patch("shutil.which", return_value="/usr/bin/uv"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0)

                result = install_dependencies(project_dir, venv_path, verbose=True)

                assert result is True


class TestMain:

    def test_main_success(self, tmp_path, monkeypatch, capsys):
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        orig_cwd = os.getcwd()
        try:
            os.chdir(project_dir)
            monkeypatch.setenv("VENV_PATH", str(venv_path))
            monkeypatch.setattr("sys.argv", ["installer.py"])

            with patch("shutil.which", return_value="/usr/bin/uv"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = subprocess.CompletedProcess([], 0)

                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 0
        finally:
            os.chdir(orig_cwd)

    def test_main_failure(self, tmp_path, monkeypatch):
        venv_path = tmp_path / ".venv"

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            monkeypatch.setenv("VENV_PATH", str(venv_path))
            monkeypatch.setattr("sys.argv", ["installer.py"])

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
        finally:
            os.chdir(orig_cwd)

    def test_main_dev_mode(self, tmp_path, monkeypatch):
        project_dir = tmp_path
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        python_bin = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
        python_bin.touch()

        orig_cwd = os.getcwd()
        try:
            os.chdir(project_dir)
            monkeypatch.setenv("VENV_PATH", str(venv_path))
            monkeypatch.setattr("sys.argv", ["installer.py", "--dev"])

            with patch("shutil.which", return_value="/usr/bin/uv"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = subprocess.CompletedProcess([], 0)

                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 0
        finally:
            os.chdir(orig_cwd)
