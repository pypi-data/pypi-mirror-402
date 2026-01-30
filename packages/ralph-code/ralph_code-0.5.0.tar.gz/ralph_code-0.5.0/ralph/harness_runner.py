"""Harness CLI integration for ralph-coding application.

This module provides the execution layer for running AI prompts through
CLI harness tools. It handles:

- Command building with harness-specific CLI flags
- Model name mapping between internal names and harness-specific names
- Rate limit detection and retry with exponential backoff
- Debug logging for troubleshooting

Key classes:
- HarnessRunner: Main class for executing prompts through the configured harness
- HarnessResponse: Dataclass representing the result of a harness execution

The module also provides backwards compatibility aliases (ClaudeRunner, ClaudeResponse)
for code that hasn't migrated to the new naming.

Example usage:
    from ralph.harness_runner import HarnessRunner

    runner = HarnessRunner(project_dir=Path("."))

    # Run a simple prompt
    response = runner.run("Explain this code")
    if response.success:
        print(response.output)

    # Implement a story (allows file writes)
    response = runner.implement_story(story_prompt, context)

See HARNESS_ARCHITECTURE.md for documentation on CLI flag patterns per harness type.
"""

import json
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from .config import get_config
from .harness import Harness, HarnessType
from .storage import get_project_logs_dir


@dataclass
class HarnessResponse:
    """Represents a response from a harness CLI execution.

    Attributes:
        success: True if the command exited with code 0, False otherwise.
        output: The stdout content from the harness CLI.
        error: The stderr content, typically containing error messages.
        rate_limited: True if rate limiting was detected in the response.
        cost: Estimated cost of the API call (if available from harness).
    """

    success: bool
    output: str
    error: str = ""
    rate_limited: bool = False
    cost: float = 0.0


# Model mapping for different harness types.
# Maps Ralph's internal model names (haiku, sonnet, opus) to harness-specific names.
# This allows users to select models using consistent names regardless of harness.
#
# When adding a new harness type, add a mapping entry here. The keys are Ralph's
# internal names, values are what gets passed to --model flag.
HARNESS_MODEL_MAPPING: dict[HarnessType, dict[str, str]] = {
    "claude": {
        # Claude CLI uses the same model names internally
        "haiku": "haiku",
        "sonnet": "sonnet",
        "opus": "opus",
    },
    "codex": {
        # Codex maps to OpenAI/Codex model names
        "haiku": "gpt-5.1-codex-mini",
        "sonnet": "gpt-5.2-codex",
        "opus": "gpt-5.1-codex-max",
    },
    "custom": {
        # Custom harnesses default to Claude-like names
        # Users can override by using harness-native model names directly
        "haiku": "haiku",
        "sonnet": "sonnet",
        "opus": "opus",
    },
}


