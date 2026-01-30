"""Unit tests for the HarnessRunner class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ralph.harness_runner import HarnessRunner


class TestBuildCommand:
    """Tests for the _build_command method."""

    @pytest.fixture
    def runner_with_claude(self, tmp_path: Path) -> HarnessRunner:
        """Create a HarnessRunner with Claude harness."""
        with patch("ralph.harness_runner.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                harness="/usr/bin/claude",
                model="sonnet",
                wait_on_rate_limit=True,
            )
            runner = HarnessRunner(project_dir=tmp_path)
            # Force the harness type
            runner._harness = MagicMock(path="/usr/bin/claude", type="claude")
            return runner

    @pytest.fixture
    def runner_with_codex(self, tmp_path: Path) -> HarnessRunner:
        """Create a HarnessRunner with Codex harness."""
        with patch("ralph.harness_runner.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                harness="/usr/bin/codex",
                model="sonnet",
                wait_on_rate_limit=True,
            )
            runner = HarnessRunner(project_dir=tmp_path)
            # Force the harness type
            runner._harness = MagicMock(path="/usr/bin/codex", type="codex")
            return runner

    # Claude CLI tests
    def test_claude_basic_command(self, runner_with_claude: HarnessRunner) -> None:
        """Test Claude CLI basic command structure."""
        cmd = runner_with_claude._build_command("test prompt")

        assert cmd[0] == "/usr/bin/claude"
        assert "--model" in cmd
        assert "--print" in cmd
        assert "-p" in cmd
        assert "test prompt" in cmd
        # Should not have write flags
        assert "--dangerously-skip-permissions" not in cmd

    def test_claude_with_model(self, runner_with_claude: HarnessRunner) -> None:
        """Test Claude CLI with explicit model."""
        cmd = runner_with_claude._build_command("test prompt", model="haiku")

        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "haiku"

    def test_claude_with_writes(self, runner_with_claude: HarnessRunner) -> None:
        """Test Claude CLI with write permissions."""
        cmd = runner_with_claude._build_command("test prompt", allow_writes=True)

        assert "--dangerously-skip-permissions" in cmd

    def test_claude_without_print(self, runner_with_claude: HarnessRunner) -> None:
        """Test Claude CLI without print mode."""
        cmd = runner_with_claude._build_command("test prompt", print_output=False)

        assert "--print" not in cmd

    def test_claude_command_order(self, runner_with_claude: HarnessRunner) -> None:
        """Test Claude CLI command structure: claude --model X --print -p 'prompt'."""
        cmd = runner_with_claude._build_command("test prompt", model="opus")

        # The prompt should come after -p flag
        p_idx = cmd.index("-p")
        assert cmd[p_idx + 1] == "test prompt"

    # Codex CLI tests
    def test_codex_uses_exec_subcommand(self, runner_with_codex: HarnessRunner) -> None:
        """Test Codex CLI uses 'exec' subcommand for non-interactive mode."""
        cmd = runner_with_codex._build_command("test prompt")

        assert cmd[0] == "/usr/bin/codex"
        assert cmd[1] == "exec"  # exec subcommand should be first after the binary

    def test_codex_basic_command(self, runner_with_codex: HarnessRunner) -> None:
        """Test Codex CLI basic command structure."""
        cmd = runner_with_codex._build_command("test prompt")

        assert "exec" in cmd
        assert "--model" in cmd
        assert "--sandbox" in cmd
        assert "read-only" in cmd  # Default without writes
        assert "test prompt" in cmd
        # Should NOT have these incorrect flags
        assert "--quiet" not in cmd
        assert "--writable-root" not in cmd

    def test_codex_with_writes(self, runner_with_codex: HarnessRunner) -> None:
        """Test Codex CLI with write permissions."""
        cmd = runner_with_codex._build_command("test prompt", allow_writes=True)

        assert "--sandbox" in cmd
        sandbox_idx = cmd.index("--sandbox")
        assert cmd[sandbox_idx + 1] == "workspace-write"
        assert "--full-auto" in cmd

    def test_codex_without_print(self, runner_with_codex: HarnessRunner) -> None:
        """Test Codex CLI without print mode (no exec subcommand)."""
        cmd = runner_with_codex._build_command("test prompt", print_output=False)

        assert "exec" not in cmd

    def test_codex_model_mapping(self, runner_with_codex: HarnessRunner) -> None:
        """Test Codex CLI maps internal model names to OpenAI models."""
        cmd = runner_with_codex._build_command("test prompt", model="haiku")

        model_idx = cmd.index("--model")
        # 'haiku' should map to 'gpt-5.1-codex-mini' for codex
        assert cmd[model_idx + 1] == "gpt-5.1-codex-mini"

    def test_codex_prompt_is_positional(self, runner_with_codex: HarnessRunner) -> None:
        """Test Codex CLI uses positional argument for prompt (no -p flag)."""
        cmd = runner_with_codex._build_command("test prompt")

        assert "-p" not in cmd
        # Prompt should be the last argument
        assert cmd[-1] == "test prompt"

    def test_codex_no_dangerously_skip_permissions(
        self, runner_with_codex: HarnessRunner
    ) -> None:
        """Test Codex CLI doesn't use Claude-specific flags."""
        cmd = runner_with_codex._build_command("test prompt", allow_writes=True)

        assert "--dangerously-skip-permissions" not in cmd
        assert "--print" not in cmd


class TestModelMapping:
    """Tests for the _map_model method."""

    @pytest.fixture
    def runner(self, tmp_path: Path) -> HarnessRunner:
        """Create a basic HarnessRunner."""
        with patch("ralph.harness_runner.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                harness="claude",
                model="sonnet",
                wait_on_rate_limit=True,
            )
            return HarnessRunner(project_dir=tmp_path)

    def test_claude_model_mapping(self, runner: HarnessRunner) -> None:
        """Test Claude model mapping (should be identity)."""
        runner._harness = MagicMock(type="claude")

        assert runner._map_model("haiku") == "haiku"
        assert runner._map_model("sonnet") == "sonnet"
        assert runner._map_model("opus") == "opus"

    def test_codex_model_mapping(self, runner: HarnessRunner) -> None:
        """Test Codex model mapping to OpenAI models."""
        runner._harness = MagicMock(type="codex")

        assert runner._map_model("haiku") == "gpt-5.1-codex-mini"
        assert runner._map_model("sonnet") == "gpt-5.2-codex"
        assert runner._map_model("opus") == "gpt-5.1-codex-max"

    def test_unknown_model_passthrough(self, runner: HarnessRunner) -> None:
        """Test that unknown model names are passed through unchanged."""
        runner._harness = MagicMock(type="claude")

        assert runner._map_model("unknown-model") == "unknown-model"
        assert runner._map_model("custom-model-v2") == "custom-model-v2"
