"""Unit tests for RED9 configuration."""

from __future__ import annotations

from pathlib import Path

from red9.config.schema import ProviderConfig, Red9Config


class TestProviderConfig:
    """Tests for ProviderConfig."""

    def test_default_values(self) -> None:
        """Test default provider configuration."""
        config = ProviderConfig()

        assert config.type == "ollama"
        assert config.base_url == "http://localhost:11434"
        assert config.timeout == 120

    def test_custom_values(self) -> None:
        """Test custom provider configuration."""
        config = ProviderConfig(
            type="ollama",
            base_url="http://custom:11434",
            model="codellama:7b",
            timeout=300,
        )

        assert config.base_url == "http://custom:11434"
        assert config.model == "codellama:7b"
        assert config.timeout == 300


class TestRed9Config:
    """Tests for Red9Config."""

    def test_default_values(self) -> None:
        """Test default configuration."""
        config = Red9Config()

        assert config.version == "1"  # version is a string
        assert config.provider is not None
        assert config.approval_mode == "default"

    def test_from_dict(self) -> None:
        """Test creating config from dictionary."""
        data = {
            "version": "1",  # version is a string
            "provider": {
                "type": "ollama",
                "model": "llama3.1:8b",
            },
            "approval_mode": "auto",
        }

        config = Red9Config(**data)

        assert config.provider.model == "llama3.1:8b"
        assert config.approval_mode == "auto"


class TestPathValidation:
    """Tests for path validation in base module."""

    def test_validate_path_within_project(self, temp_dir: Path) -> None:
        """Test validating paths within project root."""
        from red9.tools.base import set_project_root, validate_path

        set_project_root(temp_dir)

        # Create a test file
        test_file = temp_dir / "test.py"
        test_file.write_text("# test")

        path, error = validate_path(str(test_file), must_exist=True)

        assert path is not None
        assert error is None
        assert path == test_file.resolve()

    def test_validate_path_outside_project(self, temp_dir: Path) -> None:
        """Test that paths outside project are blocked."""
        from red9.tools.base import set_project_root, validate_path

        set_project_root(temp_dir)

        path, error = validate_path("/etc/passwd", must_exist=False)

        assert path is None
        assert error is not None
        assert "outside" in error.lower() or "denied" in error.lower()

    def test_validate_path_sensitive_paths(self, temp_dir: Path) -> None:
        """Test that sensitive paths are blocked."""
        from red9.tools.base import set_project_root, validate_path

        # Set project root to / to test sensitive path blocking
        set_project_root(Path("/"))

        sensitive_paths = [
            "/etc/shadow",
            "/home/user/.ssh/id_rsa",
            "/home/user/.aws/credentials",
        ]

        for sensitive_path in sensitive_paths:
            path, error = validate_path(sensitive_path, must_exist=False)
            assert path is None, f"Should block: {sensitive_path}"
            assert error is not None

        # Reset project root
        set_project_root(temp_dir)

    def test_validate_path_nonexistent_required(self, temp_dir: Path) -> None:
        """Test validation when file must exist but doesn't."""
        from red9.tools.base import set_project_root, validate_path

        set_project_root(temp_dir)

        path, error = validate_path(
            str(temp_dir / "nonexistent.py"),
            must_exist=True,
        )

        assert path is None
        assert error is not None
        assert "not found" in error.lower()

    def test_validate_relative_path(self, temp_dir: Path) -> None:
        """Test validating relative paths."""
        from red9.tools.base import set_project_root, validate_path

        set_project_root(temp_dir)

        # Create a file
        (temp_dir / "relative.py").write_text("# test")

        path, error = validate_path("relative.py", must_exist=True)

        assert path is not None
        assert error is None
        assert path == (temp_dir / "relative.py").resolve()
