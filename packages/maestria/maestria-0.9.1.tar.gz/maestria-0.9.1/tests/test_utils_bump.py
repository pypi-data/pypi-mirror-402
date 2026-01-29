import os
import subprocess
import sys
from unittest.mock import patch

import pytest

from maestria.utils.bump import bump_version, main


class TestBumpVersion:

    def test_bump_version_success(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        pyproject_initial = project_dir / "pyproject.toml"
        pyproject_initial.write_text('[project]\nversion = "1.0.0"\n')

        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        bump_bin = venv_bin / (
            "bump2version.exe" if sys.platform == "win32" else "bump2version"
        )
        bump_bin.touch()

        def mock_run(cmd, **kwargs):
            pyproject_initial.write_text('[project]\nversion = "1.0.1"\n')
            return subprocess.CompletedProcess(cmd, 0)

        with patch("subprocess.run", side_effect=mock_run):
            result = bump_version(project_dir, venv_path, "patch", verbose=False)

            assert result is not None
            old_version, new_version = result
            assert old_version == "1.0.0"
            assert new_version == "1.0.1"

    def test_bump_version_missing_tool(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        result = bump_version(project_dir, venv_path, "patch", verbose=False)

        assert result is None

    def test_bump_version_subprocess_error(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        pyproject_initial = project_dir / "pyproject.toml"
        pyproject_initial.write_text('[project]\nversion = "1.0.0"\n')

        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        bump_bin = venv_bin / (
            "bump2version.exe" if sys.platform == "win32" else "bump2version"
        )
        bump_bin.touch()

        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "bump2version"),
        ):
            result = bump_version(project_dir, venv_path, "patch", verbose=False)

            assert result is None

    def test_bump_version_verbose_mode(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        pyproject_initial = project_dir / "pyproject.toml"
        pyproject_initial.write_text('[project]\nversion = "2.5.0"\n')

        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        bump_bin = venv_bin / (
            "bump2version.exe" if sys.platform == "win32" else "bump2version"
        )
        bump_bin.touch()

        def mock_run(cmd, **kwargs):
            pyproject_initial.write_text('[project]\nversion = "3.0.0"\n')
            return subprocess.CompletedProcess(cmd, 0)

        with patch("subprocess.run", side_effect=mock_run) as mock_run_fn:
            result = bump_version(project_dir, venv_path, "major", verbose=True)

            assert result is not None
            old_version, new_version = result
            assert old_version == "2.5.0"
            assert new_version == "3.0.0"

            call_kwargs = mock_run_fn.call_args[1]
            assert (
                "stdout" not in call_kwargs
                or call_kwargs.get("stdout") != subprocess.PIPE
            )

    def test_bump_version_minor(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        pyproject_initial = project_dir / "pyproject.toml"
        pyproject_initial.write_text('[project]\nversion = "1.2.3"\n')

        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        bump_bin = venv_bin / (
            "bump2version.exe" if sys.platform == "win32" else "bump2version"
        )
        bump_bin.touch()

        def mock_run(cmd, **kwargs):
            pyproject_initial.write_text('[project]\nversion = "1.3.0"\n')
            return subprocess.CompletedProcess(cmd, 0)

        with patch("subprocess.run", side_effect=mock_run):
            result = bump_version(project_dir, venv_path, "minor", verbose=False)

            assert result is not None
            old_version, new_version = result
            assert old_version == "1.2.3"
            assert new_version == "1.3.0"

    def test_bump_version_windows_exe_fallback(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        pyproject_initial = project_dir / "pyproject.toml"
        pyproject_initial.write_text('[project]\nversion = "1.0.0"\n')

        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / "Scripts"
        venv_bin.mkdir(parents=True)
        bump_bin = venv_bin / "bump2version"
        bump_bin.touch()

        def mock_run(cmd, **kwargs):
            pyproject_initial.write_text('[project]\nversion = "1.0.1"\n')
            return subprocess.CompletedProcess(cmd, 0)

        with patch("sys.platform", "win32"):
            with patch("subprocess.run", side_effect=mock_run):
                result = bump_version(project_dir, venv_path, "patch", verbose=False)

                assert result is not None

    def test_bump_version_no_version_in_pyproject(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        pyproject_initial = project_dir / "pyproject.toml"
        pyproject_initial.write_text('[project]\nname = "test"\n')

        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        bump_bin = venv_bin / (
            "bump2version.exe" if sys.platform == "win32" else "bump2version"
        )
        bump_bin.touch()

        with patch("subprocess.run"):
            result = bump_version(project_dir, venv_path, "patch", verbose=False)

            assert result is None


class TestMain:

    def test_main_success(self, tmp_path, monkeypatch, capsys):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        pyproject_initial = project_dir / "pyproject.toml"
        pyproject_initial.write_text('[project]\nversion = "1.0.0"\n')

        # Create .venv inside project_dir since VENV_PATH env var was removed
        venv_path = project_dir / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        bump_bin = venv_bin / (
            "bump2version.exe" if sys.platform == "win32" else "bump2version"
        )
        bump_bin.touch()

        orig_cwd = os.getcwd()
        try:
            os.chdir(project_dir)
            monkeypatch.setattr("sys.argv", ["bump.py", "patch"])

            def mock_run(cmd, **kwargs):
                pyproject_initial.write_text('[project]\nversion = "1.0.1"\n')
                return subprocess.CompletedProcess(cmd, 0)

            with patch("subprocess.run", side_effect=mock_run):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert "BUMP_RESULT:1.0.0:1.0.1" in captured.out
        finally:
            os.chdir(orig_cwd)

    def test_main_failure(self, tmp_path, monkeypatch):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        orig_cwd = os.getcwd()
        try:
            os.chdir(project_dir)
            monkeypatch.setenv("VENV_PATH", str(venv_path))
            monkeypatch.setattr("sys.argv", ["bump.py", "minor"])

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
        finally:
            os.chdir(orig_cwd)

    def test_main_verbose_mode(self, tmp_path, monkeypatch, capsys):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        pyproject_initial = project_dir / "pyproject.toml"
        pyproject_initial.write_text('[project]\nversion = "0.5.0"\n')

        # Create .venv inside project_dir since VENV_PATH env var was removed
        venv_path = project_dir / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        bump_bin = venv_bin / (
            "bump2version.exe" if sys.platform == "win32" else "bump2version"
        )
        bump_bin.touch()

        orig_cwd = os.getcwd()
        try:
            os.chdir(project_dir)
            monkeypatch.setenv("MAESTRIA_VERBOSE", "1")
            monkeypatch.setattr("sys.argv", ["bump.py", "major"])

            def mock_run(cmd, **kwargs):
                pyproject_initial.write_text('[project]\nversion = "1.0.0"\n')
                return subprocess.CompletedProcess(cmd, 0)

            with patch("subprocess.run", side_effect=mock_run):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 0
        finally:
            os.chdir(orig_cwd)

    def test_main_with_different_bump_types(self, tmp_path, monkeypatch):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        venv_path = tmp_path / ".venv"

        orig_cwd = os.getcwd()
        try:
            os.chdir(project_dir)
            monkeypatch.setenv("VENV_PATH", str(venv_path))

            for bump_type in ["patch", "minor", "major"]:
                monkeypatch.setattr("sys.argv", ["bump.py", bump_type])

                try:
                    main()
                except SystemExit:
                    pass
        finally:
            os.chdir(orig_cwd)
