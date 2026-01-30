"""User Story management for ralph-coding.

User stories are derived from PRDs and stored in tasks.json in the project root.
Each story is a small, implementable unit of work.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema


def _get_schema() -> dict[str, Any]:
    """Load the ralph tasks schema."""
    schema_path = Path(__file__).parent / "schemas" / "ralph_tasks_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        result: dict[str, Any] = json.load(f)
        return result


def _validate_tasks_data(data: dict[str, Any]) -> None:
    """Validate tasks data against the JSON schema."""
    schema = _get_schema()
    jsonschema.validate(instance=data, schema=schema)


@dataclass
class UserStory:
    """Represents a single user story from tasks.json."""
    id: str  # US-001, US-002, etc.
    title: str
    description: str
    acceptance_criteria: list[str]
    priority: int
    passes: bool = False
    blocked: bool = False  # True if max attempts exceeded
    needs_intervention: bool = False  # True if human intervention needed
    notes: str = ""
    attempts: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserStory":
        """Create a UserStory from a dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            acceptance_criteria=data["acceptanceCriteria"],
            priority=data["priority"],
            passes=data.get("passes", False),
            blocked=data.get("blocked", False),
            needs_intervention=data.get("needsIntervention", False),
            notes=data.get("notes", ""),
            attempts=data.get("attempts", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "acceptanceCriteria": self.acceptance_criteria,
            "priority": self.priority,
            "passes": self.passes,
            "notes": self.notes,
            "attempts": self.attempts,
        }
        if self.blocked:
            result["blocked"] = True
        if self.needs_intervention:
            result["needsIntervention"] = True
        return result

    def mark_passing(self) -> None:
        """Mark this story as passing."""
        self.passes = True

    def mark_failed(self, notes: str = "") -> None:
        """Mark this story as failed with optional notes."""
        self.passes = False
        self.attempts += 1
        if notes:
            self.notes = f"{self.notes}\n\nAttempt {self.attempts}:\n{notes}".strip()

    def get_prompt(self) -> str:
        """Get the implementation prompt for this story."""
        criteria = "\n".join(f"- {c}" for c in self.acceptance_criteria)
        prompt = f"""## User Story: {self.id} - {self.title}

{self.description}

### Acceptance Criteria:
{criteria}
"""
        if self.notes:
            prompt += f"""
### Notes from Previous Attempts:
{self.notes}
"""
        return prompt


@dataclass
class TasksFile:
    """Represents the complete tasks.json file."""
    project: str
    branch_name: str
    description: str
    prd_file: str
    user_stories: list[UserStory] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TasksFile":
        """Create a TasksFile from a dictionary."""
        return cls(
            project=data["project"],
            branch_name=data["branchName"],
            description=data["description"],
            prd_file=data.get("prdFile", ""),
            user_stories=[UserStory.from_dict(s) for s in data["userStories"]],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "project": self.project,
            "branchName": self.branch_name,
            "description": self.description,
            "userStories": [s.to_dict() for s in self.user_stories],
        }
        if self.prd_file:
            data["prdFile"] = self.prd_file
        return data

    def get_next_story(self, max_attempts: int = 3) -> UserStory | None:
        """Get the next story to implement (lowest priority that hasn't passed or blocked)."""
        pending = [
            s for s in self.user_stories
            if not s.passes and not s.blocked and s.attempts < max_attempts
        ]
        if not pending:
            return None
        return min(pending, key=lambda s: s.priority)

    def get_progress(self) -> tuple[int, int]:
        """Get progress as (completed, total)."""
        completed = sum(1 for s in self.user_stories if s.passes)
        return completed, len(self.user_stories)

    def get_progress_percent(self) -> int:
        """Get progress as a percentage."""
        completed, total = self.get_progress()
        if total == 0:
            return 0
        return int((completed / total) * 100)

    def is_complete(self) -> bool:
        """Check if all stories have passed."""
        return all(s.passes for s in self.user_stories)


class UserStoryManager:
    """Manages tasks.json for a project."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.tasks_file_path = project_dir / "tasks.json"
        self._tasks_file: TasksFile | None = None
        self._load()

    def _load(self) -> None:
        """Load tasks.json if it exists."""
        if self.tasks_file_path.exists():
            try:
                with open(self.tasks_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                _validate_tasks_data(data)
                self._tasks_file = TasksFile.from_dict(data)
            except (json.JSONDecodeError, jsonschema.ValidationError, IOError):
                self._tasks_file = None
        else:
            self._tasks_file = None

    def _save(self) -> None:
        """Save tasks.json."""
        if self._tasks_file is None:
            return

        data = self._tasks_file.to_dict()
        _validate_tasks_data(data)

        with open(self.tasks_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def reload(self) -> None:
        """Reload from disk."""
        self._load()

    def has_tasks(self) -> bool:
        """Check if tasks.json exists and has stories."""
        return self._tasks_file is not None and len(self._tasks_file.user_stories) > 0

    def get_tasks_file(self) -> TasksFile | None:
        """Get the current tasks file."""
        return self._tasks_file

    def get_prd_file(self) -> str | None:
        """Get the source PRD file path."""
        if self._tasks_file:
            return self._tasks_file.prd_file
        return None

    def create_from_json(self, tasks_json: str, prd_file: str = "") -> TasksFile:
        """Create tasks.json from JSON string (output from Claude)."""
        data = json.loads(tasks_json)
        if prd_file:
            data["prdFile"] = prd_file
        _validate_tasks_data(data)
        self._tasks_file = TasksFile.from_dict(data)
        self._save()
        return self._tasks_file

    def get_next_story(self, max_attempts: int = 3) -> UserStory | None:
        """Get the next story to implement."""
        if self._tasks_file is None:
            return None
        return self._tasks_file.get_next_story(max_attempts)

    def update_story(self, story: UserStory) -> None:
        """Update a story and save."""
        if self._tasks_file is None:
            return

        for i, s in enumerate(self._tasks_file.user_stories):
            if s.id == story.id:
                self._tasks_file.user_stories[i] = story
                self._save()
                return

    def get_progress(self) -> tuple[int, int]:
        """Get progress as (completed, total)."""
        if self._tasks_file is None:
            return 0, 0
        return self._tasks_file.get_progress()

    def get_progress_percent(self) -> int:
        """Get progress as a percentage."""
        if self._tasks_file is None:
            return 0
        return self._tasks_file.get_progress_percent()

    def is_complete(self) -> bool:
        """Check if all stories have passed."""
        if self._tasks_file is None:
            return False
        return self._tasks_file.is_complete()

    def get_branch_name(self) -> str | None:
        """Get the branch name for this feature."""
        if self._tasks_file:
            return self._tasks_file.branch_name
        return None

    def clear(self) -> None:
        """Remove tasks.json."""
        if self.tasks_file_path.exists():
            self.tasks_file_path.unlink()
        self._tasks_file = None

    def archive(self, archive_dir: Path) -> None:
        """Archive the current tasks.json to a directory."""
        if not self.tasks_file_path.exists():
            return

        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / "tasks.json"

        # Copy tasks.json to archive
        import shutil
        shutil.copy(self.tasks_file_path, archive_path)
