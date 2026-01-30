"""Claude Code CLI integration for ralph-coding application.

This module is deprecated. Use harness_runner instead.
Maintained for backwards compatibility.
"""

# Re-export everything from harness_runner for backwards compatibility
from .harness_runner import (
    HarnessResponse as ClaudeResponse,
    HarnessRunner as ClaudeRunner,
    HarnessResponse,
    HarnessRunner,
    HARNESS_MODEL_MAPPING,
)

__all__ = [
    "ClaudeResponse",
    "ClaudeRunner",
    "HarnessResponse",
    "HarnessRunner",
    "HARNESS_MODEL_MAPPING",
]
