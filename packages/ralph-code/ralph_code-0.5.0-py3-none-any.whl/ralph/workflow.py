"""Workflow engine (state machine) for ralph-coding application."""

import json
import re
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable

from .harness_runner import HarnessRunner
from .config import get_config
from .git_manager import GitManager, GitError
from .prd_manager import PRD, PRDManager
from .spinner import SpinnerManager
from .user_stories import UserStory, UserStoryManager
from .storage import (
    get_project_state_path,
    get_progress_md_path,
    get_learnings_md_path,
    get_summarised_notes_path,
)


class WorkflowState(Enum):
    """States in the workflow state machine."""
    IDLE = "idle"
    SPECCING = "speccing"
    QUESTIONS = "questions"  # PRD has open questions needing user input
    CONVERTING = "converting"  # Converting PRD to tasks.json
    PICKING = "picking"
    IMPLEMENTING = "implementing"
    REVIEWING = "reviewing"
    TESTING = "testing"
    COMMITTING = "committing"
    ARCHIVING = "archiving"
    PAUSED = "paused"
    ERROR = "error"


class VerificationStatus(Enum):
    """Result of story verification."""
    PASSES = "passes"      # All acceptance criteria verifiably met
    FAILS = "fails"        # Implementation is wrong/incomplete
    BLOCKED = "blocked"    # Criteria cannot be verified due to external factors


# States that should display a spinner during execution
SPINNER_STATES: set[WorkflowState] = {
    WorkflowState.SPECCING,
    WorkflowState.CONVERTING,
    WorkflowState.IMPLEMENTING,
    WorkflowState.TESTING,
    WorkflowState.COMMITTING,
    WorkflowState.ARCHIVING,
}

# Default spinner messages for each state
SPINNER_MESSAGES: dict[WorkflowState, str] = {
    WorkflowState.SPECCING: "Creating PRD specification...",
    WorkflowState.CONVERTING: "Converting PRD to tasks...",
    WorkflowState.IMPLEMENTING: "Implementing user story...",
    WorkflowState.TESTING: "Running tests...",
    WorkflowState.COMMITTING: "Committing changes...",
    WorkflowState.ARCHIVING: "Archiving PRD...",
}


