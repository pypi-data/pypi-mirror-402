"""Platform-specific storage paths for ralph-coding application."""

from pathlib import Path
from platformdirs import user_data_dir


APP_NAME = "ralph-coding"


def get_app_data_dir() -> Path:
    """
    Get the platform-specific application data directory.

    Returns:
        - Windows: %APPDATA%/ralph-coding/
        - macOS: ~/Library/Application Support/ralph-coding/
        - Linux: ~/.local/share/ralph-coding/
    """
    data_dir = Path(user_data_dir(APP_NAME))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_path() -> Path:
    """Get the path to the global config file."""
    return get_app_data_dir() / "config.json"


def get_project_ralph_dir(project_dir: Path) -> Path:
    """
    Get the .ralph directory for a specific project.

    Args:
        project_dir: The root directory of the project

    Returns:
        Path to the .ralph directory within the project
    """
    ralph_dir = project_dir / ".ralph"
    ralph_dir.mkdir(parents=True, exist_ok=True)
    return ralph_dir


def get_project_tasks_path(project_dir: Path) -> Path:
    """Get the path to the project's tasks.json file."""
    return get_project_ralph_dir(project_dir) / "tasks.json"


def get_project_state_path(project_dir: Path) -> Path:
    """Get the path to the project's state.json file."""
    return get_project_ralph_dir(project_dir) / "state.json"


def get_project_logs_dir(project_dir: Path) -> Path:
    """Get the path to the project's logs directory (for debug mode)."""
    logs_dir = get_project_ralph_dir(project_dir) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_progress_md_path(project_dir: Path) -> Path:
    """Get the path to progress.md in the project root."""
    return project_dir / "progress.md"


def get_learnings_md_path(project_dir: Path) -> Path:
    """Get the path to learnings.md in the project root."""
    return project_dir / "learnings.md"


def get_summarised_notes_path(project_dir: Path) -> Path:
    """Get the path to summarised_notes.txt in the .ralph directory.

    This file archives full story notes along with their summaries
    when stories hit max attempts (debug mode only).
    """
    return get_project_ralph_dir(project_dir) / "summarised_notes.txt"
