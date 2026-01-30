"""PRD (Product Requirements Document) management for ralph-coding.

PRDs are stored as files in the PRD folder:
- .txt files = unspecced tasks (simple descriptions)
- .md files = specced PRDs (full specifications)
"""

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

PRDStatus = Literal["unspecced", "pending", "questions", "in_progress", "completed", "errored"]


@dataclass
class PRDQuestion:
    """Represents an open question in a PRD."""
    question: str
    options: list[str] | None = None  # Multi-choice options if any
    answer: str | None = None


def slugify(text: str) -> str:
    """Convert text to kebab-case slug for filenames."""
    # Lowercase and replace spaces/underscores with hyphens
    slug = text.lower().strip()
    slug = re.sub(r'[_\s]+', '-', slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug[:50]  # Limit length


@dataclass
class PRD:
    """Represents a Product Requirements Document."""
    id: str
    name: str
    file_path: Path
    is_specced: bool
    status: PRDStatus = "pending"
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    questions: list[PRDQuestion] = field(default_factory=list)

    @classmethod
    def from_txt_file(cls, file_path: Path) -> "PRD":
        """Create an unspecced PRD from a .txt file."""
        content = file_path.read_text().strip()
        name = file_path.stem  # filename without extension
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            file_path=file_path,
            is_specced=False,
            status="unspecced",
            description=content,
        )

    @classmethod
    def from_md_file(cls, file_path: Path) -> "PRD":
        """Create a specced PRD from a .md file."""
        content = file_path.read_text()
        name = file_path.stem

        # Try to extract title from first heading
        title_match = re.search(r'^#\s+(?:PRD:\s*)?(.+)$', content, re.MULTILINE)
        if title_match:
            name = title_match.group(1).strip()

        # Parse the State section
        status: PRDStatus = "pending"
        questions: list[PRDQuestion] = []

        # Look for ## State section
        state_match = re.search(r'^## State\s*\n(.*?)(?=^## |\Z)', content, re.MULTILINE | re.DOTALL)
        if state_match:
            state_section = state_match.group(1).strip()

            # Check state value
            if "ready to implement" in state_section.lower():
                status = "pending"
            elif "open questions" in state_section.lower():
                status = "questions"
                # Parse questions (lines after the state indicator)
                lines = state_section.split('\n')
                for line in lines[1:]:  # Skip the "- Open Questions" line
                    line = line.strip()
                    if not line or line.startswith('-'):
                        continue

                    # Check for JSON options at end of line
                    json_match = re.search(r'\[.*\]\s*$', line)
                    if json_match:
                        try:
                            options = json.loads(json_match.group())
                            question_text = line[:json_match.start()].strip()
                            questions.append(PRDQuestion(question=question_text, options=options))
                        except json.JSONDecodeError:
                            questions.append(PRDQuestion(question=line))
                    else:
                        questions.append(PRDQuestion(question=line))

        # Check for status markers (legacy/override)
        if "<!-- STATUS: completed -->" in content:
            status = "completed"
        elif "<!-- STATUS: in_progress -->" in content:
            status = "in_progress"
        elif "<!-- STATUS: errored -->" in content:
            status = "errored"

        return cls(
            id=str(uuid.uuid4()),
            name=name,
            file_path=file_path,
            is_specced=True,
            status=status,
            description=content[:500],  # First 500 chars as description
            questions=questions,
        )

    def start(self) -> None:
        """Mark the PRD as in progress."""
        self.status = "in_progress"
        self.started_at = datetime.utcnow().isoformat()

    def complete(self) -> None:
        """Mark the PRD as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow().isoformat()

    def error(self, reason: str = "") -> None:
        """Mark the PRD as errored."""
        self.status = "errored"

    @property
    def content(self) -> str:
        """Get the full content of the PRD file."""
        if self.file_path.exists():
            return self.file_path.read_text()
        return self.description


class PRDManager:
    """Manages PRD files in the PRD folder."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.prd_dir = project_dir / "PRD"
        self._ensure_prd_dir()
        self._prds: list[PRD] = []
        self._load()

    def _ensure_prd_dir(self) -> None:
        """Ensure PRD directory exists."""
        self.prd_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load all PRDs from the PRD folder."""
        self._prds = []

        # Load unspecced tasks (.txt files)
        for txt_file in self.prd_dir.glob("*.txt"):
            self._prds.append(PRD.from_txt_file(txt_file))

        # Load specced PRDs (.md files)
        for md_file in self.prd_dir.glob("*.md"):
            self._prds.append(PRD.from_md_file(md_file))

    def reload(self) -> None:
        """Reload PRDs from disk."""
        self._load()

    def get_all_prds(self) -> list[PRD]:
        """Get all PRDs."""
        return list(self._prds)

    def get_unspecced_prds(self) -> list[PRD]:
        """Get all unspecced PRDs (.txt files)."""
        return [p for p in self._prds if not p.is_specced]

    def get_specced_prds(self) -> list[PRD]:
        """Get all specced PRDs (.md files)."""
        return [p for p in self._prds if p.is_specced]

    def get_pending_prds(self) -> list[PRD]:
        """Get specced PRDs that are pending implementation."""
        return [p for p in self._prds if p.is_specced and p.status == "pending"]

    def get_in_progress_prd(self) -> PRD | None:
        """Get the currently in-progress PRD."""
        for prd in self._prds:
            if prd.status == "in_progress":
                return prd
        return None

    def get_completed_prds(self) -> list[PRD]:
        """Get all completed PRDs."""
        return [p for p in self._prds if p.status == "completed"]

    def get_errored_prds(self) -> list[PRD]:
        """Get all errored PRDs."""
        return [p for p in self._prds if p.status == "errored"]

    def get_questions_prds(self) -> list[PRD]:
        """Get PRDs that have open questions."""
        return [p for p in self._prds if p.status == "questions"]

    def get_prd_by_id(self, prd_id: str) -> PRD | None:
        """Get a PRD by its ID."""
        for prd in self._prds:
            if prd.id == prd_id:
                return prd
        return None

    def spec_prd(self, prd: PRD, prd_content: str, new_name: str | None = None) -> PRD:
        """
        Convert an unspecced PRD (.txt) to a specced PRD (.md).

        Args:
            prd: The unspecced PRD to convert
            prd_content: The full PRD content in markdown
            new_name: Optional new name for the PRD file (will be slugified)

        Returns:
            The new specced PRD
        """
        if prd.is_specced:
            raise ValueError("PRD is already specced")

        # Determine new filename
        if new_name:
            slug = slugify(new_name)
        else:
            # Try to extract name from PRD content
            title_match = re.search(r'^#\s+(?:PRD:\s*)?(.+)$', prd_content, re.MULTILINE)
            if title_match:
                slug = slugify(title_match.group(1))
            else:
                slug = slugify(prd.name)

        new_file = self.prd_dir / f"{slug}.md"

        # Handle name collision
        counter = 1
        while new_file.exists():
            new_file = self.prd_dir / f"{slug}-{counter}.md"
            counter += 1

        # Write the new .md file
        new_file.write_text(prd_content)

        # Delete the old .txt file
        if prd.file_path.exists() and prd.file_path.suffix == ".txt":
            prd.file_path.unlink()

        # Reload to pick up changes
        self._load()

        # Return the new PRD
        for p in self._prds:
            if p.file_path == new_file:
                return p

        raise RuntimeError("Failed to find newly created PRD")

    def update_prd_status(self, prd: PRD, status: PRDStatus) -> None:
        """Update a PRD's status by modifying its file."""
        if not prd.is_specced:
            return  # Can't update status of unspecced PRDs

        content = prd.file_path.read_text()

        # Remove any existing status line
        content = re.sub(r'\n*<!-- STATUS: \w+ -->\n*', '\n', content)

        # Add status at the end
        content = content.rstrip() + f"\n\n<!-- STATUS: {status} -->\n"

        prd.file_path.write_text(content)
        prd.status = status

    def answer_prd_questions(self, prd: PRD, answers: list[str]) -> list[tuple[str, str]]:
        """
        Update a PRD with answers to its questions.

        Args:
            prd: The PRD with questions
            answers: List of answers corresponding to each question

        Returns:
            List of (question, answer) tuples that might be useful as learnings
        """
        if not prd.is_specced or prd.status != "questions":
            return []

        content = prd.file_path.read_text()

        # Build the answered questions section
        answered_lines = []
        learnings = []

        for i, question in enumerate(prd.questions):
            answer = answers[i] if i < len(answers) else ""
            question.answer = answer
            answered_lines.append(f"Q: {question.question}")
            answered_lines.append(f"A: {answer}")
            answered_lines.append("")
            learnings.append((question.question, answer))

        # Replace the State section with "Ready to Implement" and answered questions
        new_state = "## State\n- Ready to Implement\n\n### Answered Questions\n" + "\n".join(answered_lines)

        # Find and replace the State section
        state_pattern = r'^## State\s*\n(.*?)(?=^## |\Z)'
        if re.search(state_pattern, content, re.MULTILINE | re.DOTALL):
            content = re.sub(state_pattern, new_state + "\n", content, flags=re.MULTILINE | re.DOTALL)
        else:
            # Insert State section after first heading
            first_heading_end = content.find('\n', content.find('#'))
            if first_heading_end != -1:
                content = content[:first_heading_end + 1] + "\n" + new_state + "\n" + content[first_heading_end + 1:]

        prd.file_path.write_text(content)
        prd.status = "pending"
        prd.questions = []

        return learnings

    def get_stats(self) -> dict[str, int]:
        """Get PRD statistics."""
        return {
            "unspecced": len(self.get_unspecced_prds()),
            "pending": len(self.get_pending_prds()),
            "questions": len(self.get_questions_prds()),
            "in_progress": 1 if self.get_in_progress_prd() else 0,
            "completed": len(self.get_completed_prds()),
            "errored": len(self.get_errored_prds()),
        }
