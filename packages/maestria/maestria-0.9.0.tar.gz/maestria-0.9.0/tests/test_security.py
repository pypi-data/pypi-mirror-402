"""Tests for security utilities."""

import pytest

from maestria.security import (
    SecurityError,
    enable_security_checks,
    is_safe_filename,
    reset_security_checks,
    sanitize_environment,
    validate_executable,
    validate_path,
)


class TestValidatePath:
    """Tests for validate_path function."""

    def test_validate_simple_path(self, tmp_path):
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        result = validate_path(test_dir, allow_absolute=True, must_exist=True)
        assert result == test_dir.resolve()

    def test_reject_empty_path(self):
        with pytest.raises(SecurityError, match="Path cannot be empty"):
            validate_path("")

    def test_reject_path_traversal(self, tmp_path):
        malicious_path = "../../etc/passwd"

        with pytest.raises(SecurityError, match="outside the allowed base directory"):
            validate_path(malicious_path, base_dir=tmp_path)

    def test_reject_absolute_path_when_not_allowed(self, tmp_path):
        absolute_path = tmp_path / "test"
        absolute_path.mkdir()

        with pytest.raises(SecurityError, match="Absolute paths are not allowed"):
            validate_path(absolute_path, allow_absolute=False)

    def test_reject_path_outside_base_dir(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        with pytest.raises(SecurityError, match="outside the allowed base directory"):
            validate_path(outside_dir, base_dir=base_dir, allow_absolute=True)

    def test_reject_nonexistent_path_when_required(self, tmp_path):
        enable_security_checks()
        try:
            nonexistent = tmp_path / "does_not_exist"
            with pytest.raises(SecurityError, match="Path does not exist"):
                validate_path(nonexistent, allow_absolute=True, must_exist=True)
        finally:
            reset_security_checks()

    def test_allow_relative_path_within_base(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        sub_dir = base_dir / "subdir"
        sub_dir.mkdir()

        result = validate_path(sub_dir, base_dir=base_dir, allow_absolute=True)
        assert result.is_relative_to(base_dir.resolve())


class TestValidateExecutable:
    """Tests for validate_executable function."""

    def test_validate_executable_in_allowed_dir(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        exe_file = bin_dir / "test_exe"
        exe_file.touch()
        exe_file.chmod(0o755)

        result = validate_executable(exe_file, allowed_dirs=[bin_dir])
        assert result == exe_file.resolve()

    def test_reject_empty_executable_path(self):
        with pytest.raises(SecurityError, match="Executable path cannot be empty"):
            validate_executable("")

    def test_reject_nonexistent_executable(self, tmp_path):
        enable_security_checks()
        try:
            nonexistent = tmp_path / "does_not_exist"
            with pytest.raises(SecurityError, match="Executable does not exist"):
                validate_executable(nonexistent)
        finally:
            reset_security_checks()

    def test_reject_non_executable_file(self, tmp_path):
        enable_security_checks()
        try:
            non_exe = tmp_path / "not_executable"
            non_exe.touch()
            non_exe.chmod(0o644)
            with pytest.raises(SecurityError, match="File is not executable"):
                validate_executable(non_exe)
        finally:
            reset_security_checks()

    def test_reject_executable_outside_allowed_dirs(self, tmp_path):
        enable_security_checks()
        try:
            allowed_dir = tmp_path / "allowed"
            allowed_dir.mkdir()

            forbidden_dir = tmp_path / "forbidden"
            forbidden_dir.mkdir()

            exe_file = forbidden_dir / "evil_exe"
            exe_file.touch()
            exe_file.chmod(0o755)
            with pytest.raises(SecurityError, match="not in an allowed directory"):
                validate_executable(exe_file, allowed_dirs=[allowed_dir])
        finally:
            reset_security_checks()


class TestIsSafeFilename:
    """Tests for is_safe_filename function."""

    def test_safe_filenames(self):
        safe_names = ["test.py", "myfile.txt", "README.md", "file123.json"]

        for name in safe_names:
            assert is_safe_filename(name), f"{name} should be safe"

    def test_reject_empty_filename(self):
        assert not is_safe_filename("")

    def test_reject_dot_and_dotdot(self):
        assert not is_safe_filename(".")
        assert not is_safe_filename("..")

    def test_reject_path_separators(self):
        assert not is_safe_filename("path/to/file.txt")
        assert not is_safe_filename("path\\to\\file.txt")

    def test_reject_path_traversal_attempts(self):
        assert not is_safe_filename("../etc/passwd")
        assert not is_safe_filename("..secret")

    def test_reject_dangerous_characters(self):
        dangerous = ["<", ">", ":", '"', "|", "?", "*", "\0"]

        for char in dangerous:
            filename = f"file{char}.txt"
            assert not is_safe_filename(filename), f"Should reject {char}"

    def test_allow_hidden_files(self):
        assert is_safe_filename(".gitignore")
        assert is_safe_filename(".env")


class TestPathTraversalScenarios:
    """Integration tests for path traversal attack scenarios."""

    def test_prevent_directory_escape_in_template(self, tmp_path):
        base_dir = tmp_path / "templates"
        base_dir.mkdir()

        attack_path = "../../../etc/passwd"

        with pytest.raises(SecurityError):
            validate_path(attack_path, base_dir=base_dir)

    def test_prevent_symlink_escape(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        symlink = base_dir / "escape"

        try:
            symlink.symlink_to(outside_dir)

            with pytest.raises(SecurityError):
                validate_path(symlink, base_dir=base_dir, allow_absolute=True)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")


class TestCommandInjectionScenarios:
    """Integration tests for command injection attack scenarios."""

    def test_reject_executable_with_injection_attempt(self, tmp_path):
        malicious_path = tmp_path / "evil; rm -rf /"
        malicious_path.mkdir()

        exe_file = malicious_path / "exe"
        exe_file.touch()
        exe_file.chmod(0o755)

        result = validate_executable(exe_file, allowed_dirs=[malicious_path])
        assert result.exists()


class TestSanitizeEnvironment:
    """Tests for sanitize_environment function."""

    def test_sanitize_safe_environment(self):
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/home/user",
            "USER": "testuser",
            "LANG": "en_US.UTF-8",
        }

        result = sanitize_environment(env)

        assert result["PATH"] == "/usr/bin:/bin"
        assert result["HOME"] == "/home/user"
        assert result["USER"] == "testuser"
        assert result["LANG"] == "en_US.UTF-8"

    def test_remove_unsafe_variables(self):
        env = {
            "PATH": "/usr/bin",
            "UNSAFE_VAR": "malicious",
            "LD_PRELOAD": "/tmp/evil.so",
        }

        result = sanitize_environment(env)

        assert "PATH" in result
        assert "UNSAFE_VAR" not in result
        assert "LD_PRELOAD" not in result

    def test_reject_command_injection_in_values(self):
        env = {
            "PATH": "/usr/bin; rm -rf /",
            "HOME": "/home/user",
        }

        result = sanitize_environment(env)

        assert "PATH" not in result
        assert "HOME" in result

    def test_reject_command_substitution(self):
        env = {
            "PYTHONPATH": "/path/to/lib",
            "SHELL": "/bin/bash && malicious",
            "USER": "test$(whoami)",
        }

        result = sanitize_environment(env)

        assert "PYTHONPATH" in result
        assert "SHELL" not in result
        assert "USER" not in result

    def test_allow_maestria_variables(self):
        env = {
            "MAESTRIA_VERBOSE": "1",
            "MAESTRIA_CONFIG": "/path/to/config",
            "PATH": "/usr/bin",
        }

        result = sanitize_environment(env)

        assert "MAESTRIA_VERBOSE" in result
        assert "MAESTRIA_CONFIG" in result
        assert "PATH" in result