class HarnessRunner:
    """Executes prompts through the configured AI harness CLI tool.

    HarnessRunner is the main interface for running AI prompts in Ralph. It:
    - Builds CLI commands with the correct flags for each harness type
    - Maps internal model names to harness-specific model names
    - Handles rate limiting with configurable retry and exponential backoff
    - Provides logging for debugging harness interactions

    The runner lazily loads the Harness object from configuration and caches it
    for the lifetime of the runner instance.

    Attributes:
        project_dir: Working directory for command execution.
        debug: If True, enables logging of commands and responses.
        on_output: Optional callback for streaming status updates to UI.

    Example:
        runner = HarnessRunner(Path("/my/project"), debug=True)

        # Simple prompt
        result = runner.run("Explain the code in main.py")

        # Implementation with file writes enabled
        result = runner.implement_story(story_spec, context="Use async/await")

        # PRD generation (uses lighter model)
        prd = runner.create_prd("Add user authentication")

    Note:
        All high-level methods (create_prd, implement_story, etc.) are convenience
        wrappers around run() with appropriate prompt templates and settings.
    """

    # Regex patterns for detecting rate limit errors in harness output.
    # When matched, the runner will retry with exponential backoff if configured.
    RATE_LIMIT_PATTERNS = [
        r"rate.?limit",
        r"too many requests",
        r"quota exceeded",
        r"429",  # HTTP status code often present in error messages
    ]

    def __init__(
        self,
        project_dir: Path,
        debug: bool = False,
        on_output: Callable[[str], None] | None = None,
    ):
        """Initialize the HarnessRunner.

        Args:
            project_dir: Working directory for running harness commands.
                         All file paths in prompts should be relative to this.
            debug: If True, log all commands and responses to a timestamped
                   file in the project's logs directory.
            on_output: Optional callback invoked with status messages (e.g.,
                       "Rate limited. Waiting 60s...") for UI feedback.
        """
        self.project_dir = project_dir
        self.debug = debug
        self.on_output = on_output
        self._config = get_config()
        self._log_file: Path | None = None
        self._harness: Harness | None = None  # Lazily loaded from config

        if debug:
            self._setup_logging()

    def _get_harness(self) -> Harness:
        """Get the harness object, creating it lazily from config."""
        if self._harness is None:
            self._harness = Harness.from_config(self._config.harness)
        return self._harness

    def _setup_logging(self) -> None:
        """Setup debug logging."""
        logs_dir = get_project_logs_dir(self.project_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._log_file = logs_dir / f"{timestamp}.log"

    def _log(self, message: str) -> None:
        """Log a message to the debug log file."""
        if self._log_file:
            with open(self._log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] {message}\n")

    def _is_rate_limited(self, output: str, error: str) -> bool:
        """Check if the response indicates rate limiting."""
        combined = (output + error).lower()
        for pattern in self.RATE_LIMIT_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return True
        return False

    def _map_model(self, model: str) -> str:
        """Map the internal model type to harness-specific model name."""
        harness = self._get_harness()
        mapping = HARNESS_MODEL_MAPPING.get(harness.type, HARNESS_MODEL_MAPPING["custom"])
        return mapping.get(model, model)

    def _build_command(
        self,
        prompt: str,
        model: str | None = None,
        print_output: bool = True,
        allow_writes: bool = False,
    ) -> list[str]:
        """Build the harness CLI command with harness-specific flags.

        This method handles the differences in CLI interfaces between harness types:

        Claude CLI:
            claude --model <model> --print [--dangerously-skip-permissions] -p "<prompt>"

        Codex CLI (non-interactive):
            codex exec --model <model> --sandbox <mode> "<prompt>"

        Custom (defaults to Claude-like):
            custom --model <model> --print [--dangerously-skip-permissions] -p "<prompt>"

        Args:
            prompt: The prompt text to send to the harness.
            model: Model name (internal name like 'sonnet', mapped automatically).
                   If None, uses the worker model from configuration.
            print_output: If True, add flags for non-interactive output mode.
            allow_writes: If True, add flags to permit file modifications.

        Returns:
            List of command arguments suitable for subprocess.run().
        """
        harness = self._get_harness()
        model = model or self._config.worker_model
        mapped_model = self._map_model(model)

        cmd = [harness.path]

        # Build command based on harness type
        if harness.type == "claude":
            # Claude CLI flags
            cmd.extend(["--model", mapped_model])

            if print_output:
                cmd.append("--print")

            if allow_writes:
                cmd.append("--dangerously-skip-permissions")

            cmd.extend(["-p", prompt])

        elif harness.type == "codex":
            # Codex CLI uses 'exec' subcommand for non-interactive execution
            if print_output:
                cmd.append("exec")

            cmd.extend(["--model", mapped_model])

            # Codex uses --sandbox for write permissions
            if allow_writes:
                cmd.extend(["--sandbox", "workspace-write", "--full-auto"])
            else:
                cmd.extend(["--sandbox", "read-only"])

            # Codex uses positional argument for prompt
            cmd.append(prompt)

        else:
            # Custom harness - use Claude-like flags as default
            cmd.extend(["--model", mapped_model])

            if print_output:
                cmd.append("--print")

            if allow_writes:
                cmd.append("--dangerously-skip-permissions")

            cmd.extend(["-p", prompt])

        return cmd

    def run(
        self,
        prompt: str,
        model: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 60.0,
        allow_writes: bool = False,
    ) -> HarnessResponse:
        """
        Run a prompt through the harness CLI.

        Args:
            prompt: The prompt to send to the harness
            model: Model to use. Uses worker model config if not specified.
            max_retries: Maximum retries on rate limit
            retry_delay: Base delay between retries (doubles each retry)
            allow_writes: Whether to allow file writes (for implementation tasks)

        Returns:
            HarnessResponse with the result
        """
        cmd = self._build_command(prompt, model, allow_writes=allow_writes)

        self._log(f"Command: {' '.join(cmd)}")
        self._log(f"Prompt:\n{prompt}\n")

        attempt = 0
        current_delay = retry_delay

        while attempt <= max_retries:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                )

                output = result.stdout
                error = result.stderr

                self._log(f"Output:\n{output}\n")
                if error:
                    self._log(f"Error:\n{error}\n")

                # Check for rate limiting (only on failure)
                if result.returncode != 0 and self._is_rate_limited(output, error):
                    if self._config.wait_on_rate_limit and attempt < max_retries:
                        self._log(f"Rate limited. Waiting {current_delay}s before retry...")
                        if self.on_output:
                            self.on_output(f"Rate limited. Waiting {current_delay:.0f}s...")
                        time.sleep(current_delay)
                        attempt += 1
                        current_delay *= 2  # Exponential backoff
                        continue

                    return HarnessResponse(
                        success=False,
                        output=output,
                        error=error,
                        rate_limited=True,
                    )

                return HarnessResponse(
                    success=result.returncode == 0,
                    output=output,
                    error=error,
                )

            except FileNotFoundError:
                harness = self._get_harness()
                error_msg = f"Harness not found: {harness.path}"
                self._log(f"Error: {error_msg}")
                return HarnessResponse(
                    success=False,
                    output="",
                    error=error_msg,
                )
            except Exception as e:
                error_msg = str(e)
                self._log(f"Exception: {error_msg}")
                return HarnessResponse(
                    success=False,
                    output="",
                    error=error_msg,
                )

        return HarnessResponse(
            success=False,
            output="",
            error="Max retries exceeded",
            rate_limited=True,
        )

    def create_prd(self, task_description: str, learnings: str = "") -> HarnessResponse:
        """
        Create a PRD (Product Requirements Document) for a task using the prd skill format.

        Args:
            task_description: Brief description of the task/feature
            learnings: Optional learnings content to inform the PRD

        Returns:
            HarnessResponse containing the PRD in markdown format
        """
        # Read the PRD skill file for guidance
        skill_path = self.project_dir / "skills" / "prd" / "SKILL.md"
        skill_content = ""
        if skill_path.exists():
            skill_content = skill_path.read_text()

        learnings_section = ""
        if learnings:
            learnings_section = f"""
PROJECT LEARNINGS (use these to inform your PRD):
{learnings}
"""

        prompt = f"""Create a Product Requirements Document (PRD) for the following feature/task.

{f"PRD SKILL GUIDE:{chr(10)}{skill_content}" if skill_content else ""}

TASK DESCRIPTION:
{task_description}
{learnings_section}
IMPORTANT: You MUST include a "## State" section in the PRD with one of these values:
- "Ready to Implement" - if the PRD is complete and has no ambiguities
- "Open Questions" - if there are questions that need answers before implementation

If there are open questions, list them one per line after the State section.
For multi-choice questions, include a JSON array of options at the end of the line.
Example:
## State
- Open Questions
How should authentication be handled? ["JWT", "Session cookies", "OAuth2"]
What database should be used? ["PostgreSQL", "SQLite", "MySQL"]

Output ONLY the PRD markdown content, nothing else. Start with "# PRD:"."""

        return self.run(prompt, model=self._config.summary_model)

    def pick_next_task(self, tasks_summary: str) -> HarnessResponse:
        """
        Ask the harness to pick the most important task to work on next.

        Args:
            tasks_summary: Summary of available tasks

        Returns:
            HarnessResponse with the task selection
        """
        prompt = f"""You are helping to prioritize tasks. Given the following list of available tasks, pick the most important one to work on next.

Consider:
- Dependencies (tasks that unblock other tasks are higher priority)
- Foundational work (core functionality before features)
- Complexity (start with simpler tasks to build momentum)

Available tasks:
{tasks_summary}

Respond with just the task ID of the task you recommend working on next, followed by a brief explanation.

Format:
TASK_ID: <uuid>
REASON: <brief explanation>"""

        return self.run(prompt, model=self._config.summary_model)

    def implement_task(self, task_spec: str, context: str = "") -> HarnessResponse:
        """
        Ask the harness to implement a task.

        Args:
            task_spec: The full task specification
            context: Additional context about the project

        Returns:
            HarnessResponse with the implementation
        """
        prompt = f"""Please implement the following task:

{task_spec}

{f"Additional context: {context}" if context else ""}

Implement this task completely. Create or modify files as needed. Run tests if applicable."""

        return self.run(prompt, allow_writes=True)

    def write_tests(self, implementation_summary: str) -> HarnessResponse:
        """
        Ask the harness to write tests for an implementation.

        Args:
            implementation_summary: Summary of what was implemented

        Returns:
            HarnessResponse with the test implementation
        """
        prompt = f"""Please write tests for the following implementation:

{implementation_summary}

Create comprehensive tests that cover:
- Happy path scenarios
- Edge cases
- Error handling

Place tests in the appropriate test directory following the project's conventions."""

        return self.run(prompt, allow_writes=True)

    def verify_implementation(
        self, task_spec: str, git_diff: str, require_tests: bool = False
    ) -> HarnessResponse:
        """
        Use the harness to verify if implementation meets acceptance criteria.

        Args:
            task_spec: The task specification with acceptance criteria
            git_diff: The git diff of changes made
            require_tests: Whether tests are required for completion

        Returns:
            HarnessResponse with verification result (COMPLETE/INCOMPLETE with feedback)
        """
        prompt = f"""You are a code reviewer. Review the following implementation against the task requirements.

TASK SPECIFICATION:
{task_spec}

GIT DIFF OF CHANGES:
{git_diff if git_diff else "(No changes detected)"}

{"IMPORTANT: Tests are required for this task. Check that appropriate tests were created." if require_tests else ""}

Evaluate whether the implementation:
1. Addresses all acceptance criteria
2. Actually modifies/creates the necessary files (not just documentation)
3. {"Includes appropriate tests" if require_tests else "Is functionally complete"}

Respond in this exact format:
STATUS: COMPLETE or INCOMPLETE
FEEDBACK: <If INCOMPLETE, explain what's missing or needs to be fixed. If COMPLETE, briefly confirm what was done.>"""

        return self.run(prompt, model=self._config.summary_model)

    def generate_commit_message(self, changes_summary: str) -> HarnessResponse:
        """
        Ask the harness to generate a commit message for changes.

        Args:
            changes_summary: Summary of the changes made

        Returns:
            HarnessResponse with the commit message
        """
        prompt = f"""Generate a concise but descriptive git commit message for the following changes:

{changes_summary}

Follow conventional commit format if appropriate. Keep the first line under 72 characters.
Respond with just the commit message, nothing else.
Do NOT include Co-Authored-By, Signed-off-by, or any other git trailers."""

        return self.run(prompt, model=self._config.summary_model)

    def update_learnings(self, session_summary: str, current_learnings: str) -> HarnessResponse:
        """
        Ask the harness to update the learnings file with new insights.

        Args:
            session_summary: Summary of the current session
            current_learnings: Current contents of learnings.md

        Returns:
            HarnessResponse with updated learnings content
        """
        prompt = f"""Based on the following session, identify any new learnings or insights that should be documented.

Session summary:
{session_summary}

Current learnings.md content:
{current_learnings if current_learnings else "(empty)"}

If there are new insights worth documenting, provide the updated content for learnings.md.
If there's nothing new to add, respond with "NO_UPDATES".

Keep the format clean and organized with clear sections."""

        return self.run(prompt, model=self._config.summary_model)

    def filter_learnings_after_prd(self, prd_name: str, current_learnings: str) -> HarnessResponse:
        """
        Filter learnings after a PRD is completed, removing PRD-scoped items.

        Args:
            prd_name: Name of the completed PRD
            current_learnings: Current contents of learnings.md

        Returns:
            HarnessResponse with filtered learnings content (only project-wide ones)
        """
        prompt = f"""A PRD has been completed: "{prd_name}"

Review the current learnings and remove any that are scoped to this specific PRD.

REMOVE learnings about:
- Package/library choices for this specific feature
- Code style decisions specific to this implementation
- Implementation strategies or technical approaches for this PRD
- Design decisions that only apply to this feature

KEEP learnings about:
- Project-wide conventions or standards
- Development workflow preferences
- General architectural decisions
- User preferences that apply across features
- Things the user explicitly wants remembered for future work

Current learnings.md:
{current_learnings}

Return the filtered learnings.md content with only project-wide learnings.
If all learnings should be removed, return just the header:
# Project Learnings

Preserve the markdown format and date sections for any remaining learnings."""

        return self.run(prompt, model=self._config.summary_model)

    def update_progress(self, task_name: str, status: str, notes: str = "") -> HarnessResponse:
        """
        Generate a progress update for progress.md.

        Args:
            task_name: Name of the task
            status: Current status
            notes: Additional notes

        Returns:
            HarnessResponse with progress update content
        """
        prompt = f"""Generate a brief progress update entry for the following:

Task: {task_name}
Status: {status}
Notes: {notes if notes else "None"}

Format as a markdown list item with timestamp. Keep it concise."""

        return self.run(prompt, model=self._config.summary_model)

    def convert_prd_to_tasks(
        self, prd_content: str, project_name: str = "Project", branch_prefix: str = "ralph"
    ) -> HarnessResponse:
        """
        Convert a PRD to tasks.json format using the ralph skill.

        Args:
            prd_content: The full PRD markdown content
            project_name: Name of the project
            branch_prefix: Prefix for feature branch names (e.g., 'ralph' -> 'ralph/feature-name')

        Returns:
            HarnessResponse containing the tasks.json content
        """
        # Read the ralph skill file for guidance
        skill_path = self.project_dir / "skills" / "ralph" / "SKILL.md"
        skill_content = ""
        if skill_path.exists():
            skill_content = skill_path.read_text()

        prompt = f"""Convert the following PRD to tasks.json format for the Ralph autonomous agent system.

{f"RALPH SKILL GUIDE:{chr(10)}{skill_content}" if skill_content else ""}

PRD CONTENT:
{prd_content}

PROJECT NAME: {project_name}

IMPORTANT RULES:
1. Each user story MUST be small enough to implement in ONE iteration (one context window)
2. Stories are ordered by dependency (schema/database first, then backend, then UI)
3. Every story MUST have "Typecheck passes" in acceptance criteria
4. UI stories MUST have "Verify in browser using dev-browser skill" as criterion
5. Acceptance criteria must be specific and verifiable (not vague)
6. IDs must be in format US-001, US-002, etc.
7. Priority is execution order (1 = first)
8. All stories start with passes: false

Output ONLY valid JSON in the exact format below, nothing else:
{{
  "project": "{project_name}",
  "branchName": "{branch_prefix}/feature-name-here",
  "description": "Feature description here",
  "userStories": [
    {{
      "id": "US-001",
      "title": "Story title",
      "description": "As a [user], I want [feature] so that [benefit]",
      "acceptanceCriteria": ["criterion 1", "criterion 2", "Typecheck passes"],
      "priority": 1,
      "passes": false,
      "notes": ""
    }}
  ]
}}"""

        return self.run(prompt, model=self._config.summary_model)

    def implement_story(self, story_prompt: str, context: str = "") -> HarnessResponse:
        """
        Implement a single user story.

        Args:
            story_prompt: The user story with acceptance criteria
            context: Additional context (progress notes, learnings, etc.)

        Returns:
            HarnessResponse with the implementation result
        """
        prompt = f"""Implement the following user story completely:

{story_prompt}

{f"CONTEXT:{chr(10)}{context}" if context else ""}

IMPORTANT:
- Implement the story completely in one go
- Ensure all acceptance criteria are met
- Run typecheck/linting to verify
- If you encounter issues, document them clearly
- Do NOT leave work half-done

After implementation, verify each acceptance criterion is met."""

        return self.run(prompt, allow_writes=True)

    def verify_story(self, story_prompt: str, git_diff: str) -> HarnessResponse:
        """
        Verify a user story implementation against its acceptance criteria.

        Args:
            story_prompt: The user story with acceptance criteria
            git_diff: The git diff of changes made

        Returns:
            HarnessResponse with verification result (PASSES/FAILS/BLOCKED with feedback)
        """
        prompt = f"""Verify the following user story implementation against its acceptance criteria.

{story_prompt}

GIT DIFF OF CHANGES:
{git_diff if git_diff else "(No changes detected)"}

Check each acceptance criterion and determine if it has been met.

IMPORTANT: Distinguish between these scenarios:
1. PASSES - All acceptance criteria are verifiably met (or irrelevant - see below)
2. FAILS - One or more criteria are NOT met (implementation is wrong/incomplete)
3. BLOCKED - Some criteria CANNOT BE VERIFIED due to external factors (permission issues,
   pre-existing errors unrelated to this change, environment constraints, etc.)

HANDLING IRRELEVANT OR NONSENSICAL CRITERIA:
- If a criterion is based on an erroneous assumption (e.g., "update file X for library Y" but
  file X doesn't use library Y), treat it as PASSED by virtue of being irrelevant.
- If a criterion seems nonsensical or impossible, question it and explain why it doesn't apply.
- These criteria may have been auto-generated by earlier processes and don't reflect reality.
- Mark such criteria as passed with a note explaining why they're not applicable.

Respond in this exact format:

STATUS: PASSES or FAILS or BLOCKED
NOTES:
**What Passed:**
- ✅ List each criterion that was clearly met
- ✅ List criteria that are N/A with explanation (e.g., "N/A - file doesn't use this library")

**What Failed:**
- ❌ List each criterion that was NOT met (implementation issue)

**What Could Not Be Verified:**
- ⚠️ List criteria that cannot be verified with reasons (e.g., "Tests execution - requires permission")

**Pre-existing Issues:**
- List any errors/issues that exist in the codebase but are NOT related to this change
  (e.g., "30 type errors in unrelated files: git_manager.py, config.py")

**To Complete:**
- List specific actions needed to resolve blockers or failures

Be strict on PASSES - all applicable criteria must be verifiably met.
Use BLOCKED when the implementation looks correct but verification is impossible.
Use FAILS when the implementation itself is wrong or incomplete."""

        return self.run(prompt, model=self._config.summary_model)

    def stage_story_changes(
        self, story_id: str, story_title: str, changed_files: list[str]
    ) -> HarnessResponse:
        """
        Ask the LLM to identify which changed files should be staged for commit.

        The LLM reviews the list of changed files and determines which are
        relevant to the story being implemented. This allows intelligent
        filtering of artifacts, generated files, and unrelated changes.

        Args:
            story_id: The story ID (e.g., "US-001").
            story_title: The story title for context.
            changed_files: List of file paths that have uncommitted changes.

        Returns:
            HarnessResponse with FILES_TO_STAGE section listing files to stage,
            one per line.
        """
        files_list = "\n".join(f"  - {f}" for f in changed_files)

        prompt = f"""You are reviewing uncommitted changes to determine which files should be committed for a user story.

STORY: {story_id} - {story_title}

CHANGED FILES (uncommitted):
{files_list}

Review these files and decide which should be committed as part of this story's implementation.
The goal is to commit files needed for the production codebase to function correctly.

INCLUDE files that are:
- Source code modules (.py, .js, .ts, etc.) that are imported/referenced by other code
- Functions, classes, and utilities needed for normal application operation
- Test files that are part of the permanent test suite
- Schema/migration files for database changes
- Configuration files with non-sensitive default values
- Constants files that are NOT user-configurable and contain NO secrets
- Long-term utility scripts intended as permanent tools
- Important .md documentation ONLY for significant features (be conservative)
- PNG files that appear to be assets, documentation images, or icon master files
  (e.g., in assets/, images/, icons/, static/, docs/ directories)

EXCLUDE files that are:
- Binary files (.pdf, .jpg, .zip, .exe, .xlsx, .doc, etc.)
- Short-term test scripts or throwaway debugging code
- Generated/compiled files (.pyc, .class, node_modules/, dist/, build/)
- IDE/editor files (.idea/, .vscode/, *.swp)
- Temporary files (*.tmp, *.log, *.bak)
- Large data files, exports, or reports
- Unrelated changes that happened to be in the working directory
- Credentials, secrets, or API keys (.env, *.pem, credentials.*, *secret*)
- User-configurable settings files that should remain local
- Excessive .md files for minor/esoteric changes (too many = noise)

Respond with ONLY the files that should be staged, one per line, in this exact format:

FILES_TO_STAGE:
path/to/file1.py
path/to/file2.py

If no files should be staged, respond with:

FILES_TO_STAGE:
NONE"""

        return self.run(prompt, model=self._config.summary_model, allow_writes=False)

    def detect_project_context(self) -> str:
        """
        Detect project context including test framework, build tools, and type checker.

        Returns:
            A string describing the detected project configuration.
        """
        context_parts = []

        # Detect test framework
        if (self.project_dir / "pytest.ini").exists():
            context_parts.append("Test framework: pytest (pytest.ini found)")
        elif (self.project_dir / "pyproject.toml").exists():
            context_parts.append("Test framework: likely pytest (pyproject.toml found)")
        elif (self.project_dir / "tests").is_dir():
            context_parts.append("Test framework: tests/ directory found")

        # Detect build tools
        if (self.project_dir / "Pipfile").exists():
            context_parts.append("Build tool: pipenv (Pipfile found)")
        if (self.project_dir / "pyproject.toml").exists():
            context_parts.append("Build tool: pyproject.toml found")
        if (self.project_dir / "setup.py").exists():
            context_parts.append("Build tool: setup.py found")
        if (self.project_dir / "requirements.txt").exists():
            context_parts.append("Dependencies: requirements.txt found")

        # Detect type checker
        if (self.project_dir / "mypy.ini").exists():
            context_parts.append("Type checker: mypy (mypy.ini found)")
        elif (self.project_dir / ".mypy.ini").exists():
            context_parts.append("Type checker: mypy (.mypy.ini found)")

        # Detect CLAUDE.md for project instructions
        if (self.project_dir / "CLAUDE.md").exists():
            context_parts.append("Project instructions: CLAUDE.md found")

        if not context_parts:
            return "No specific project configuration detected."

        return "\n".join(context_parts)

    def analyze_blocked_story(
        self,
        story_prompt: str,
        full_notes: str,
        git_diff: str,
        project_context: str,
    ) -> HarnessResponse:
        """
        Analyze a blocked story to determine if it can be retried with adjustments.

        Uses the sonnet model for deeper analysis. This is an analysis-only call
        (no file writes) that provides recommendations for the next retry attempt.

        Args:
            story_prompt: The full user story prompt with acceptance criteria.
            full_notes: Complete notes from all previous attempts.
            git_diff: The current git diff of changes.
            project_context: Detected project configuration (from detect_project_context).

        Returns:
            HarnessResponse containing:
            - ACTION: RETRY or NEEDS_INTERVENTION
            - SUMMARY: Brief summary for notes replacement
            - ANALYSIS: Detailed failure breakdown
            - RECOMMENDATIONS: Steps for next retry attempt
            - INTERVENTION_REASON: If human intervention is needed
        """
        prompt = f"""You are analyzing a blocked user story that has failed multiple implementation attempts.
Your job is to determine if it can succeed with one more attempt (with adjustments) or if it needs human intervention.

PROJECT CONTEXT:
{project_context}

USER STORY:
{story_prompt}

NOTES FROM PREVIOUS ATTEMPTS:
{full_notes}

GIT DIFF OF CURRENT STATE:
{git_diff if git_diff else "(No changes detected)"}

Analyze the failure patterns and determine the best course of action.

Consider RETRY if:
- The failures are due to fixable issues (wrong approach, missing imports, typos)
- The acceptance criteria are achievable with a different strategy
- Pre-existing issues can be worked around
- The implementation is close but needs minor adjustments

Consider NEEDS_INTERVENTION if:
- There are fundamental blockers (missing dependencies, infrastructure issues)
- The acceptance criteria are ambiguous or impossible
- External factors prevent completion (permissions, environment)
- The same error keeps recurring despite different approaches
- Human judgment is needed to clarify requirements

Respond in this EXACT format:

ACTION: RETRY or NEEDS_INTERVENTION

SUMMARY:
<2-3 sentence summary of what happened and what the next approach should be>

ANALYSIS:
<Detailed breakdown of what failed and why>

RECOMMENDATIONS:
<If RETRY: Specific steps to try in the next attempt>
<If NEEDS_INTERVENTION: What the human should do to unblock>

INTERVENTION_REASON:
<Only if NEEDS_INTERVENTION: Why human help is required>"""

        # Use sonnet model for deeper analysis, no file writes
        return self.run(prompt, model="sonnet", allow_writes=False)


# Backwards compatibility aliases.
# These allow existing code using the old ClaudeRunner name to continue working
# without modification. New code should use HarnessRunner and HarnessResponse.
# See HARNESS_ARCHITECTURE.md "Migration from claude_binary" section.
ClaudeRunner = HarnessRunner
ClaudeResponse = HarnessResponse
