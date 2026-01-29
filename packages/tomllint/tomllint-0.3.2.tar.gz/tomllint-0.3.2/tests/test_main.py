"""Tests for tomllint."""

import subprocess
import sys
from pathlib import Path

import pytest

TOMLLINT_CMD = [sys.executable, "-m", "tomllint.main"]


@pytest.fixture
def valid_toml(tmp_path: Path) -> Path:
    """Create a temporary valid TOML file."""
    f = tmp_path / "valid.toml"
    f.write_text('[section]\nkey = "value"\nnumber = 42\n')
    return f


@pytest.fixture
def invalid_toml(tmp_path: Path) -> Path:
    """Create a temporary invalid TOML file."""
    f = tmp_path / "invalid.toml"
    f.write_text('key = "unclosed string\n')
    return f


@pytest.fixture
def another_valid_toml(tmp_path: Path) -> Path:
    """Create another temporary valid TOML file."""
    f = tmp_path / "another_valid.toml"
    f.write_text("name = 'test'\nenabled = true\n")
    return f


class TestValidToml:
    """Tests for valid TOML files."""

    def test_valid_file_returns_zero(self, valid_toml: Path) -> None:
        """Valid TOML file should return exit code 0."""
        result = subprocess.run(
            [*TOMLLINT_CMD, str(valid_toml)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stderr == ""

    def test_pyproject_toml_is_valid(self) -> None:
        """The project's own pyproject.toml should be valid."""
        result = subprocess.run(
            [*TOMLLINT_CMD, "pyproject.toml"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestInvalidToml:
    """Tests for invalid TOML files."""

    def test_invalid_file_returns_one(self, invalid_toml: Path) -> None:
        """Invalid TOML file should return exit code 1."""
        result = subprocess.run(
            [*TOMLLINT_CMD, str(invalid_toml)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_error_format(self, invalid_toml: Path) -> None:
        """Error message should follow format: filename:line:col: error: message."""
        result = subprocess.run(
            [*TOMLLINT_CMD, str(invalid_toml)],
            capture_output=True,
            text=True,
        )
        # Error format: filename:line:col: error: message
        assert str(invalid_toml) in result.stderr
        assert ":1:" in result.stderr  # line 1
        assert ": error:" in result.stderr


class TestStdin:
    """Tests for stdin input."""

    def test_stdin_valid_toml(self) -> None:
        """Valid TOML from stdin should return exit code 0."""
        result = subprocess.run(
            [*TOMLLINT_CMD, "-"],
            input='key = "value"\n',
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_stdin_invalid_toml(self) -> None:
        """Invalid TOML from stdin should return exit code 1."""
        result = subprocess.run(
            [*TOMLLINT_CMD, "-"],
            input='key = "unclosed\n',
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_stdin_error_shows_stdin_filename(self) -> None:
        """Error from stdin should show <stdin> as filename."""
        result = subprocess.run(
            [*TOMLLINT_CMD, "-"],
            input='key = "unclosed\n',
            capture_output=True,
            text=True,
        )
        assert "<stdin>:" in result.stderr


class TestMultipleFiles:
    """Tests for multiple file handling."""

    def test_multiple_valid_files(self, valid_toml: Path, another_valid_toml: Path) -> None:
        """Multiple valid files should return exit code 0."""
        result = subprocess.run(
            [*TOMLLINT_CMD, str(valid_toml), str(another_valid_toml)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_one_invalid_among_valid(
        self, valid_toml: Path, invalid_toml: Path, another_valid_toml: Path
    ) -> None:
        """If any file is invalid, return exit code 1."""
        result = subprocess.run(
            [*TOMLLINT_CMD, str(valid_toml), str(invalid_toml), str(another_valid_toml)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1


class TestErrorHandling:
    """Tests for error handling."""

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """Nonexistent file should cause an error."""
        nonexistent = tmp_path / "does_not_exist.toml"
        result = subprocess.run(
            [*TOMLLINT_CMD, str(nonexistent)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
