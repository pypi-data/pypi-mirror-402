"""Unit tests for the Harness class."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from ralph.harness import Harness, HarnessDetector, HarnessType, DEFAULT_MODELS


class TestHarnessDataclass:
    """Tests for the Harness dataclass fields."""

    def test_harness_creation_with_all_fields(self) -> None:
        """Test creating a Harness with all required fields."""
        harness = Harness(name="claude", path="/usr/bin/claude", type="claude")

        assert harness.name == "claude"
        assert harness.path == "/usr/bin/claude"
        assert harness.type == "claude"

    def test_harness_type_literal(self) -> None:
        """Test that harness type accepts all valid literals."""
        types: list[HarnessType] = ["claude", "codex", "custom"]
        for harness_type in types:
            harness = Harness(name="test", path="/bin/test", type=harness_type)
            assert harness.type == harness_type


class TestIsAvailable:
    """Tests for the is_available property."""

    def test_is_available_with_existing_executable(self, tmp_path: Path) -> None:
        """Test is_available returns True for existing executable file."""
        # Create a temporary executable file
        exe_path = tmp_path / "test_harness"
        exe_path.write_text("#!/bin/bash\necho test")
        exe_path.chmod(0o755)

        harness = Harness(name="test", path=str(exe_path), type="custom")
        assert harness.is_available is True

    def test_is_available_with_nonexistent_path(self) -> None:
        """Test is_available returns False for non-existent path."""
        harness = Harness(
            name="nonexistent",
            path="/nonexistent/path/to/harness",
            type="custom",
        )
        assert harness.is_available is False

    def test_is_available_with_non_executable_file(self, tmp_path: Path) -> None:
        """Test is_available returns False for non-executable file."""
        # Create a file without execute permission
        file_path = tmp_path / "non_executable"
        file_path.write_text("not executable")
        file_path.chmod(0o644)

        harness = Harness(name="test", path=str(file_path), type="custom")
        assert harness.is_available is False

    def test_is_available_with_command_on_path(self) -> None:
        """Test is_available with a command that should be on PATH."""
        # 'python' or 'python3' should be available on most systems
        harness = Harness(name="python", path="python3", type="custom")
        # This might fail in some environments, but should work in dev
        assert harness.is_available is True

    def test_is_available_with_command_not_on_path(self) -> None:
        """Test is_available with a command not on PATH."""
        harness = Harness(
            name="nonexistent",
            path="definitely_not_a_real_command_12345",
            type="custom",
        )
        assert harness.is_available is False


class TestGetSupportedModels:
    """Tests for the get_supported_models method."""

    def test_get_supported_models_claude_default(self) -> None:
        """Test that Claude harness returns default models when unavailable."""
        harness = Harness(name="claude", path="/nonexistent/claude", type="claude")
        models = harness.get_supported_models()

        # Models are now tuples of (model_name, label)
        assert models == [("haiku", "Light"), ("sonnet", "Standard"), ("opus", "Standard")]

    def test_get_supported_models_codex_default(self) -> None:
        """Test that Codex harness returns default models when unavailable."""
        harness = Harness(name="codex", path="/nonexistent/codex", type="codex")
        models = harness.get_supported_models()

        # Models are now tuples of (model_name, label)
        assert models == [
            ("gpt-5.1-codex-mini", "Light"),
            ("gpt-5.2-codex", "Standard"),
            ("gpt-5.1-codex-max", "Standard"),
            ("gpt-5.2", "Standard"),
        ]

    def test_get_supported_models_custom_returns_empty(self) -> None:
        """Test that custom harness returns empty list when unavailable."""
        harness = Harness(name="custom", path="/nonexistent/custom", type="custom")
        models = harness.get_supported_models()

        assert models == []

    def test_get_supported_models_returns_copy(self) -> None:
        """Test that get_supported_models returns a copy, not the original list."""
        harness = Harness(name="claude", path="/nonexistent/claude", type="claude")
        models1 = harness.get_supported_models()
        models2 = harness.get_supported_models()

        # Modifying one should not affect the other
        models1.append(("test", "Standard"))
        assert ("test", "Standard") not in models2
        assert ("test", "Standard") not in DEFAULT_MODELS["claude"]

    def test_get_supported_models_queries_cli_for_claude(self) -> None:
        """Test that Claude harness returns known models even when available."""
        with patch.object(Harness, "is_available", new_callable=PropertyMock, return_value=True):
            harness = Harness(name="claude", path="claude", type="claude")
            models = harness.get_supported_models()

            # Claude always returns the known models with labels
            model_names = [m[0] for m in models]
            assert "sonnet" in model_names
            assert "haiku" in model_names
            assert "opus" in model_names

    @patch("subprocess.run")
    def test_get_supported_models_custom_with_list_models_flag(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test custom harness querying --list-models flag."""
        # Create a mock executable
        exe_path = tmp_path / "custom_harness"
        exe_path.write_text("#!/bin/bash\necho test")
        exe_path.chmod(0o755)

        # Mock subprocess.run to return model list
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="model-a\nmodel-b\nmodel-c\n",
        )

        harness = Harness(name="custom", path=str(exe_path), type="custom")
        models = harness.get_supported_models()

        # Queried models default to "Standard" label
        assert models == [("model-a", "Standard"), ("model-b", "Standard"), ("model-c", "Standard")]

    @patch("subprocess.run")
    def test_get_supported_models_handles_cli_error(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test that CLI errors are handled gracefully."""
        exe_path = tmp_path / "failing_harness"
        exe_path.write_text("#!/bin/bash\nexit 1")
        exe_path.chmod(0o755)

        mock_run.side_effect = subprocess.SubprocessError("Command failed")

        harness = Harness(name="custom", path=str(exe_path), type="custom")
        models = harness.get_supported_models()

        # Should return empty list for custom on failure
        assert models == []


class TestGetDefaultModel:
    """Tests for the get_default_model method."""

    def test_get_default_model_claude_returns_sonnet(self) -> None:
        """Test that Claude harness defaults to 'sonnet' (first Standard model)."""
        harness = Harness(name="claude", path="/nonexistent/claude", type="claude")
        default = harness.get_default_model()

        assert default == "sonnet"

    def test_get_default_model_codex_returns_standard(self) -> None:
        """Test that Codex harness defaults to first Standard model."""
        harness = Harness(name="codex", path="/nonexistent/codex", type="codex")
        default = harness.get_default_model()

        # gpt-5.2-codex is the first "Standard" labeled model for codex
        assert default == "gpt-5.2-codex"

    def test_get_default_model_custom_returns_none(self) -> None:
        """Test that custom harness with no models returns None."""
        harness = Harness(name="custom", path="/nonexistent/custom", type="custom")
        default = harness.get_default_model()

        assert default is None


class TestIsModelSupported:
    """Tests for the is_model_supported method."""

    def test_is_model_supported_claude_valid(self) -> None:
        """Test that Claude harness accepts valid model names."""
        harness = Harness(name="claude", path="/nonexistent/claude", type="claude")

        assert harness.is_model_supported("haiku") is True
        assert harness.is_model_supported("sonnet") is True
        assert harness.is_model_supported("opus") is True

    def test_is_model_supported_claude_invalid(self) -> None:
        """Test that Claude harness rejects invalid model names."""
        harness = Harness(name="claude", path="/nonexistent/claude", type="claude")

        assert harness.is_model_supported("gpt-4") is False
        assert harness.is_model_supported("gpt-5.2") is False
        assert harness.is_model_supported("nonexistent-model") is False

    def test_is_model_supported_codex_valid(self) -> None:
        """Test that Codex harness accepts valid model names."""
        harness = Harness(name="codex", path="/nonexistent/codex", type="codex")

        assert harness.is_model_supported("gpt-5.1-codex-mini") is True
        assert harness.is_model_supported("gpt-5.2-codex") is True
        assert harness.is_model_supported("gpt-5.1-codex-max") is True
        assert harness.is_model_supported("gpt-5.2") is True

    def test_is_model_supported_codex_invalid(self) -> None:
        """Test that Codex harness rejects Claude model names."""
        harness = Harness(name="codex", path="/nonexistent/codex", type="codex")

        assert harness.is_model_supported("sonnet") is False
        assert harness.is_model_supported("haiku") is False
        assert harness.is_model_supported("opus") is False

    def test_is_model_supported_custom_accepts_any(self) -> None:
        """Test that custom harness with no models accepts any model name."""
        harness = Harness(name="custom", path="/nonexistent/custom", type="custom")

        # Custom harnesses with no predefined models accept anything
        assert harness.is_model_supported("any-model") is True
        assert harness.is_model_supported("sonnet") is True
        assert harness.is_model_supported("gpt-4") is True


class TestFromConfig:
    """Tests for the from_config class method."""

    def test_from_config_with_explicit_type(self) -> None:
        """Test from_config with explicitly provided type."""
        harness = Harness.from_config("/usr/bin/myharness", harness_type="codex")

        assert harness.name == "myharness"
        assert harness.path == "/usr/bin/myharness"
        assert harness.type == "codex"

    def test_from_config_infers_claude_type(self) -> None:
        """Test from_config infers 'claude' type from path."""
        harness = Harness.from_config("/usr/local/bin/claude")

        assert harness.name == "claude"
        assert harness.type == "claude"

    def test_from_config_infers_codex_type(self) -> None:
        """Test from_config infers 'codex' type from path."""
        harness = Harness.from_config("/usr/bin/codex")

        assert harness.name == "codex"
        assert harness.type == "codex"

    def test_from_config_infers_custom_type_for_unknown(self) -> None:
        """Test from_config defaults to 'custom' for unknown tools."""
        harness = Harness.from_config("/usr/bin/mytool")

        assert harness.name == "mytool"
        assert harness.type == "custom"

    def test_from_config_with_simple_command_name(self) -> None:
        """Test from_config with just a command name (no path)."""
        harness = Harness.from_config("claude")

        assert harness.name == "claude"
        assert harness.path == "claude"
        assert harness.type == "claude"


class TestInferType:
    """Tests for the _infer_type static method."""

    def test_infer_type_claude(self) -> None:
        """Test type inference for Claude paths."""
        assert Harness._infer_type("claude") == "claude"
        assert Harness._infer_type("/usr/bin/claude") == "claude"
        assert Harness._infer_type("claude-code") == "claude"
        assert Harness._infer_type("/path/to/Claude") == "claude"

    def test_infer_type_codex(self) -> None:
        """Test type inference for Codex paths."""
        assert Harness._infer_type("codex") == "codex"
        assert Harness._infer_type("/usr/bin/codex") == "codex"
        assert Harness._infer_type("openai") == "codex"
        assert Harness._infer_type("/path/to/openai-cli") == "codex"

    def test_infer_type_custom(self) -> None:
        """Test type inference defaults to custom."""
        assert Harness._infer_type("aider") == "custom"
        assert Harness._infer_type("/usr/bin/mytool") == "custom"
        assert Harness._infer_type("custom-harness") == "custom"


class TestHarnessDetector:
    """Tests for the HarnessDetector class."""

    def test_detector_initialization(self) -> None:
        """Test that HarnessDetector can be instantiated."""
        detector = HarnessDetector()
        assert detector is not None

    def test_known_harnesses_list(self) -> None:
        """Test that KNOWN_HARNESSES contains expected entries."""
        assert ("claude", "claude") in HarnessDetector.KNOWN_HARNESSES
        assert ("codex", "codex") in HarnessDetector.KNOWN_HARNESSES

    @patch("ralph.harness.shutil.which")
    def test_detect_all_finds_both_harnesses(self, mock_which: MagicMock) -> None:
        """Test detect_all finds both claude and codex when available."""
        # Mock shutil.which to return paths for both
        def which_side_effect(name: str) -> str | None:
            paths = {
                "claude": "/usr/local/bin/claude",
                "codex": "/usr/local/bin/codex",
            }
            return paths.get(name)

        mock_which.side_effect = which_side_effect

        detector = HarnessDetector()
        harnesses = detector.detect_all()

        assert len(harnesses) == 2

        claude_harness = next((h for h in harnesses if h.name == "claude"), None)
        assert claude_harness is not None
        assert claude_harness.path == "/usr/local/bin/claude"
        assert claude_harness.type == "claude"

        codex_harness = next((h for h in harnesses if h.name == "codex"), None)
        assert codex_harness is not None
        assert codex_harness.path == "/usr/local/bin/codex"
        assert codex_harness.type == "codex"

    @patch("ralph.harness.shutil.which")
    def test_detect_all_finds_only_claude(self, mock_which: MagicMock) -> None:
        """Test detect_all when only claude is available."""
        def which_side_effect(name: str) -> str | None:
            if name == "claude":
                return "/usr/bin/claude"
            return None

        mock_which.side_effect = which_side_effect

        detector = HarnessDetector()
        harnesses = detector.detect_all()

        assert len(harnesses) == 1
        assert harnesses[0].name == "claude"
        assert harnesses[0].path == "/usr/bin/claude"
        assert harnesses[0].type == "claude"

    @patch("ralph.harness.shutil.which")
    def test_detect_all_finds_only_codex(self, mock_which: MagicMock) -> None:
        """Test detect_all when only codex is available."""
        def which_side_effect(name: str) -> str | None:
            if name == "codex":
                return "/opt/bin/codex"
            return None

        mock_which.side_effect = which_side_effect

        detector = HarnessDetector()
        harnesses = detector.detect_all()

        assert len(harnesses) == 1
        assert harnesses[0].name == "codex"
        assert harnesses[0].path == "/opt/bin/codex"
        assert harnesses[0].type == "codex"

    @patch("ralph.harness.shutil.which")
    def test_detect_all_returns_empty_when_none_found(
        self, mock_which: MagicMock
    ) -> None:
        """Test detect_all returns empty list when no harnesses found."""
        mock_which.return_value = None

        detector = HarnessDetector()
        harnesses = detector.detect_all()

        assert harnesses == []
        assert isinstance(harnesses, list)

    @patch("ralph.harness.shutil.which")
    def test_detect_specific_harness_found(self, mock_which: MagicMock) -> None:
        """Test detect method finds a specific harness."""
        mock_which.return_value = "/home/user/.local/bin/claude"

        detector = HarnessDetector()
        harness = detector.detect("claude")

        assert harness is not None
        assert harness.name == "claude"
        assert harness.path == "/home/user/.local/bin/claude"
        assert harness.type == "claude"

    @patch("ralph.harness.shutil.which")
    def test_detect_specific_harness_not_found(self, mock_which: MagicMock) -> None:
        """Test detect method returns None when harness not found."""
        mock_which.return_value = None

        detector = HarnessDetector()
        harness = detector.detect("claude")

        assert harness is None

    @patch("ralph.harness.shutil.which")
    def test_detect_infers_type_for_custom_harness(
        self, mock_which: MagicMock
    ) -> None:
        """Test detect method infers type for unknown harness names."""
        mock_which.return_value = "/usr/bin/aider"

        detector = HarnessDetector()
        harness = detector.detect("aider")

        assert harness is not None
        assert harness.name == "aider"
        assert harness.path == "/usr/bin/aider"
        assert harness.type == "custom"

    @patch("ralph.harness.shutil.which")
    def test_detect_all_returns_full_paths(self, mock_which: MagicMock) -> None:
        """Test that detect_all returns full absolute paths from shutil.which."""
        mock_which.return_value = "/absolute/path/to/claude"

        detector = HarnessDetector()
        harnesses = detector.detect_all()

        # The path should be the full path returned by shutil.which
        for harness in harnesses:
            assert harness.path.startswith("/")

    @patch("ralph.harness.shutil.which")
    def test_detect_uses_shutil_which(self, mock_which: MagicMock) -> None:
        """Test that detection uses shutil.which for platform-aware PATH searching."""
        mock_which.return_value = None

        detector = HarnessDetector()
        detector.detect("claude")

        # Verify shutil.which was called with the executable name
        mock_which.assert_called_once_with("claude")

    @patch("ralph.harness.shutil.which")
    def test_detect_all_calls_which_for_each_known_harness(
        self, mock_which: MagicMock
    ) -> None:
        """Test that detect_all calls shutil.which for each known harness."""
        mock_which.return_value = None

        detector = HarnessDetector()
        detector.detect_all()

        # Should have called which for both 'claude' and 'codex'
        calls = [call[0][0] for call in mock_which.call_args_list]
        assert "claude" in calls
        assert "codex" in calls
