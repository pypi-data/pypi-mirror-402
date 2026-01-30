"""Harness abstraction layer for CLI tools in ralph-coding application.

This module provides the core abstraction for integrating different AI CLI tools
with Ralph. It defines:

- Harness: A dataclass representing a CLI tool with validation and model querying
- HarnessDetector: Discovers available harnesses on the system PATH
- HarnessType: Type literal for known harness categories (claude, codex, custom)

The harness system allows Ralph to work with different AI backends (Claude, Codex,
or custom tools) without changing its core workflow logic. Each harness type has
specific CLI flag patterns and model mappings handled by HarnessRunner.

Example usage:
    # Create a harness from configuration
    harness = Harness.from_config("claude")

    # Check availability
    if harness.is_available:
        models = harness.get_supported_models()

    # Auto-detect available harnesses
    detector = HarnessDetector()
    available = detector.detect_all()

See HARNESS_ARCHITECTURE.md for detailed documentation on adding custom harnesses.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Literal


# Type literal defining the supported harness categories.
# - "claude": Anthropic's Claude CLI tool
# - "codex": OpenAI's Codex CLI tool
# - "custom": Any other CLI tool (uses Claude-like flags by default)
HarnessType = Literal["claude", "codex", "custom"]

# Default models for known harness types.
# Each tuple is (model_name, label) where label indicates the model tier:
# - "Light": Faster, cheaper models for quick tasks (PRD generation, verification)
# - "Standard": Full-featured models for implementation tasks
# These defaults are used when CLI model querying fails or isn't supported.
DEFAULT_MODELS: dict[HarnessType, list[tuple[str, str]]] = {
    "claude": [
        ("haiku", "Light"),
        ("sonnet", "Standard"),
        ("opus", "Standard"),
    ],
    "codex": [
        ("gpt-5.1-codex-mini", "Light"),
        ("gpt-5.2-codex", "Standard"),
        ("gpt-5.1-codex-max", "Standard"),
        ("gpt-5.2", "Standard"),
    ],
    "custom": [],  # Custom harnesses must provide models via CLI or manual entry
}

DEFAULT_WORKER_MODEL: dict[HarnessType, str] = {
    "claude": "opus",
    "codex": "gpt-5.2-codex",
    "custom": "",
}

DEFAULT_SUMMARY_MODEL: dict[HarnessType, str] = {
    "claude": "haiku",
    "codex": "gpt-5.2",
    "custom": "",
}


@dataclass
class Harness:
    """
    Represents a CLI harness tool for AI-assisted coding.

    A harness is an abstraction over different CLI tools (like claude, codex, etc.)
    that can be used to run AI-powered code generation tasks.
    """

    name: str
    path: str
    type: HarnessType

    @property
    def is_available(self) -> bool:
        """
        Check if the harness is available (path exists and is executable).

        Returns:
            True if the harness executable exists and is executable, False otherwise.
        """
        # If path is just a command name (no directory), check if it's on PATH
        if os.path.dirname(self.path) == "":
            resolved = shutil.which(self.path)
            if resolved is None:
                return False
            return os.access(resolved, os.X_OK)

        # Otherwise check the absolute/relative path directly
        if not os.path.exists(self.path):
            return False

        return os.access(self.path, os.X_OK)

    def get_supported_models(self) -> list[tuple[str, str]]:
        """
        Get the list of models supported by this harness.

        For known harness types (claude, codex), this attempts to query the CLI
        for available models. If that fails or for custom harnesses, it returns
        sensible defaults based on the harness type.

        Returns:
            List of (model_name, label) tuples where label is "Standard" or "Light".
        """
        # Try to query the harness CLI for models
        queried_models = self._query_models_from_cli()
        if queried_models:
            return queried_models

        # Fall back to defaults for the harness type
        return DEFAULT_MODELS.get(self.type, []).copy()

    def get_default_model(self) -> str | None:
        """
        Get the default model for this harness type.

        Returns the first "Standard" labeled model, or the first model if no
        standard model exists. Returns None if no models are available.

        Returns:
            Model name string, or None if no models available.
        """
        models = self.get_supported_models()
        if not models:
            return None

        # Prefer a "Standard" model as default
        for model_name, label in models:
            if label == "Standard":
                return model_name

        # Fall back to first available model
        return models[0][0]

    def get_default_worker_model(self) -> str | None:
        """Get the default worker model for this harness type."""
        preferred = DEFAULT_WORKER_MODEL.get(self.type)
        if preferred:
            return preferred
        return self.get_default_model()

    def get_default_summary_model(self) -> str | None:
        """Get the default summary model for this harness type."""
        preferred = DEFAULT_SUMMARY_MODEL.get(self.type)
        if preferred:
            return preferred
        models = self.get_supported_models()
        if not models:
            return None
        for model_name, label in models:
            if label == "Light":
                return model_name
        return models[0][0]

    def is_model_supported(self, model: str) -> bool:
        """
        Check if a model name is supported by this harness.

        Args:
            model: Model name to check.

        Returns:
            True if the model is in the supported models list, False otherwise.
        """
        models = self.get_supported_models()
        # Empty list means any model is acceptable (custom harness)
        if not models:
            return True
        return any(model_name == model for model_name, _ in models)

    def _query_models_from_cli(self) -> list[tuple[str, str]]:
        """
        Attempt to query the harness CLI for available models.

        Returns:
            List of (model_name, label) tuples if successful, empty list otherwise.
        """
        if not self.is_available:
            return []

        # Different harnesses have different ways to list models
        # Claude Code uses: claude --help (models are in help text)
        # We try common patterns
        try:
            if self.type == "claude":
                return self._query_claude_models()
            elif self.type == "codex":
                return self._query_codex_models()
            else:
                # Custom harnesses: try generic --list-models flag
                return self._query_generic_models()
        except (subprocess.SubprocessError, OSError):
            return []

    def _query_claude_models(self) -> list[tuple[str, str]]:
        """Query Claude CLI for available models."""
        # Claude Code doesn't have a direct --list-models command
        # The models are fixed: haiku, sonnet, opus
        # We could parse --help output but the models are well-known
        return DEFAULT_MODELS["claude"].copy()

    def _query_codex_models(self) -> list[tuple[str, str]]:
        """Query Codex CLI for available models."""
        # Codex/OpenAI CLI model listing would go here
        # For now return defaults
        return DEFAULT_MODELS["codex"].copy()

    def _query_generic_models(self) -> list[tuple[str, str]]:
        """Try generic model listing for custom harnesses."""
        # Try common flags that tools might support
        for flag in ["--list-models", "--models", "models"]:
            try:
                result = subprocess.run(
                    [self.path, flag],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    # Parse output - assume one model per line
                    models: list[tuple[str, str]] = [
                        (line.strip(), "Standard")  # Default label for queried models
                        for line in result.stdout.strip().split("\n")
                        if line.strip() and not line.startswith("#")
                    ]
                    if models:
                        return models
            except (subprocess.SubprocessError, OSError):
                continue
        return []

    @classmethod
    def from_config(
        cls,
        harness_path: str,
        harness_type: HarnessType | None = None,
    ) -> "Harness":
        """
        Create a Harness from a configuration path.

        Args:
            harness_path: Path to the harness executable or command name.
            harness_type: Type of harness. If None, inferred from the path.

        Returns:
            A new Harness instance.
        """
        # Infer type from path if not provided
        if harness_type is None:
            harness_type = cls._infer_type(harness_path)

        # Extract name from path
        name = os.path.basename(harness_path)

        return cls(name=name, path=harness_path, type=harness_type)

    @staticmethod
    def _infer_type(harness_path: str) -> HarnessType:
        """
        Infer the harness type from the path.

        Args:
            harness_path: Path to the harness executable.

        Returns:
            The inferred harness type.
        """
        basename = os.path.basename(harness_path).lower()

        if "claude" in basename:
            return "claude"
        elif "codex" in basename or "openai" in basename:
            return "codex"
        else:
            return "custom"


class HarnessDetector:
    """Detects available CLI harnesses on the system PATH.

    This class provides platform-aware detection of known harness tools
    (claude, codex) by searching the system PATH using shutil.which().

    The detector is used by:
    - Settings UI: To show available harnesses for selection
    - Startup validation: To verify the configured harness exists

    Example:
        detector = HarnessDetector()

        # Find all available harnesses
        all_harnesses = detector.detect_all()

        # Find a specific harness
        claude = detector.detect("claude")
        if claude and claude.is_available:
            print(f"Found Claude at {claude.path}")

    Note:
        Detection only checks if executables exist and are accessible.
        It does not validate that they are functional AI tools.
    """

    # Known harness executables to search for.
    # Format: (executable_name, harness_type)
    # Add new known harnesses here to enable auto-detection.
    KNOWN_HARNESSES: list[tuple[str, HarnessType]] = [
        ("claude", "claude"),
        ("codex", "codex"),
    ]

    def __init__(self) -> None:
        """Initialize the HarnessDetector."""
        pass

    def detect_all(self) -> list[Harness]:
        """
        Detect all available harnesses on the system PATH.

        Searches for known harness executables (claude, codex) using
        platform-aware PATH searching (shutil.which).

        Returns:
            List of detected Harness objects with full paths.
            Returns an empty list if no harnesses are found.
        """
        detected: list[Harness] = []

        for executable_name, harness_type in self.KNOWN_HARNESSES:
            harness = self._detect_harness(executable_name, harness_type)
            if harness is not None:
                detected.append(harness)

        return detected

    def _detect_harness(
        self, executable_name: str, harness_type: HarnessType
    ) -> Harness | None:
        """
        Detect a specific harness executable on the PATH.

        Args:
            executable_name: Name of the executable to search for.
            harness_type: The type of harness this executable represents.

        Returns:
            A Harness object if found, None otherwise.
        """
        path = shutil.which(executable_name)
        if path is None:
            return None

        return Harness(
            name=executable_name,
            path=path,
            type=harness_type,
        )

    def detect(self, executable_name: str) -> Harness | None:
        """
        Detect a specific harness by executable name.

        Args:
            executable_name: Name of the executable to search for (e.g., 'claude').

        Returns:
            A Harness object if found, None otherwise.
        """
        path = shutil.which(executable_name)
        if path is None:
            return None

        harness_type = Harness._infer_type(executable_name)
        return Harness(
            name=executable_name,
            path=path,
            type=harness_type,
        )
