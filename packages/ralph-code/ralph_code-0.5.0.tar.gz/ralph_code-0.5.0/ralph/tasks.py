"""Task management and JSON schema validation for ralph-coding."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import jsonschema

from .storage import get_project_tasks_path


TaskStatus = Literal["pending", "in_progress", "completed", "errored"]


def _get_schema() -> dict[str, Any]:
    """Load the task schema from the schemas directory."""
    schema_path = Path(__file__).parent / "schemas" / "task_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        result: dict[str, Any] = json.load(f)
        return result


def _validate_tasks_data(data: dict[str, Any]) -> None:
    """Validate tasks data against the JSON schema."""
    schema = _get_schema()
    jsonschema.validate(instance=data, schema=schema)


class Task:
    """Represents a single task (either thin or full spec)."""

    def __init__(
        self,
        name: str,
        id: str | None = None,
        description: str = "",
        status: TaskStatus = "pending",
        prerequisites: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
        files_to_modify: list[str] | None = None,
        notes: str = "",
        created_at: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
        is_thin: bool = False,
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.status = status
        self.prerequisites = prerequisites or []
        self.acceptance_criteria = acceptance_criteria or []
        self.files_to_modify = files_to_modify or []
        self.notes = notes
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.started_at = started_at
        self.completed_at = completed_at
        self._is_thin = is_thin

    @classmethod
    def from_thin(cls, description: str) -> "Task":
        """Create a task from a thin task string."""
        return cls(name=description, is_thin=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | str) -> "Task":
        """Create a task from a dictionary or thin task string."""
        if isinstance(data, str):
            return cls.from_thin(data)

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            prerequisites=data.get("prerequisites"),
            acceptance_criteria=data.get("acceptance_criteria"),
            files_to_modify=data.get("files_to_modify"),
            notes=data.get("notes", ""),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            is_thin=False,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert task to a dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "prerequisites": self.prerequisites,
            "acceptance_criteria": self.acceptance_criteria,
            "files_to_modify": self.files_to_modify,
            "notes": self.notes,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    def to_serializable(self) -> str | dict[str, Any]:
        """Convert task to serializable format (thin string or full dict)."""
        if self._is_thin and self.status == "pending":
            return self.name
        return self.to_dict()

    @property
    def is_thin(self) -> bool:
        """Check if this is a thin (unspecced) task."""
        return self._is_thin

    @property
    def is_specced(self) -> bool:
        """Check if this task has been fully specified."""
        return not self._is_thin

    def spec(
        self,
        description: str,
        acceptance_criteria: list[str] | None = None,
        files_to_modify: list[str] | None = None,
        prerequisites: list[str] | None = None,
        notes: str = "",
    ) -> None:
        """Convert a thin task to a full spec."""
        self.description = description
        self.acceptance_criteria = acceptance_criteria or []
        self.files_to_modify = files_to_modify or []
        self.prerequisites = prerequisites or []
        self.notes = notes
        self._is_thin = False

    def start(self) -> None:
        """Mark the task as in progress."""
        self.status = "in_progress"
        self.started_at = datetime.utcnow().isoformat()

    def complete(self) -> None:
        """Mark the task as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow().isoformat()

    def error(self, reason: str = "") -> None:
        """Mark the task as errored."""
        self.status = "errored"
        if reason:
            self.notes = f"{self.notes}\n\nError: {reason}".strip()


class TaskManager:
    """Manages the collection of tasks for a project."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self._tasks: list[Task] = []
        self._load()

    def _load(self) -> None:
        """Load tasks from the project's tasks.json file."""
        tasks_path = get_project_tasks_path(self.project_dir)

        if tasks_path.exists():
            try:
                with open(tasks_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                _validate_tasks_data(data)
                self._tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
            except (json.JSONDecodeError, jsonschema.ValidationError, IOError) as e:
                # Start fresh if file is corrupted
                self._tasks = []
        else:
            self._tasks = []

    def _save(self) -> None:
        """Save tasks to the project's tasks.json file."""
        tasks_path = get_project_tasks_path(self.project_dir)
        tasks_path.parent.mkdir(parents=True, exist_ok=True)

        data = {"tasks": [t.to_serializable() for t in self._tasks]}
        _validate_tasks_data(data)

        with open(tasks_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @property
    def tasks(self) -> list[Task]:
        """Get all tasks."""
        return self._tasks.copy()

    def add_thin_task(self, description: str) -> Task:
        """Add a thin (unspecced) task."""
        task = Task.from_thin(description)
        self._tasks.append(task)
        self._save()
        return task

    def add_full_task(
        self,
        name: str,
        description: str,
        acceptance_criteria: list[str] | None = None,
        files_to_modify: list[str] | None = None,
        prerequisites: list[str] | None = None,
        notes: str = "",
    ) -> Task:
        """Add a fully specified task."""
        task = Task(
            name=name,
            description=description,
            acceptance_criteria=acceptance_criteria,
            files_to_modify=files_to_modify,
            prerequisites=prerequisites,
            notes=notes,
        )
        self._tasks.append(task)
        self._save()
        return task

    def get_task_by_id(self, task_id: str) -> Task | None:
        """Get a task by its ID."""
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def get_unspecced_tasks(self) -> list[Task]:
        """Get all thin (unspecced) tasks."""
        return [t for t in self._tasks if t.is_thin]

    def get_specced_tasks(self) -> list[Task]:
        """Get all fully specified tasks."""
        return [t for t in self._tasks if t.is_specced]

    def get_pending_tasks(self) -> list[Task]:
        """Get all pending tasks that are ready to work on."""
        return [
            t for t in self._tasks
            if t.status == "pending" and t.is_specced and self._prerequisites_met(t)
        ]

    def get_in_progress_task(self) -> Task | None:
        """Get the currently in-progress task, if any."""
        for task in self._tasks:
            if task.status == "in_progress":
                return task
        return None

    def get_completed_tasks(self) -> list[Task]:
        """Get all completed tasks."""
        return [t for t in self._tasks if t.status == "completed"]

    def get_errored_tasks(self) -> list[Task]:
        """Get all errored tasks."""
        return [t for t in self._tasks if t.status == "errored"]

    def _prerequisites_met(self, task: Task) -> bool:
        """Check if all prerequisites for a task are completed.

        Only considers prerequisites that match existing task IDs.
        Descriptive prerequisites (non-UUID strings) are ignored.
        """
        for prereq_id in task.prerequisites:
            prereq = self.get_task_by_id(prereq_id)
            # Only block on prerequisites that actually exist
            if prereq is not None and prereq.status != "completed":
                return False
        return True

    def update_task(self, task: Task) -> None:
        """Update a task and save changes."""
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                self._save()
                return
        raise ValueError(f"Task not found: {task.id}")

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID."""
        for i, task in enumerate(self._tasks):
            if task.id == task_id:
                del self._tasks[i]
                self._save()
                return True
        return False

    def get_stats(self) -> dict[str, int]:
        """Get task statistics."""
        return {
            "unspecced": len(self.get_unspecced_tasks()),
            "pending": sum(1 for t in self._tasks if t.status == "pending" and t.is_specced),
            "in_progress": sum(1 for t in self._tasks if t.status == "in_progress"),
            "completed": sum(1 for t in self._tasks if t.status == "completed"),
            "errored": sum(1 for t in self._tasks if t.status == "errored"),
        }
