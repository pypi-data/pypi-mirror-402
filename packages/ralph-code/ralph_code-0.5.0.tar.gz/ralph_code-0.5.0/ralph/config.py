"""Configuration management for ralph-coding application."""

import json
from pathlib import Path
from typing import Any, Literal

from .storage import get_config_path


ErrorMode = Literal["block", "retry", "pause", "skip"]


DEFAULT_CONFIG = {
    "harness": "claude",
    "worker_model": "opus",
    "summary_model": "haiku",
    "max_iterations": 10,
    "max_story_attempts": 3,
    "auto_spec_without_oversight": True,
    "wait_on_rate_limit": True,
    "pause_on_completion": True,
    "always_build_tests": False,
    "branch_prefix": "ralph",
    "on_error": "block",
}


class Config:
    """Global configuration manager for ralph-coding."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from disk, using defaults for missing values."""
        config_path = get_config_path()
        needs_save = False

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = {}

        # Migration: convert old 'claude_binary' key to 'harness'
        if "claude_binary" in self._config and "harness" not in self._config:
            self._config["harness"] = self._config.pop("claude_binary")
            needs_save = True

        # Migration: map old 'model' key to worker_model
        if "model" in self._config and "worker_model" not in self._config:
            self._config["worker_model"] = self._config["model"]
            needs_save = True
        if "model" in self._config:
            self._config.pop("model", None)
            needs_save = True

        # Set worker model if missing (based on harness defaults)
        if "worker_model" not in self._config:
            harness = self._config.get("harness", DEFAULT_CONFIG["harness"])
            if harness == "codex":
                self._config["worker_model"] = "gpt-5.2-codex"
            else:
                self._config["worker_model"] = "opus"
            needs_save = True

        # Set summary model if missing (based on harness defaults)
        if "summary_model" not in self._config:
            harness = self._config.get("harness", DEFAULT_CONFIG["harness"])
            if harness == "codex":
                self._config["summary_model"] = "gpt-5.2"
            else:
                self._config["summary_model"] = "haiku"
            needs_save = True

        # Apply defaults for any missing keys
        for key, default in DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = default

        # Save if migration was performed
        if needs_save:
            self._save()

    def _save(self) -> None:
        """Save configuration to disk."""
        config_path = get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    @property
    def harness(self) -> str:
        """Path to the harness CLI tool (e.g., claude, aider)."""
        return str(self._config["harness"])

    @harness.setter
    def harness(self, value: str) -> None:
        self._config["harness"] = value
        self._save()

    @property
    def worker_model(self) -> str:
        """Model to use for implementation (harness-specific model names)."""
        return str(self._config["worker_model"])

    @worker_model.setter
    def worker_model(self, value: str) -> None:
        self._config["worker_model"] = value
        self._save()

    @property
    def summary_model(self) -> str:
        """Model to use for summarization and review tasks."""
        return str(self._config["summary_model"])

    @summary_model.setter
    def summary_model(self, value: str) -> None:
        self._config["summary_model"] = value
        self._save()

    @property
    def max_iterations(self) -> int:
        """Maximum iterations for implementation loop."""
        return int(self._config["max_iterations"])

    @max_iterations.setter
    def max_iterations(self, value: int) -> None:
        self._config["max_iterations"] = max(1, value)
        self._save()

    @property
    def auto_spec_without_oversight(self) -> bool:
        """Whether to auto-spec tasks without user confirmation."""
        return bool(self._config["auto_spec_without_oversight"])

    @auto_spec_without_oversight.setter
    def auto_spec_without_oversight(self, value: bool) -> None:
        self._config["auto_spec_without_oversight"] = value
        self._save()

    @property
    def wait_on_rate_limit(self) -> bool:
        """Whether to wait and retry on rate limit."""
        return bool(self._config["wait_on_rate_limit"])

    @wait_on_rate_limit.setter
    def wait_on_rate_limit(self, value: bool) -> None:
        self._config["wait_on_rate_limit"] = value
        self._save()

    @property
    def pause_on_completion(self) -> bool:
        """Whether to pause after completing all tasks."""
        return bool(self._config["pause_on_completion"])

    @pause_on_completion.setter
    def pause_on_completion(self, value: bool) -> None:
        self._config["pause_on_completion"] = value
        self._save()

    @property
    def always_build_tests(self) -> bool:
        """Whether to always build tests for implementations."""
        return bool(self._config["always_build_tests"])

    @always_build_tests.setter
    def always_build_tests(self, value: bool) -> None:
        self._config["always_build_tests"] = value
        self._save()

    @property
    def max_story_attempts(self) -> int:
        """Maximum attempts per story before marking as blocked."""
        return int(self._config.get("max_story_attempts", 3))

    @max_story_attempts.setter
    def max_story_attempts(self, value: int) -> None:
        self._config["max_story_attempts"] = max(1, value)
        self._save()

    @property
    def branch_prefix(self) -> str:
        """Prefix for feature branch names (e.g., 'ralph' creates 'ralph/feature-name')."""
        return str(self._config.get("branch_prefix", "ralph"))

    @branch_prefix.setter
    def branch_prefix(self, value: str) -> None:
        self._config["branch_prefix"] = value
        self._save()

    @property
    def on_error(self) -> ErrorMode:
        """Error handling mode (block, retry, pause, skip)."""
        value: ErrorMode = self._config["on_error"]
        return value

    @on_error.setter
    def on_error(self, value: ErrorMode) -> None:
        if value not in ("block", "retry", "pause", "skip"):
            raise ValueError(f"Invalid error mode: {value}")
        self._config["on_error"] = value
        self._save()

    def to_dict(self) -> dict[str, Any]:
        """Return a copy of the configuration as a dictionary."""
        return self._config.copy()

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self._config = DEFAULT_CONFIG.copy()
        self._save()


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