class WorkflowEngine:
    """
    Main workflow engine that orchestrates task execution.

    Workflow:
    1. SPECCING: Convert .txt files to .md PRDs
    2. QUESTIONS: Pause if PRDs have open questions
    3. CONVERTING: Convert picked PRD to tasks.json
    4. IMPLEMENTING: Pick and implement user stories one at a time
    5. REVIEWING: Verify story implementation
    6. COMMITTING: Commit passing stories
    7. ARCHIVING: Archive completed PRDs
    """

    def __init__(
        self,
        project_dir: Path,
        debug: bool = False,
        on_state_change: Callable[[WorkflowState, str], None] | None = None,
        on_output: Callable[[str], None] | None = None,
        use_spinner: bool = True,
    ):
        self.project_dir = project_dir
        self.debug = debug
        self.on_state_change = on_state_change
        self.on_output = on_output
        self._use_spinner = use_spinner

        self._config = get_config()
        self._prd_manager = PRDManager(project_dir)
        self._story_manager = UserStoryManager(project_dir)
        self._git_manager = GitManager(project_dir)
        self._harness_runner = HarnessRunner(project_dir, debug=debug, on_output=on_output)

        self._state = WorkflowState.IDLE
        self._current_prd: PRD | None = None
        self._current_story: UserStory | None = None
        self._iteration = 0
        self._paused = False
        self._error_message = ""
        self._completed_this_session = 0
        self._spinner: SpinnerManager | None = None

        self._load_state()

    def _load_state(self) -> None:
        """Load workflow state from disk."""
        state_path = get_project_state_path(self.project_dir)
        if state_path.exists():
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._state = WorkflowState(data.get("state", "idle"))
                self._iteration = data.get("iteration", 0)
                self._paused = data.get("paused", False)
                self._error_message = data.get("error_message", "")
                if prd_id := data.get("current_prd_id"):
                    self._current_prd = self._prd_manager.get_prd_by_id(prd_id)
                # Ensure paused flag is consistent with state
                if self._state == WorkflowState.PAUSED:
                    self._paused = True
            except (json.JSONDecodeError, IOError, ValueError):
                pass

    def _save_state(self) -> None:
        """Save workflow state to disk."""
        state_path = get_project_state_path(self.project_dir)
        data = {
            "state": self._state.value,
            "iteration": self._iteration,
            "current_prd_id": self._current_prd.id if self._current_prd else None,
            "paused": self._paused,
            "error_message": self._error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _set_state(self, new_state: WorkflowState, message: str = "") -> None:
        """Update the workflow state and manage spinner display."""
        old_state = self._state
        self._state = new_state
        self._save_state()

        # Handle spinner for loading states
        self._update_spinner(old_state, new_state, message)

        if self.on_state_change:
            self.on_state_change(new_state, message)

    def _update_spinner(
        self, old_state: WorkflowState, new_state: WorkflowState, message: str
    ) -> None:
        """Start or stop spinner based on state transition.

        Args:
            old_state: The previous workflow state.
            new_state: The new workflow state.
            message: Optional custom message for the spinner.
        """
        if not self._use_spinner:
            return

        should_show_spinner = (not self._paused) and (new_state in SPINNER_STATES)

        if should_show_spinner:
            # Determine spinner message
            spinner_message = message if message else SPINNER_MESSAGES.get(
                new_state, f"{new_state.value.capitalize()}..."
            )

            if self._spinner is None:
                # Create and start new spinner
                self._spinner = SpinnerManager(message=spinner_message)
                self._spinner.start()
            else:
                # Update existing spinner message
                self._spinner.update_message(spinner_message)
        elif self._spinner is not None:
            # Transitioning out of spinner state or paused - stop spinner
            self._stop_spinner()

    def _stop_spinner(self) -> None:
        """Stop the spinner if it's running."""
        if self._spinner is not None:
            self._spinner.stop()
            self._spinner = None

    def _output(self, message: str) -> None:
        """Send output to the callback."""
        if self.on_output:
            self.on_output(message)

    @property
    def state(self) -> WorkflowState:
        """Get the current workflow state."""
        return self._state

    @property
    def current_task(self) -> PRD | None:
        """Get the current PRD being worked on."""
        return self._current_prd

    @property
    def current_prd(self) -> PRD | None:
        """Get the current PRD being worked on."""
        return self._current_prd

    @property
    def current_story(self) -> UserStory | None:
        """Get the current user story being worked on."""
        return self._current_story

    @property
    def prd_manager(self) -> PRDManager:
        """Get the PRD manager."""
        return self._prd_manager

    @property
    def story_manager(self) -> UserStoryManager:
        """Get the user story manager."""
        return self._story_manager

    @property
    def completed_this_session(self) -> int:
        """Get the number of PRDs completed this session."""
        return self._completed_this_session

    @property
    def is_paused(self) -> bool:
        """Check if the workflow is paused."""
        return self._paused

    @property
    def error_message(self) -> str:
        """Get the current error message, if any."""
        return self._error_message

    def pause(self) -> None:
        """Pause the workflow."""
        self._paused = True
        self._set_state(WorkflowState.PAUSED, "Paused by user")

    def resume(self) -> None:
        """Resume the workflow."""
        self._paused = False
        self._error_message = ""
        self._iteration = 0  # Reset iteration counter on resume
        if self._state in (WorkflowState.PAUSED, WorkflowState.ERROR):
            self._set_state(WorkflowState.IDLE, "Resumed")

    def _ensure_git_branch(self) -> None:
        """Ensure we're on the correct git branch."""
        # Use branch from tasks.json
        branch_name = self._story_manager.get_branch_name()
        if branch_name:
            self._git_manager.ensure_on_branch(branch_name)

    def _get_learnings(self) -> str:
        """Read learnings.md content if it exists."""
        learnings_path = get_learnings_md_path(self.project_dir)
        if learnings_path.exists():
            return learnings_path.read_text()
        return ""

    def _append_learnings(self, learnings: list[tuple[str, str]]) -> None:
        """Append new learnings to learnings.md."""
        if not learnings:
            return

        learnings_path = get_learnings_md_path(self.project_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d")

        content = ""
        if learnings_path.exists():
            content = learnings_path.read_text()
        else:
            content = "# Project Learnings\n\n"

        content += f"\n## {timestamp}\n\n"
        for question, answer in learnings:
            content += f"**{question}**\n{answer}\n\n"

        learnings_path.write_text(content)

    def _filter_prd_learnings(self, prd: PRD) -> None:
        """Filter out PRD-scoped learnings after a PRD is completed."""
        learnings_path = get_learnings_md_path(self.project_dir)
        if not learnings_path.exists():
            return

        current_learnings = learnings_path.read_text()
        if not current_learnings.strip() or current_learnings.strip() == "# Project Learnings":
            return

        self._output("Filtering PRD-scoped learnings...")
        response = self._harness_runner.filter_learnings_after_prd(prd.name, current_learnings)

        if response.success and response.output.strip():
            filtered = response.output.strip()
            # Remove markdown code fence if present
            if filtered.startswith("```"):
                filtered = re.sub(r'^```\w*\n?', '', filtered)
                filtered = re.sub(r'\n?```$', '', filtered)
            learnings_path.write_text(filtered)

    def _update_progress(self, story: UserStory, status: str, notes: str = "") -> None:
        """Update progress.md with story progress.

        For BLOCKED or FAILED status, stores full structured notes to inform
        future iterations about what passed, what couldn't be verified, and
        what actions are needed to complete.
        """
        progress_path = get_progress_md_path(self.project_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        entry = f"- [{timestamp}] {story.id}: {status}"
        if notes:
            # Store full notes for BLOCKED/FAILED to inform next iteration
            # Use newlines for readability in multi-line structured notes
            if status in ("BLOCKED", "FAILED") and "\n" in notes:
                entry += f" - {notes}"
            else:
                entry += f" - {notes}"
        entry += "\n"

        if progress_path.exists():
            content = progress_path.read_text()
        else:
            content = "# Progress\n\n"

        content += entry
        progress_path.write_text(content)

    def _handle_first_blocked(self, story: UserStory, max_attempts: int) -> None:
        """Handle a story that has just reached max attempts for the first time.

        Uses a mid-tier model to analyze the failure and determine if:
        1. The story can be retried with adjustments (gets one more attempt)
        2. The story needs human intervention

        Args:
            story: The user story that reached max attempts.
            max_attempts: The configured max attempts value.
        """
        self._output(f"Story {story.id} reached max attempts. Analyzing...")

        # Archive full notes if debug mode is enabled
        full_notes = story.notes
        if self.debug:
            self._archive_full_notes(story, full_notes, "")  # Summary added later

        # Get project context
        project_context = self._harness_runner.detect_project_context()

        # Get git diff
        git_diff = self._git_manager.get_diff()

        # Analyze the blocked story
        response = self._harness_runner.analyze_blocked_story(
            story_prompt=story.get_prompt(),
            full_notes=full_notes,
            git_diff=git_diff,
            project_context=project_context,
        )

        if not response.success:
            # Analysis failed - fall back to simple blocking
            self._output(f"Analysis failed: {response.error}. Marking as blocked.")
            story.blocked = True
            self._story_manager.update_story(story)
            self._update_progress(story, "BLOCKED", f"Analysis failed: {response.error}")
            return

        # Parse the response
        output = response.output
        action = self._extract_action_from_analysis(output)
        summary = self._extract_summary_from_analysis(output)
        recommendations = self._extract_recommendations_from_analysis(output)

        # Update archived notes with summary (debug mode only)
        if self.debug and summary:
            self._archive_full_notes(story, full_notes, summary)

        if action == "RETRY":
            # Give the story one more attempt
            story.attempts = max_attempts - 1  # Decrement to allow one more retry
            # Replace notes with summary + recommendations
            story.notes = f"ANALYSIS SUMMARY:\n{summary}\n\nRECOMMENDATIONS:\n{recommendations}"
            self._output(f"Story {story.id} will retry with analysis recommendations")
            self._story_manager.update_story(story)
            self._update_progress(story, "RETRY_WITH_ANALYSIS", summary)
        else:
            # Needs human intervention
            story.blocked = True
            story.needs_intervention = True
            # Replace notes with summary
            story.notes = f"ANALYSIS SUMMARY:\n{summary}\n\nINTERVENTION NEEDED:\n{self._extract_intervention_reason(output)}"
            self._output(f"Story {story.id} needs human intervention")
            self._story_manager.update_story(story)
            self._update_progress(story, "NEEDS_INTERVENTION", summary)

    def _archive_full_notes(self, story: UserStory, full_notes: str, summary: str) -> None:
        """Archive full notes to summarised_notes.txt (debug mode only).

        Args:
            story: The user story being archived.
            full_notes: The complete notes from all attempts.
            summary: The analysis summary (may be empty on first call).
        """
        notes_path = get_summarised_notes_path(self.project_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = f"""
{'='*60}
Story: {story.id} - {story.title}
Timestamp: {timestamp}
{'='*60}

FULL NOTES:
{full_notes}

"""
        if summary:
            entry += f"""ANALYSIS SUMMARY:
{summary}

"""

        # Append to file (create if doesn't exist)
        with open(notes_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def _extract_action_from_analysis(self, output: str) -> str:
        """Extract the ACTION from analysis output.

        Args:
            output: The full analysis output from the harness.

        Returns:
            'RETRY' or 'NEEDS_INTERVENTION'
        """
        output_upper = output.upper()
        if "ACTION: RETRY" in output_upper:
            return "RETRY"
        elif "ACTION: NEEDS_INTERVENTION" in output_upper:
            return "NEEDS_INTERVENTION"
        # Default to intervention if unclear
        return "NEEDS_INTERVENTION"

    def _extract_summary_from_analysis(self, output: str) -> str:
        """Extract the SUMMARY section from analysis output.

        Args:
            output: The full analysis output from the harness.

        Returns:
            The summary text, or empty string if not found.
        """
        if "SUMMARY:" not in output:
            return ""

        # Find the start of SUMMARY section
        start = output.find("SUMMARY:") + len("SUMMARY:")

        # Find the end (next section marker or end of string)
        end = len(output)
        for marker in ["ANALYSIS:", "RECOMMENDATIONS:", "INTERVENTION_REASON:"]:
            pos = output.find(marker, start)
            if pos != -1 and pos < end:
                end = pos

        return output[start:end].strip()

    def _extract_recommendations_from_analysis(self, output: str) -> str:
        """Extract the RECOMMENDATIONS section from analysis output.

        Args:
            output: The full analysis output from the harness.

        Returns:
            The recommendations text, or empty string if not found.
        """
        if "RECOMMENDATIONS:" not in output:
            return ""

        # Find the start of RECOMMENDATIONS section
        start = output.find("RECOMMENDATIONS:") + len("RECOMMENDATIONS:")

        # Find the end (next section marker or end of string)
        end = len(output)
        for marker in ["INTERVENTION_REASON:"]:
            pos = output.find(marker, start)
            if pos != -1 and pos < end:
                end = pos

        return output[start:end].strip()

    def _extract_intervention_reason(self, output: str) -> str:
        """Extract the INTERVENTION_REASON section from analysis output.

        Args:
            output: The full analysis output from the harness.

        Returns:
            The intervention reason text, or default message if not found.
        """
        if "INTERVENTION_REASON:" not in output:
            return "Human intervention required to resolve this issue."

        # Find the start of INTERVENTION_REASON section
        start = output.find("INTERVENTION_REASON:") + len("INTERVENTION_REASON:")

        return output[start:].strip()

    def _clear_progress(self) -> None:
        """Clear progress.md for new PRD (keep only header and learnings notes)."""
        progress_path = get_progress_md_path(self.project_dir)
        progress_path.write_text("# Progress\n\n")

    def _spec_prds(self) -> bool:
        """Convert unspecced PRDs (.txt) to specced PRDs (.md). Returns True if any were specced."""
        unspecced = self._prd_manager.get_unspecced_prds()
        if not unspecced:
            return False

        self._set_state(WorkflowState.SPECCING, f"Creating PRDs for {len(unspecced)} tasks")

        # Get learnings to inform PRD creation
        learnings = self._get_learnings()

        for prd in unspecced:
            self._output(f"Creating PRD: {prd.name}")

            # Get the task description from the .txt file
            task_description = prd.content

            # Use Claude to create a full PRD
            response = self._harness_runner.create_prd(task_description, learnings=learnings)

            if not response.success:
                self._output(f"Failed to create PRD: {response.error}")
                continue

            # The response should be markdown PRD content
            prd_content = response.output.strip()

            # Remove any markdown code fence if present
            if prd_content.startswith("```"):
                prd_content = re.sub(r'^```\w*\n?', '', prd_content)
                prd_content = re.sub(r'\n?```$', '', prd_content)

            try:
                # Convert .txt to .md
                new_prd = self._prd_manager.spec_prd(prd, prd_content)
                self._output(f"Created PRD: {new_prd.file_path.name}")

                # Check if it has open questions
                if new_prd.status == "questions":
                    self._output(f"PRD has {len(new_prd.questions)} open questions")
            except Exception as e:
                self._output(f"Failed to save PRD: {e}")

        # Reload to pick up changes
        self._prd_manager.reload()
        return True

    def _pick_next_prd(self) -> PRD | None:
        """Pick the next PRD to implement."""
        # First check for in-progress PRD
        in_progress = self._prd_manager.get_in_progress_prd()
        if in_progress:
            return in_progress

        # Get pending PRDs (specced but not started)
        pending = self._prd_manager.get_pending_prds()
        if not pending:
            return None

        # If only one PRD, pick it
        if len(pending) == 1:
            return pending[0]

        self._set_state(WorkflowState.PICKING, "Picking next PRD")

        # Ask Claude to pick
        prds_summary = "\n".join([
            f"- ID: {p.id}\n  Name: {p.name}\n  File: {p.file_path.name}"
            for p in pending
        ])

        response = self._harness_runner.pick_next_task(prds_summary)

        if response.success:
            # Parse the response for PRD ID
            match = re.search(r'TASK_ID:\s*([a-f0-9-]+)', response.output)
            if match:
                prd_id = match.group(1)
                prd = self._prd_manager.get_prd_by_id(prd_id)
                if prd:
                    return prd

        # Fallback: return first pending PRD
        return pending[0] if pending else None

    def _convert_prd_to_tasks(self, prd: PRD) -> bool:
        """Convert a PRD to tasks.json. Returns True on success."""
        self._set_state(WorkflowState.CONVERTING, f"Converting PRD to tasks: {prd.name}")

        # Get project name from directory
        project_name = self.project_dir.name

        response = self._harness_runner.convert_prd_to_tasks(
            prd.content, project_name, branch_prefix=self._config.branch_prefix
        )

        if not response.success:
            self._output(f"Failed to convert PRD: {response.error}")
            return False

        # Extract JSON from response
        tasks_json = response.output.strip()

        # Remove markdown code fence if present
        if tasks_json.startswith("```"):
            tasks_json = re.sub(r'^```\w*\n?', '', tasks_json)
            tasks_json = re.sub(r'\n?```$', '', tasks_json)

        try:
            # Create tasks.json
            tasks_file = self._story_manager.create_from_json(tasks_json, str(prd.file_path))
            self._output(f"Created tasks.json with {len(tasks_file.user_stories)} stories")

            # Clear progress for new PRD
            self._clear_progress()

            return True
        except Exception as e:
            self._output(f"Failed to create tasks.json: {e}")
            return False

    def _implement_story(self, story: UserStory) -> bool:
        """Implement a single user story. Returns True on success."""
        self._current_story = story
        self._set_state(
            WorkflowState.IMPLEMENTING,
            f"Implementing: {story.id} - {story.title}"
        )

        # Build context from progress and learnings
        context = ""
        progress_path = get_progress_md_path(self.project_dir)
        if progress_path.exists():
            context += f"Progress so far:\n{progress_path.read_text()}\n\n"

        learnings = self._get_learnings()
        if learnings:
            context += f"Project learnings:\n{learnings}\n\n"

        # Get the story prompt
        story_prompt = story.get_prompt()

        # Implement the story
        response = self._harness_runner.implement_story(story_prompt, context)

        if not response.success:
            self._update_progress(story, "FAILED", response.error)
            story.mark_failed(response.error)
            self._story_manager.update_story(story)
            self._output(f"Implementation failed: {response.error}")
            return False

        return True

    def _verify_story(self, story: UserStory) -> tuple[VerificationStatus, str]:
        """Verify a story implementation. Returns (status, notes)."""
        self._set_state(WorkflowState.REVIEWING, f"Reviewing: {story.id}")

        # Get git diff for review
        git_diff = self._git_manager.get_diff()

        response = self._harness_runner.verify_story(story.get_prompt(), git_diff)

        if not response.success:
            return VerificationStatus.FAILS, f"Verification error: {response.error}"

        # Parse response
        output = response.output.upper()

        # Determine status (check BLOCKED before FAILS since BLOCKED is more specific)
        if "STATUS: PASSES" in output:
            status = VerificationStatus.PASSES
        elif "STATUS: BLOCKED" in output:
            status = VerificationStatus.BLOCKED
        else:
            status = VerificationStatus.FAILS

        # Extract notes (everything after NOTES: or FEEDBACK: for backwards compat)
        notes = ""
        raw_output = response.output
        if "NOTES:" in raw_output:
            notes = raw_output.split("NOTES:", 1)[1].strip()
        elif "FEEDBACK:" in raw_output:
            notes = raw_output.split("FEEDBACK:", 1)[1].strip()

        return status, notes

    def _commit_story(self, story: UserStory) -> bool:
        """Commit changes for a passing story. Returns True on success."""
        self._set_state(WorkflowState.COMMITTING, f"Committing: {story.id}")

        # Check if there are already staged changes or unstaged changes
        has_staged = self._git_manager.has_staged_changes()
        unstaged_files = self._git_manager.get_unstaged_files()

        if not has_staged and not unstaged_files:
            return True

        try:
            # Ask LLM to identify which unstaged files should be committed
            if unstaged_files:
                self._output(f"Reviewing {len(unstaged_files)} changed files...")
                response = self._harness_runner.stage_story_changes(
                    story.id, story.title, unstaged_files
                )

                if response.success:
                    files_to_stage = self._parse_files_to_stage(response.output)
                    if files_to_stage:
                        self._output(f"Staging {len(files_to_stage)} files...")
                        self._git_manager.stage_files(files_to_stage)

            # Check if we have anything to commit now
            if not self._git_manager.has_staged_changes():
                self._output("No files to commit")
                return True

            # Generate commit message
            status = self._git_manager.get_status()
            response = self._harness_runner.generate_commit_message(
                f"Story: {story.id} - {story.title}\n\nChanges:\n{status}"
            )

            if response.success and response.output.strip():
                message = response.output.strip()
            else:
                message = f"{story.id}: {story.title}"

            self._git_manager.commit_staged(message)
            return True

        except GitError as e:
            self._output(f"Git error: {e}")
            return False

    def _parse_files_to_stage(self, output: str) -> list[str]:
        """Parse the FILES_TO_STAGE section from LLM output.

        Args:
            output: The full output from stage_story_changes().

        Returns:
            List of file paths to stage, empty if none or NONE specified.
        """
        if "FILES_TO_STAGE:" not in output:
            return []

        # Extract content after FILES_TO_STAGE:
        content = output.split("FILES_TO_STAGE:", 1)[1].strip()

        # Check for NONE response
        if content.upper().startswith("NONE"):
            return []

        # Parse file paths (one per line)
        files = []
        for line in content.split("\n"):
            line = line.strip()
            # Skip empty lines and common artifacts
            if line and not line.startswith("#") and not line.startswith("-"):
                # Handle markdown list format if LLM uses it
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    files.append(line)

        return files

    def _archive_prd(self, prd: PRD) -> None:
        """Archive a completed PRD."""
        self._set_state(WorkflowState.ARCHIVING, f"Archiving: {prd.name}")

        # Create archive directory
        timestamp = datetime.now().strftime("%Y-%m-%d")
        archive_dir = self.project_dir / "ARCHIVED_PRDs" / f"{timestamp}-{prd.file_path.stem}"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Archive tasks.json
        self._story_manager.archive(archive_dir)

        # Archive progress.md
        progress_path = get_progress_md_path(self.project_dir)
        if progress_path.exists():
            shutil.copy(progress_path, archive_dir / "progress.md")

        # Move PRD to archive
        if prd.file_path.exists():
            shutil.copy(prd.file_path, archive_dir / prd.file_path.name)
            prd.file_path.unlink()

        # Filter learnings - remove PRD-scoped items, keep project-wide ones
        self._filter_prd_learnings(prd)

        # Clear tasks.json
        self._story_manager.clear()

        # Clear progress
        self._clear_progress()

        self._output(f"Archived PRD to {archive_dir}")

    def _handle_error(self, error_message: str, prd: PRD | None = None) -> bool:
        """Handle an error based on configuration."""
        self._error_message = error_message
        error_mode = self._config.on_error

        if error_mode in ("block", "skip") and prd:
            prd.error(error_message)
            self._prd_manager.update_prd_status(prd, "errored")
            self._output(f"PRD errored: {error_message}")
            return False

        elif error_mode == "pause":
            self._paused = True
            self._set_state(WorkflowState.ERROR, error_message)
            return False

        # retry mode is handled in the main step() method
        return False

    def get_prds_with_questions(self) -> list[PRD]:
        """Get all PRDs that have open questions needing answers."""
        return self._prd_manager.get_questions_prds()

    def answer_questions(self, prd: PRD, answers: list[str]) -> None:
        """Answer open questions for a PRD and save any learnings."""
        learnings = self._prd_manager.answer_prd_questions(prd, answers)
        if learnings:
            self._append_learnings(learnings)
            self._output(f"Saved {len(learnings)} learnings from PRD questions")
        self._prd_manager.reload()

        # If no more PRDs have questions, reset workflow state
        if not self._prd_manager.get_questions_prds():
            self._paused = False
            if self._state == WorkflowState.QUESTIONS:
                self._set_state(WorkflowState.IDLE, "Questions answered")

    def get_story_progress(self) -> tuple[int, int, int]:
        """Get story progress as (completed, total, percent)."""
        completed, total = self._story_manager.get_progress()
        percent = self._story_manager.get_progress_percent()
        return completed, total, percent

    def step(self) -> bool:
        """
        Execute one step of the workflow.

        Returns True if there's more work to do, False if idle or paused.
        """
        if self._paused:
            return False

        # Check iteration limit
        if self._iteration >= self._config.max_iterations:
            self._output("Max iterations reached")
            if self._config.pause_on_completion:
                self.pause()
            return False

        self._iteration += 1

        try:
            # Reload to pick up any changes
            self._prd_manager.reload()
            self._story_manager.reload()

            # Step 1: Create PRDs from unspecced .txt files
            if self._prd_manager.get_unspecced_prds():
                self._spec_prds()
                return True

            # Step 2: Check for PRDs with open questions - pause for user input
            questions_prds = self._prd_manager.get_questions_prds()
            if questions_prds:
                self._set_state(WorkflowState.QUESTIONS, f"{len(questions_prds)} PRD(s) have open questions")
                self._paused = True
                return False

            # Step 3: Check if we have tasks.json with incomplete stories
            if self._story_manager.has_tasks() and not self._story_manager.is_complete():
                # Ensure we're on the right branch
                self._ensure_git_branch()

                # Pick next story (respecting max attempts)
                max_attempts = self._config.max_story_attempts
                story = self._story_manager.get_next_story(max_attempts)

                if story is None:
                    # No actionable stories - all are either passed or blocked
                    # Pause and let user decide what to do
                    self._output("All remaining stories are blocked (max attempts exceeded)")
                    self._paused = True
                    self._set_state(WorkflowState.PAUSED, "Stories blocked - manual intervention needed")
                    return False

                # Implement the story
                if not self._implement_story(story):
                    # Failed - story already marked, try next
                    return True

                # Verify the story
                status, notes = self._verify_story(story)

                if status == VerificationStatus.PASSES:
                    story.mark_passing()
                    self._story_manager.update_story(story)
                    self._update_progress(story, "PASSED", notes)
                    self._output(f"Story {story.id} passed!")

                    # Commit the changes
                    self._commit_story(story)

                elif status == VerificationStatus.BLOCKED:
                    # BLOCKED means implementation looks correct but verification
                    # couldn't complete (e.g., can't run tests, pre-existing errors)
                    # Record as BLOCKED with full notes for next iteration to address
                    story.mark_failed(notes)
                    self._story_manager.update_story(story)
                    self._update_progress(story, "BLOCKED", notes)

                    # Extract a brief summary for output
                    brief = notes.split("\n")[0][:100] if notes else "Verification blocked"
                    self._output(f"Story {story.id} blocked: {brief}...")
                    self._output("See progress.md for full blocker details and next steps")

                else:  # VerificationStatus.FAILS
                    story.mark_failed(notes)
                    # Check if this story is now blocked due to max attempts
                    if story.attempts >= max_attempts:
                        self._handle_first_blocked(story, max_attempts)
                    else:
                        brief = notes.split("\n")[0][:100] if notes else "Implementation failed"
                        self._output(f"Story {story.id} failed (attempt {story.attempts}/{max_attempts}): {brief}...")
                        self._story_manager.update_story(story)
                        self._update_progress(story, "FAILED", notes)

                self._current_story = None
                return True

            # Step 4: Check if tasks.json is complete - archive the PRD and move to next
            if self._story_manager.has_tasks() and self._story_manager.is_complete():
                prd_file = self._story_manager.get_prd_file()
                if prd_file:
                    # Find the PRD
                    for prd in self._prd_manager.get_all_prds():
                        if str(prd.file_path) == prd_file:
                            prd.complete()
                            self._prd_manager.update_prd_status(prd, "completed")
                            self._archive_prd(prd)
                            self._completed_this_session += 1
                            self._output(f"Completed PRD: {prd.name}")
                            break
                else:
                    # No PRD file recorded, just clear tasks
                    self._story_manager.clear()

                # Clear current PRD so we pick the next one
                self._current_prd = None
                self._prd_manager.reload()

                return True  # Continue to pick next PRD

            # Step 5: Pick next PRD if no current one and no tasks
            if not self._story_manager.has_tasks():
                next_prd = self._pick_next_prd()
                if not next_prd:
                    self._set_state(WorkflowState.IDLE, "No PRDs available")
                    if self._config.pause_on_completion:
                        self.pause()
                    return False

                # Mark PRD as in progress
                if next_prd.status != "in_progress":
                    next_prd.start()
                    self._prd_manager.update_prd_status(next_prd, "in_progress")

                self._current_prd = next_prd

                # Convert PRD to tasks.json
                if not self._convert_prd_to_tasks(next_prd):
                    self._handle_error("Failed to convert PRD to tasks", next_prd)
                    self._current_prd = None
                    return True

                # Ensure we're on the right branch
                self._ensure_git_branch()

                return True

            return False

        except GitError as e:
            # Git errors always pause - user needs to fix something
            self._error_message = str(e)
            self._paused = True
            self._set_state(WorkflowState.ERROR, str(e))
            return False

        except Exception as e:
            self._handle_error(str(e), self._current_prd)
            # Only continue if on_error is "retry", otherwise stop
            return self._config.on_error == "retry"

    def run(self) -> None:
        """Run the workflow until completion or pause."""
        while self.step():
            pass
