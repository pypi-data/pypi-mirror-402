"""Main application class with Rich UI for ralph-coding."""

import sys
from pathlib import Path
from typing import Callable

import questionary
from questionary import Style
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .colors import (
    # Polar Night (backgrounds)
    NORD1,
    NORD3,
    # Snow Storm (text)
    NORD4,
    NORD5,
    NORD6,
    # Frost (accents)
    NORD8,
    NORD10,
    # Aurora (states)
    NORD11,
    NORD12,
    NORD13,
    NORD14,
    NORD15,
)
from .config import get_config
from .harness import Harness, HarnessDetector
from .spinner import RichSpinner, SpinnerStyle
from .user_stories import UserStory
from .workflow import SPINNER_MESSAGES, SPINNER_STATES, WorkflowEngine, WorkflowState


# Ralph Wiggum ASCII art - Using Nord Theme colors
# NORD15 (Aurora Purple) for the face, NORD8 (Frost Cyan) for eyes and tagline
RALPH_ART = rf"""
[bold {NORD15}]        _______________
       /               \
      |  [/bold {NORD15}][bold {NORD8}]●[/bold {NORD8}][bold {NORD15}]         [/bold {NORD15}][bold {NORD8}]●[/bold {NORD8}][bold {NORD15}]  |
      |       [/bold {NORD15}][bold {NORD11}]>[/bold {NORD11}][bold {NORD15}]       |
      |    \______/    |
       \_______________/
          |       |
         /|       |\
        / |       | \
[/bold {NORD15}][bold {NORD8}]   "I'm helping!"[/bold {NORD8}]
"""

RALPH_ART_SMALL = f"""[bold {NORD15}]  ___
 (o o)  [/bold {NORD15}][bold {NORD8}]"I'm helping!"[/bold {NORD8}]
[bold {NORD15}]  \\\\[/bold {NORD15}][bold {NORD11}]>[/bold {NORD11}][bold {NORD15}]/[/bold {NORD15}]"""

# Custom style for questionary using Nord Theme colors
MENU_STYLE = Style([
    ('qmark', f'fg:{NORD15} bold'),           # Aurora purple for question marks
    ('question', f'fg:{NORD6} bold'),          # Snow storm (brightest) for question text
    ('answer', f'fg:{NORD8} bold'),            # Frost cyan for answers
    ('pointer', f'fg:{NORD14} bold'),          # Aurora green for pointer
    ('highlighted', f'fg:{NORD8} bold'),       # Frost cyan for highlighted items
    ('selected', f'fg:{NORD10}'),              # Frost blue for selected items
    ('separator', f'fg:{NORD3}'),              # Polar night (lighter) for separators
    ('instruction', f'fg:{NORD3}'),            # Polar night (lighter) for instructions
])


class RalphApp:
    """Main application with Rich terminal UI."""

    def __init__(self, project_dir: Path, debug: bool = False):
        self.project_dir = project_dir.resolve()
        self.debug = debug
        self.console = Console()
        self._config = get_config()
        self._workflow: WorkflowEngine | None = None
        self._running = False
        self._last_output = ""
        self._live: Live | None = None
        self._last_status_key: tuple[object, ...] | None = None
        self._spinner = RichSpinner(style=SpinnerStyle.DOTS_6, spinner_color=NORD8)
        self._state_message = ""
        self._harness_available = False  # Set by _validate_harness()

    def _get_status_key(self) -> tuple[object, ...]:
        """Get a hashable key representing current status for change detection."""
        workflow = self._get_workflow()
        stats = workflow.prd_manager.get_stats()
        return (
            workflow.state,
            workflow.is_paused,
            workflow.current_task.id if workflow.current_task else None,
            self._state_message,
            self._last_output,
            workflow.error_message,
            tuple(stats.items()),
            workflow.completed_this_session,
        )

    def _update_live(self) -> None:
        """Update live display only if content has changed."""
        if not self._live:
            return
        status_key = self._get_status_key()
        if status_key != self._last_status_key:
            self._last_status_key = status_key
            self._live.update(self._build_live_status())

    def _on_state_change(self, state: WorkflowState, message: str) -> None:
        """Handle workflow state changes."""
        if message:
            self._state_message = message
        else:
            self._state_message = SPINNER_MESSAGES.get(state, "")
        self._update_live()

    def _on_output(self, message: str) -> None:
        """Handle output from the workflow."""
        self._last_output = message
        self._update_live()

    def _get_workflow(self) -> WorkflowEngine:
        """Get or create the workflow engine."""
        if self._workflow is None:
            self._workflow = WorkflowEngine(
                self.project_dir,
                debug=self.debug,
                on_state_change=self._on_state_change,
                on_output=self._on_output,
                use_spinner=False,  # App uses its own Live display
            )
        return self._workflow

    def _show_header(self) -> None:
        """Show the Ralph header with ASCII art using Nord theme colors."""
        self.console.print(Panel(
            RALPH_ART,
            title=f"[bold {NORD15}]RALPH CODING[/bold {NORD15}]",
            subtitle=f"[bold {NORD6}]{self.project_dir.name}[/bold {NORD6}]",
            border_style=NORD8,
        ))

    def _validate_harness(self) -> bool:
        """
        Validate that the configured harness exists and is usable.

        Checks if the harness path exists and is executable. If not,
        offers auto-detect or reconfigure options.

        Returns:
            True if a valid harness is available, False otherwise.
        """
        harness = Harness.from_config(self._config.harness)

        if harness.is_available:
            self._harness_available = True
            return True

        # Harness not available - show warning
        self.console.print(f"\n[{NORD11} bold]⚠ Warning: Harness not found[/{NORD11} bold]")
        self.console.print(f"[{NORD4}]Configured harness '[{NORD8}]{self._config.harness}[/{NORD8}]' is not available.[/{NORD4}]")
        self.console.print(f"[{NORD3}]The path does not exist or is not executable.[/{NORD3}]\n")

        # Try auto-detection
        detector = HarnessDetector()
        alternatives = detector.detect_all()

        if alternatives:
            # Found alternatives - offer to use them
            self.console.print(f"[{NORD14}]Found available alternatives:[/{NORD14}]")
            choices = []
            for alt in alternatives:
                self.console.print(f"  [{NORD8}]• {alt.name}[/{NORD8}] [{NORD3}]({alt.path})[/{NORD3}]")
                choices.append({"name": f"Use {alt.name} ({alt.path})", "value": alt.path})

            choices.append({"name": "Enter custom path", "value": "custom"})
            choices.append({"name": "Continue without harness (workflow disabled)", "value": "skip"})

            self.console.print()
            result: str | None = questionary.select(
                "What would you like to do?",
                choices=choices,
                style=MENU_STYLE,
            ).ask()

            if result is None:
                # User cancelled
                self._harness_available = False
                return False
            elif result == "skip":
                self.console.print(f"[{NORD13}]Continuing without harness. Workflow commands will be disabled.[/{NORD13}]\n")
                self._harness_available = False
                return False
            elif result == "custom":
                custom_path = questionary.text(
                    "Enter harness path or command:",
                    style=MENU_STYLE,
                ).ask()
                if custom_path:
                    self._config.harness = custom_path
                    # Recursively validate the new path
                    return self._validate_harness()
                else:
                    self._harness_available = False
                    return False
            else:
                # User selected an alternative
                self._config.harness = result
                self.console.print(f"[{NORD14}]Harness updated to: {result}[/{NORD14}]\n")
                self._harness_available = True
                return True
        else:
            # No alternatives found
            self.console.print(f"[{NORD13}]No alternative harnesses detected on PATH.[/{NORD13}]\n")

            choices = [
                {"name": "Enter custom path", "value": "custom"},
                {"name": "Continue without harness (workflow disabled)", "value": "skip"},
            ]

            result = questionary.select(
                "What would you like to do?",
                choices=choices,
                style=MENU_STYLE,
            ).ask()

            if result is None or result == "skip":
                self.console.print(f"[{NORD13}]Continuing without harness. Workflow commands will be disabled.[/{NORD13}]\n")
                self._harness_available = False
                return False
            elif result == "custom":
                custom_path = questionary.text(
                    "Enter harness path or command:",
                    style=MENU_STYLE,
                ).ask()
                if custom_path:
                    self._config.harness = custom_path
                    # Recursively validate the new path
                    return self._validate_harness()
                else:
                    self._harness_available = False
                    return False

        self._harness_available = False
        return False

    def _build_status_panel(self) -> Panel:
        """Build the status panel with Nord theme colors."""
        workflow = self._get_workflow()
        stats = workflow.prd_manager.get_stats()

        lines = []

        # PRD stats: Unspecced | Questions | Pending | In Progress | Complete | Errored
        # PRD status colors (US-007):
        #   unspecced = dim gray (NORD3)
        #   questions = aurora yellow (NORD13)
        #   pending = aurora orange (NORD12)
        #   in_progress = aurora green (NORD14)
        #   completed = aurora green dim (NORD14 dim)
        #   errored = aurora red (NORD11)
        parts = []
        if stats['unspecced'] > 0:
            parts.append(f"[{NORD3}]{stats['unspecced']} unspecced[/{NORD3}]")
        if stats['questions'] > 0:
            parts.append(f"[{NORD13}]{stats['questions']} questions[/{NORD13}]")
        parts.append(f"[{NORD12}]{stats['pending']} pending[/{NORD12}]")
        parts.append(f"[{NORD14}]{stats['in_progress']} in progress[/{NORD14}]")
        parts.append(f"[dim {NORD14}]{stats['completed']} complete[/dim {NORD14}]")
        if stats['errored'] > 0:
            parts.append(f"[{NORD11}]{stats['errored']} errored[/{NORD11}]")
        lines.append(f"[{NORD8}]PRDs:[/{NORD8}] [{NORD4}]{' | '.join(parts)}[/{NORD4}]")

        # Story progress (if tasks.json exists)
        completed, total, percent = workflow.get_story_progress()
        if total > 0:
            lines.append(f"[{NORD8}]Stories:[/{NORD8}] [{NORD4}]{percent}% ({completed}/{total} complete)[/{NORD4}]")

        # Activity detail (only show if not idle)
        if workflow.state not in (WorkflowState.IDLE, WorkflowState.PAUSED, WorkflowState.QUESTIONS):
            activity = workflow.state.value.replace("_", " ").title()
            if workflow.current_story:
                lines.append(f"[{NORD3}]Activity:[/{NORD3}] [{NORD5}]{activity} - {workflow.current_story.id}: {workflow.current_story.title}[/{NORD5}]")
            elif workflow.current_task:
                lines.append(f"[{NORD3}]Activity:[/{NORD3}] [{NORD5}]{activity} - {workflow.current_task.name}[/{NORD5}]")
            else:
                lines.append(f"[{NORD3}]Activity:[/{NORD3}] [{NORD5}]{activity}[/{NORD5}]")

        # Questions indicator - Nord aurora orange for attention
        if workflow.state == WorkflowState.QUESTIONS:
            lines.append(f"[{NORD12} bold]*** PRDs HAVE OPEN QUESTIONS ***[/{NORD12} bold]")

        # Last output - Nord polar night for dim text
        if self._last_output:
            lines.append(f"[{NORD3}]{self._last_output}[/{NORD3}]")

        # Paused indicator - Nord aurora yellow for warning
        if workflow.is_paused:
            lines.append(f"[{NORD13} bold]*** WORKFLOW PAUSED ***[/{NORD13} bold]")

        # Harness unavailable indicator - Nord aurora red for warning
        if not self._harness_available:
            lines.append(f"[{NORD11} bold]*** NO HARNESS - WORKFLOW DISABLED ***[/{NORD11} bold]")

        # Error message - Nord aurora red for errors
        if workflow.error_message:
            lines.append(f"[{NORD11}]Error: {workflow.error_message}[/{NORD11}]")

        content = "\n".join(lines)
        # Panel with Nord frost blue border and Snow Storm title
        return Panel(
            content,
            title=f"[{NORD6} bold]Status[/{NORD6} bold]",
            border_style=NORD10,
        )

    def _main_menu(self) -> str | None:
        """Show the main menu and return the selected action."""
        workflow = self._get_workflow()
        has_questions = len(workflow.get_prds_with_questions()) > 0

        # Check if we have stories to manage
        has_stories = workflow.story_manager.has_tasks()

        # If no harness available, show limited menu
        if not self._harness_available:
            choices = [
                {"name": "Add PRD", "value": "add"},
                {"name": "List PRDs", "value": "list"},
            ]
            if has_stories:
                choices.append({"name": "Manage stories", "value": "stories"})
            choices.extend([
                {"name": "Settings", "value": "settings"},
                {"name": "Quit", "value": "quit"},
            ])
        elif workflow.state == WorkflowState.QUESTIONS or has_questions:
            # Questions need to be answered before continuing
            choices = [
                {"name": "Answer PRD questions", "value": "answer"},
                {"name": "Add PRD", "value": "add"},
                {"name": "List PRDs", "value": "list"},
            ]
            if has_stories:
                choices.append({"name": "Manage stories", "value": "stories"})
            choices.extend([
                {"name": "Settings", "value": "settings"},
                {"name": "Quit", "value": "quit"},
            ])
        elif workflow.is_paused:
            choices = [
                {"name": "Resume workflow", "value": "resume"},
                {"name": "Add PRD", "value": "add"},
                {"name": "List PRDs", "value": "list"},
            ]
            if has_stories:
                choices.append({"name": "Manage stories", "value": "stories"})
            choices.extend([
                {"name": "Settings", "value": "settings"},
                {"name": "Quit", "value": "quit"},
            ])
        else:
            choices = [
                {"name": "Run workflow", "value": "run"},
                {"name": "Add PRD", "value": "add"},
                {"name": "List PRDs", "value": "list"},
            ]
            if has_stories:
                choices.append({"name": "Manage stories", "value": "stories"})
            choices.extend([
                {"name": "Pause workflow", "value": "pause"},
                {"name": "Settings", "value": "settings"},
                {"name": "Quit", "value": "quit"},
            ])

        result: str | None = questionary.select(
            "What would you like to do?",
            choices=choices,
            style=MENU_STYLE,
            instruction="(Use arrow keys, then Enter)",
        ).ask()
        return result

    def _show_add_task_menu(self) -> None:
        """Show the add task menu."""
        self.console.print()

        task_type = questionary.select(
            "What type of PRD?",
            choices=[
                {"name": "Quick task (creates .txt for later speccing)", "value": "thin"},
                {"name": "Cancel", "value": "cancel"},
            ],
            style=MENU_STYLE,
        ).ask()

        if task_type == "cancel" or task_type is None:
            return

        if task_type == "thin":
            name = questionary.text(
                "PRD name (will be used as filename):",
                style=MENU_STYLE,
            ).ask()

            if not name:
                return

            description = questionary.text(
                "Task description:",
                style=MENU_STYLE,
            ).ask()

            if description:
                workflow = self._get_workflow()
                # Create a .txt file in the PRD folder
                from .prd_manager import slugify
                slug = slugify(name)
                prd_file = workflow.prd_manager.prd_dir / f"{slug}.txt"
                prd_file.write_text(description)
                workflow.prd_manager.reload()
                self.console.print(f"\n[green]Added PRD: {prd_file.name}[/green]")

    def _show_settings_menu(self) -> None:
        """Show the settings menu."""
        while True:
            self.console.print()

            setting = questionary.select(
                "Settings",
                choices=[
                    {"name": f"Worker model: {self._config.worker_model}", "value": "worker_model"},
                    {"name": f"Summary model: {self._config.summary_model}", "value": "summary_model"},
                    {"name": f"Harness: {self._config.harness}", "value": "harness"},
                    {"name": f"Max iterations: {self._config.max_iterations}", "value": "max_iter"},
                    {"name": f"Max story attempts: {self._config.max_story_attempts}", "value": "max_attempts"},
                    {"name": f"Branch prefix: {self._config.branch_prefix}", "value": "branch_prefix"},
                    {"name": f"On error: {self._config.on_error}", "value": "on_error"},
                    {"name": f"Auto spec: {self._config.auto_spec_without_oversight}", "value": "auto_spec"},
                    {"name": f"Wait on rate limit: {self._config.wait_on_rate_limit}", "value": "rate_limit"},
                    {"name": f"Pause on completion: {self._config.pause_on_completion}", "value": "pause_completion"},
                    {"name": f"Always build tests: {self._config.always_build_tests}", "value": "tests"},
                    {"name": "Back", "value": "back"},
                ],
                style=MENU_STYLE,
            ).ask()

            if setting == "back" or setting is None:
                break
            elif setting == "worker_model":
                self._show_model_selection("worker")
            elif setting == "summary_model":
                self._show_model_selection("summary")
            elif setting == "harness":
                self._show_harness_selection()
            elif setting == "max_iter":
                max_iter = questionary.text(
                    "Max iterations:",
                    default=str(self._config.max_iterations),
                    style=MENU_STYLE,
                ).ask()
                if max_iter and max_iter.isdigit():
                    self._config.max_iterations = int(max_iter)
            elif setting == "max_attempts":
                max_attempts = questionary.text(
                    "Max story attempts (before marking blocked):",
                    default=str(self._config.max_story_attempts),
                    style=MENU_STYLE,
                ).ask()
                if max_attempts and max_attempts.isdigit():
                    self._config.max_story_attempts = int(max_attempts)
            elif setting == "branch_prefix":
                prefix = questionary.text(
                    "Branch prefix (e.g., 'ralph' creates 'ralph/feature-name'):",
                    default=self._config.branch_prefix,
                    style=MENU_STYLE,
                ).ask()
                if prefix:
                    self._config.branch_prefix = prefix
                    self.console.print(f"[cyan]Branch prefix: {prefix}[/cyan]")
            elif setting == "on_error":
                on_error = questionary.select(
                    "On error:",
                    choices=["block", "retry", "pause", "skip"],
                    default=self._config.on_error,
                    style=MENU_STYLE,
                ).ask()
                if on_error:
                    self._config.on_error = on_error
            elif setting == "auto_spec":
                self._config.auto_spec_without_oversight = not self._config.auto_spec_without_oversight
                self.console.print(f"[cyan]Auto spec: {self._config.auto_spec_without_oversight}[/cyan]")
            elif setting == "rate_limit":
                self._config.wait_on_rate_limit = not self._config.wait_on_rate_limit
                self.console.print(f"[cyan]Wait on rate limit: {self._config.wait_on_rate_limit}[/cyan]")
            elif setting == "pause_completion":
                self._config.pause_on_completion = not self._config.pause_on_completion
                self.console.print(f"[cyan]Pause on completion: {self._config.pause_on_completion}[/cyan]")
            elif setting == "tests":
                self._config.always_build_tests = not self._config.always_build_tests
                self.console.print(f"[cyan]Always build tests: {self._config.always_build_tests}[/cyan]")

    def _show_model_selection(self, role: str) -> None:
        """Show harness-specific model selection menu."""
        self.console.print()

        # Get the current harness and query for supported models
        harness = Harness.from_config(self._config.harness)
        supported_models = harness.get_supported_models()
        current_model = (
            self._config.worker_model if role == "worker" else self._config.summary_model
        )
        role_label = "Worker model" if role == "worker" else "Summary model"

        # For unknown harnesses (custom) with no models, fall back to text input
        if not supported_models:
            self.console.print(
                f"[{NORD13}]No predefined models for harness '{harness.name}'.[/{NORD13}]"
            )
            model_name: str | None = questionary.text(
                f"Enter {role_label.lower()} name:",
                default=current_model,
                style=MENU_STYLE,
            ).ask()
            if model_name and model_name.strip():
                if role == "worker":
                    self._config.worker_model = model_name.strip()
                else:
                    self._config.summary_model = model_name.strip()
                self.console.print(
                    f"[{NORD14}]{role_label} set to: {model_name.strip()}[/{NORD14}]"
                )
            return

        # Build choices (model name only)
        from questionary import Choice

        choices: list[Choice] = []

        for model_name, label in supported_models:
            choices.append(Choice(title=model_name, value=model_name))

        # No models available - show alert and return
        if not choices:
            self.console.bell()
            self.console.print(
                f"[{NORD11}]No models available for harness '{harness.name}'.[/{NORD11}]"
            )
            return

        # Get the valid model values (excluding cancel)
        valid_model_values: list[str] = [str(c.value) for c in choices]

        # Add cancel option
        choices.append(Choice(title="Cancel", value="cancel"))

        # Determine the default - MUST be a value that exists in choices
        if current_model in valid_model_values:
            default_choice = current_model
        else:
            # Current model not valid - use first available model as default
            default_choice = valid_model_values[0]
            if role == "worker":
                self._config.worker_model = default_choice
            else:
                self._config.summary_model = default_choice
            self.console.print(
                f"[{NORD13}]{role_label} '{current_model}' not supported by {harness.name}. "
                f"Reset to: {default_choice}[/{NORD13}]"
            )

        try:
            selected: str | None = questionary.select(
                f"Select {role_label.lower()} (current: {current_model}):",
                choices=choices,
                default=default_choice,
                style=MENU_STYLE,
            ).ask()
        except ValueError as e:
            # Debug info to diagnose questionary issues
            self.console.print(f"[{NORD11}]Error in model selection:[/{NORD11}]")
            self.console.print(f"  default_choice: {default_choice!r}")
            self.console.print(f"  valid_model_values: {valid_model_values!r}")
            choice_info = [(c.title, c.value) for c in choices]
            self.console.print(f"  choices: {choice_info!r}")
            self.console.print(f"  harness: {harness.name} (type={harness.type})")
            self.console.print(f"  {role_label.lower()}: {current_model!r}")
            raise e

        if selected and selected != "cancel":
            if role == "worker":
                self._config.worker_model = selected
            else:
                self._config.summary_model = selected
            self.console.print(f"[{NORD14}]{role_label} set to: {selected}[/{NORD14}]")

    def _show_harness_selection(self) -> None:
        """Show harness selection submenu with auto-detect, custom, and detected options."""
        self.console.print()

        # Run auto-detection to find available harnesses
        detector = HarnessDetector()
        detected_harnesses = detector.detect_all()

        # Build choices list
        choices: list[dict[str, str]] = []

        # Add Auto-detect option first
        choices.append({
            "name": "Auto-detect (scan PATH for available tools)",
            "value": "auto-detect",
        })

        # Add detected harnesses with full paths
        for harness in detected_harnesses:
            choices.append({
                "name": f"{harness.name} ({harness.path})",
                "value": harness.path,
            })

        # Add Custom option
        choices.append({
            "name": "Custom (enter path manually)",
            "value": "custom",
        })

        # Add Cancel option
        choices.append({
            "name": "Cancel",
            "value": "cancel",
        })

        result: str | None = questionary.select(
            f"Select harness (current: {self._config.harness}):",
            choices=choices,
            style=MENU_STYLE,
        ).ask()

        if result is None or result == "cancel":
            return

        if result == "auto-detect":
            # Show auto-detection results
            self._show_autodetect_results(detected_harnesses)
        elif result == "custom":
            # Prompt for custom path
            self._prompt_custom_harness()
        else:
            # User selected a detected harness - save it
            self._set_harness(result)

    def _show_autodetect_results(self, detected_harnesses: list[Harness]) -> None:
        """Show auto-detection results and allow selection."""
        self.console.print()

        if not detected_harnesses:
            self.console.print(f"[{NORD13}]No harnesses detected on PATH.[/{NORD13}]")
            self.console.print(f"[{NORD3}]Looked for: claude, codex[/{NORD3}]")
            self.console.print()

            # Offer custom path option
            enter_custom = questionary.confirm(
                "Would you like to enter a custom harness path?",
                default=True,
                style=MENU_STYLE,
            ).ask()

            if enter_custom:
                self._prompt_custom_harness()
            return

        # Show detected harnesses
        self.console.print(f"[{NORD14}]Detected harnesses:[/{NORD14}]")
        for harness in detected_harnesses:
            self.console.print(f"  [{NORD8}]{harness.name}[/{NORD8}] [{NORD3}]({harness.path})[/{NORD3}]")
        self.console.print()

        # Build selection choices
        choices: list[dict[str, str]] = []
        for harness in detected_harnesses:
            choices.append({
                "name": f"{harness.name} ({harness.path})",
                "value": harness.path,
            })
        choices.append({"name": "Cancel", "value": "cancel"})

        selected: str | None = questionary.select(
            "Select a harness to use:",
            choices=choices,
            style=MENU_STYLE,
        ).ask()

        if selected and selected != "cancel":
            self._set_harness(selected)

    def _prompt_custom_harness(self) -> None:
        """Prompt user to enter a custom harness path."""
        self.console.print()

        custom_path: str | None = questionary.text(
            "Enter harness path or command:",
            style=MENU_STYLE,
        ).ask()

        if custom_path and custom_path.strip():
            self._set_harness(custom_path.strip())

    def _set_harness(self, harness_path: str) -> None:
        """Set and validate a harness path, updating model if needed."""
        self._config.harness = harness_path

        # Validate the harness
        harness_obj = Harness.from_config(harness_path)
        if harness_obj.is_available:
            self._harness_available = True
            self.console.print(f"[{NORD14}]Harness set to: {harness_path}[/{NORD14}]")
        else:
            self._harness_available = False
            self.console.print(f"[{NORD11}]Warning: Harness '{harness_path}' not found or not executable[/{NORD11}]")
            self.console.print(f"[{NORD13}]The harness will be saved, but workflow will be disabled until a valid harness is configured.[/{NORD13}]")

        # Check if current models are valid for the new harness
        current_worker = self._config.worker_model
        if not harness_obj.is_model_supported(current_worker):
            default_worker = harness_obj.get_default_worker_model()
            if default_worker:
                self._config.worker_model = default_worker
                self.console.print(
                    f"[{NORD13}]Worker model '{current_worker}' not supported by {harness_obj.name}. "
                    f"Switched to: {default_worker}[/{NORD13}]"
                )
            else:
                self.console.print(
                    f"[{NORD13}]Note: Worker model '{current_worker}' may not be supported by {harness_obj.name}. "
                    f"You may need to configure a worker model in Settings.[/{NORD13}]"
                )

        current_summary = self._config.summary_model
        if not harness_obj.is_model_supported(current_summary):
            default_summary = harness_obj.get_default_summary_model()
            if default_summary:
                self._config.summary_model = default_summary
                self.console.print(
                    f"[{NORD13}]Summary model '{current_summary}' not supported by {harness_obj.name}. "
                    f"Switched to: {default_summary}[/{NORD13}]"
                )
            else:
                self.console.print(
                    f"[{NORD13}]Note: Summary model '{current_summary}' may not be supported by {harness_obj.name}. "
                    f"You may need to configure a summary model in Settings.[/{NORD13}]"
                )

    def _show_prd_list(self) -> None:
        """Show the current PRD list with Nord theme colors."""
        workflow = self._get_workflow()
        prds = workflow.prd_manager.get_all_prds()

        self.console.print()

        if not prds:
            self.console.print(f"[{NORD3}]No PRDs yet. Add some tasks to get started![/{NORD3}]")
            return

        # Table with Nord frost blue border and Snow Storm title
        table = Table(title=f"[{NORD6}]PRDs[/{NORD6}]", border_style=NORD10)
        table.add_column("Status", style=NORD8, width=12)
        table.add_column("Name", style=NORD4)
        table.add_column("Type", style=NORD3, width=8)

        # Status badges using Nord Aurora colors (US-007):
        #   unspecced = dim gray (NORD3)
        #   questions = aurora yellow (NORD13)
        #   pending = aurora orange (NORD12)
        #   in_progress = aurora green (NORD14)
        #   completed = aurora green dim (dim NORD14)
        #   errored = aurora red (NORD11)
        status_styles = {
            "unspecced": NORD3,            # dim gray
            "questions": NORD13,           # aurora yellow
            "pending": NORD12,             # aurora orange
            "in_progress": NORD14,         # aurora green
            "completed": f"dim {NORD14}",  # aurora green dim
            "errored": NORD11,             # aurora red
        }

        for prd in prds:
            status_style = status_styles.get(prd.status, NORD4)
            prd_type = "specced" if prd.is_specced else "unspecced"
            table.add_row(
                f"[{status_style}]{prd.status}[/{status_style}]",
                prd.name,
                prd_type,
            )

        self.console.print(table)

    def _show_manage_stories(self) -> None:
        """Show UI to manage user stories (mark as passed/unblock)."""
        workflow = self._get_workflow()

        if not workflow.story_manager.has_tasks():
            self.console.print(f"[{NORD3}]No stories to manage.[/{NORD3}]")
            return

        tasks_file = workflow.story_manager.get_tasks_file()
        if not tasks_file:
            return

        # Outer loop: story selection list
        while True:
            # Reload stories to reflect any changes made
            workflow.story_manager.reload()
            tasks_file = workflow.story_manager.get_tasks_file()
            if not tasks_file:
                return
            stories = tasks_file.user_stories

            self.console.print()

            # Build story choices (plain text - questionary doesn't support Rich markup)
            max_attempts = self._config.max_story_attempts
            choices = []
            for story in stories:
                if story.passes:
                    status = "PASSED"
                elif story.needs_intervention:
                    status = "NEEDS HELP"
                elif story.blocked or story.attempts >= max_attempts:
                    status = "BLOCKED"
                elif story.attempts > 0:
                    status = f"{story.attempts} attempts"
                else:
                    status = "pending"

                choices.append({
                    "name": f"{story.id}: {story.title} ({status})",
                    "value": story.id,
                })
            choices.append({"name": "Back", "value": "back"})

            story_id = questionary.select(
                "Select a story to manage:",
                choices=choices,
                style=MENU_STYLE,
            ).ask()

            if story_id == "back" or story_id is None:
                return

            # Find the story
            story_match = next((s for s in stories if s.id == story_id), None)
            if not story_match:
                continue
            story = story_match

            # Inner loop: story actions until user selects Back
            while True:
                # Show story details
                self.console.print(f"\n[{NORD6} bold]{story.id}: {story.title}[/{NORD6} bold]")
                self.console.print(f"[{NORD4}]{story.description}[/{NORD4}]")
                self.console.print(f"\n[{NORD8}]Acceptance Criteria:[/{NORD8}]")
                for criterion in story.acceptance_criteria:
                    self.console.print(f"  [{NORD4}]- {criterion}[/{NORD4}]")
                intervention_str = f" | Needs Help: {story.needs_intervention}" if story.needs_intervention else ""
                self.console.print(f"\n[{NORD3}]Attempts: {story.attempts} | Passes: {story.passes} | Blocked: {story.blocked}{intervention_str}[/{NORD3}]")
                max_attempts = self._config.max_story_attempts

                # Show action choices
                action_choices = []
                if story.notes:
                    action_choices.append({"name": "View notes", "value": "notes"})
                action_choices.append({"name": "Edit acceptance criteria", "value": "edit_criteria"})
                if not story.passes:
                    action_choices.append({"name": "Mark as PASSED", "value": "pass"})
                if story.needs_intervention:
                    action_choices.append({"name": "Mark intervention complete (retry)", "value": "resolve_intervention"})
                if not story.passes and story.attempts >= max_attempts and not story.blocked:
                    action_choices.append({"name": "Retry (reset attempts)", "value": "retry"})
                if story.blocked and not story.needs_intervention:
                    action_choices.append({"name": "Unblock (reset attempts)", "value": "unblock"})
                if story.passes:
                    action_choices.append({"name": "Mark as NOT passed", "value": "unpass"})
                action_choices.append({"name": "Back", "value": "back"})

                action = questionary.select(
                    "What would you like to do?",
                    choices=action_choices,
                    style=MENU_STYLE,
                ).ask()

                if action == "back" or action is None:
                    break
                elif action == "notes":
                    self._view_story_notes(story)
                elif action == "edit_criteria":
                    self._edit_acceptance_criteria(story, workflow)
                elif action == "pass":
                    story.passes = True
                    story.blocked = False
                    workflow.story_manager.update_story(story)
                    self.console.print(f"[{NORD14}]Marked {story.id} as PASSED[/{NORD14}]")
                elif action == "resolve_intervention":
                    story.blocked = False
                    story.needs_intervention = False
                    story.attempts = 0
                    workflow.story_manager.update_story(story)
                    self.console.print(f"[{NORD14}]Intervention resolved for {story.id} (ready for retry)[/{NORD14}]")
                elif action == "retry":
                    story.blocked = False
                    story.needs_intervention = False
                    story.attempts = 0
                    workflow.story_manager.update_story(story)
                    self.console.print(f"[{NORD14}]Reset attempts for {story.id} (ready for retry)[/{NORD14}]")
                elif action == "unblock":
                    story.blocked = False
                    story.needs_intervention = False
                    story.attempts = 0
                    workflow.story_manager.update_story(story)
                    self.console.print(f"[{NORD14}]Unblocked {story.id} (attempts reset)[/{NORD14}]")
                elif action == "unpass":
                    story.passes = False
                    workflow.story_manager.update_story(story)
                    self.console.print(f"[{NORD13}]Marked {story.id} as NOT passed[/{NORD13}]")

    def _view_story_notes(self, story: UserStory) -> None:
        """View story notes in a pager for scrolling."""
        if not story.notes:
            self.console.print(f"[{NORD3}]No notes for this story.[/{NORD3}]")
            return

        # Build plain text notes content (pager doesn't handle Rich markup well)
        notes_content = f"Notes for {story.id}: {story.title}\n"
        notes_content += "=" * 60 + "\n\n"
        notes_content += story.notes
        notes_content += "\n\n" + "=" * 60
        notes_content += "\n(Press 'q' to exit)"

        # Use pager for scrollable output - plain text mode
        with self.console.pager():
            self.console.print(notes_content)

    def _edit_acceptance_criteria(
        self, story: UserStory, workflow: WorkflowEngine
    ) -> None:
        """Edit acceptance criteria for a story."""
        self.console.print(f"\n[{NORD8}]Editing acceptance criteria for {story.id}[/{NORD8}]")
        self.console.print(f"[{NORD3}]Current criteria:[/{NORD3}]")

        for i, criterion in enumerate(story.acceptance_criteria, 1):
            self.console.print(f"  [{NORD4}]{i}. {criterion}[/{NORD4}]")

        self.console.print()

        while True:
            action = questionary.select(
                "What would you like to do?",
                choices=[
                    {"name": "Edit a criterion", "value": "edit"},
                    {"name": "Add a criterion", "value": "add"},
                    {"name": "Remove a criterion", "value": "remove"},
                    {"name": "Done", "value": "done"},
                ],
                style=MENU_STYLE,
            ).ask()

            if action == "done" or action is None:
                break
            elif action == "edit":
                self._edit_single_criterion(story, workflow)
            elif action == "add":
                self._add_criterion(story, workflow)
            elif action == "remove":
                self._remove_criterion(story, workflow)

    def _edit_single_criterion(
        self, story: UserStory, workflow: WorkflowEngine
    ) -> None:
        """Edit a single acceptance criterion."""
        if not story.acceptance_criteria:
            self.console.print(f"[{NORD13}]No criteria to edit.[/{NORD13}]")
            return

        # Build choices for criteria
        choices = [
            {"name": f"{i}. {c}", "value": i - 1}
            for i, c in enumerate(story.acceptance_criteria, 1)
        ]
        choices.append({"name": "Cancel", "value": -1})

        idx = questionary.select(
            "Select criterion to edit:",
            choices=choices,
            style=MENU_STYLE,
        ).ask()

        if idx is None or idx == -1:
            return

        current = story.acceptance_criteria[idx]
        new_value = questionary.text(
            "Edit criterion:",
            default=current,
            style=MENU_STYLE,
        ).ask()

        if new_value and new_value.strip() and new_value != current:
            story.acceptance_criteria[idx] = new_value.strip()
            workflow.story_manager.update_story(story)
            self.console.print(f"[{NORD14}]Criterion updated.[/{NORD14}]")

    def _add_criterion(self, story: UserStory, workflow: WorkflowEngine) -> None:
        """Add a new acceptance criterion."""
        new_criterion = questionary.text(
            "Enter new criterion:",
            style=MENU_STYLE,
        ).ask()

        if new_criterion and new_criterion.strip():
            story.acceptance_criteria.append(new_criterion.strip())
            workflow.story_manager.update_story(story)
            self.console.print(f"[{NORD14}]Criterion added.[/{NORD14}]")

    def _remove_criterion(
        self, story: UserStory, workflow: WorkflowEngine
    ) -> None:
        """Remove an acceptance criterion."""
        if not story.acceptance_criteria:
            self.console.print(f"[{NORD13}]No criteria to remove.[/{NORD13}]")
            return

        if len(story.acceptance_criteria) == 1:
            self.console.print(
                f"[{NORD11}]Cannot remove the last criterion. Stories must have at least one.[/{NORD11}]"
            )
            return

        # Build choices for criteria
        choices = [
            {"name": f"{i}. {c}", "value": i - 1}
            for i, c in enumerate(story.acceptance_criteria, 1)
        ]
        choices.append({"name": "Cancel", "value": -1})

        idx = questionary.select(
            "Select criterion to remove:",
            choices=choices,
            style=MENU_STYLE,
        ).ask()

        if idx is None or idx == -1:
            return

        removed = story.acceptance_criteria.pop(idx)
        workflow.story_manager.update_story(story)
        self.console.print(f"[{NORD14}]Removed: {removed}[/{NORD14}]")

    def _show_answer_questions(self) -> None:
        """Show UI to answer PRD questions."""
        workflow = self._get_workflow()
        prds_with_questions = workflow.get_prds_with_questions()

        if not prds_with_questions:
            self.console.print("[dim]No PRDs have open questions.[/dim]")
            return

        for prd in prds_with_questions:
            self.console.print(f"\n[bold cyan]PRD: {prd.name}[/bold cyan]")
            self.console.print(f"[dim]{prd.description[:200]}...[/dim]\n")

            answers = []
            for question in prd.questions:
                self.console.print(f"[yellow]Q: {question.question}[/yellow]")

                if question.options:
                    # Multi-choice question
                    answer = questionary.select(
                        "Select an answer:",
                        choices=question.options + ["Other (type answer)"],
                        style=MENU_STYLE,
                    ).ask()

                    if answer is None:
                        return

                    if answer == "Other (type answer)":
                        answer = questionary.text(
                            "Your answer:",
                            style=MENU_STYLE,
                        ).ask()
                        if answer is None:
                            return
                else:
                    # Free-form question
                    answer = questionary.text(
                        "Your answer:",
                        style=MENU_STYLE,
                    ).ask()
                    if answer is None:
                        return

                answers.append(answer)
                self.console.print(f"[green]A: {answer}[/green]\n")

            # Confirm and save
            confirm = questionary.confirm(
                f"Save answers for '{prd.name}'?",
                default=True,
                style=MENU_STYLE,
            ).ask()

            if confirm is None:
                return

            if confirm:
                workflow.answer_questions(prd, answers)
                self.console.print(f"[green]Saved answers for {prd.name}[/green]")

                # Resume workflow if it was paused for questions
                if workflow.state == WorkflowState.QUESTIONS:
                    workflow.resume()

    def run(self) -> None:
        """Run the main application loop."""
        self._running = True
        workflow = self._get_workflow()

        # Show header
        self._show_header()

        if self.debug:
            self.console.print("[yellow]Debug mode enabled[/yellow]\n")

        # Validate harness on startup
        self._validate_harness()

        # Notify if workflow was paused from previous session
        if workflow.is_paused:
            self.console.print("[yellow]Workflow was paused from previous session.[/yellow]")
            if workflow.current_task:
                self.console.print(f"[yellow]PRD in progress: {workflow.current_task.name}[/yellow]")
            self.console.print()

        while self._running:
            # Show status
            self.console.print(self._build_status_panel())

            # Get user choice
            try:
                choice = self._main_menu()

                if choice is None or choice == "quit":
                    confirm = questionary.confirm(
                        "Are you sure you want to quit?",
                        default=False,
                        style=MENU_STYLE,
                    ).ask()
                    if confirm:
                        self._running = False
                elif choice == "add":
                    self._show_add_task_menu()
                elif choice == "answer":
                    self._show_answer_questions()
                elif choice == "settings":
                    self._show_settings_menu()
                elif choice == "run" or choice == "resume":
                    self._run_workflow()
                elif choice == "pause":
                    workflow.pause()
                    self.console.print("[yellow]Paused[/yellow]")
                elif choice == "list":
                    self._show_prd_list()
                elif choice == "stories":
                    self._show_manage_stories()

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted[/yellow]")
                confirm = questionary.confirm(
                    "Are you sure you want to quit?",
                    default=False,
                    style=MENU_STYLE,
                ).ask()
                if confirm:
                    self._running = False

        # Goodbye message with Ralph - Nord theme colors
        self.console.print(Panel(
            RALPH_ART_SMALL + f"\n[{NORD4}]Goodbye![/{NORD4}]",
            border_style=NORD8,
        ))

    def _build_live_status(self) -> Panel:
        """Build a live status panel for workflow execution with Nord theme colors."""
        workflow = self._get_workflow()
        stats = workflow.prd_manager.get_stats()

        # State colors using Nord palette (US-006)
        state_colors = {
            WorkflowState.IDLE: NORD3,         # dim (Polar Night)
            WorkflowState.SPECCING: NORD8,     # frost (Frost cyan)
            WorkflowState.QUESTIONS: NORD8,    # frost (Frost cyan)
            WorkflowState.CONVERTING: NORD8,   # frost (Frost cyan)
            WorkflowState.PICKING: NORD5,      # snow (Snow Storm)
            WorkflowState.IMPLEMENTING: NORD14,  # aurora green
            WorkflowState.REVIEWING: NORD8,    # frost cyan
            WorkflowState.TESTING: NORD10,     # frost blue
            WorkflowState.COMMITTING: NORD15,  # aurora purple
            WorkflowState.ARCHIVING: NORD14,   # aurora green
            WorkflowState.PAUSED: NORD13,      # aurora yellow
            WorkflowState.ERROR: NORD11,       # aurora red
        }
        state_color = state_colors.get(workflow.state, NORD4)

        lines = []

        # Current state with spinner for active states
        is_active = (workflow.state in SPINNER_STATES) and (not workflow.is_paused)
        if is_active:
            # Update spinner message and get current frame
            message = self._state_message or SPINNER_MESSAGES.get(
                workflow.state, workflow.state.value.upper()
            )
            self._spinner.message = message
            self._spinner.spinner_color = state_color
            spinner_frame = self._spinner.current_frame
            self._spinner.next_frame()
            lines.append(f"[bold {state_color}]{spinner_frame} {message}[/bold {state_color}]")
        else:
            lines.append(f"[bold {state_color}]● {workflow.state.value.upper()}[/bold {state_color}]")

        # Current PRD - Snow Storm for text
        if workflow.current_task:
            lines.append(f"  [{NORD6} bold]PRD:[/{NORD6} bold] [{NORD4}]{workflow.current_task.name}[/{NORD4}]")

        # Current story
        if workflow.current_story:
            lines.append(f"  [{NORD6} bold]Story:[/{NORD6} bold] [{NORD4}]{workflow.current_story.id} - {workflow.current_story.title}[/{NORD4}]")

        # Last output - Polar Night for dim text
        if self._last_output:
            lines.append(f"  [{NORD3}]{self._last_output}[/{NORD3}]")

        lines.append("")

        # PRD stats: Unspecced | Questions | Pending | In Progress | Complete | Errored
        # PRD status colors (US-007):
        #   unspecced = dim gray (NORD3)
        #   questions = aurora yellow (NORD13)
        #   pending = aurora orange (NORD12)
        #   in_progress = aurora green (NORD14)
        #   completed = aurora green dim (NORD14 dim)
        #   errored = aurora red (NORD11)
        parts = []
        if stats['unspecced'] > 0:
            parts.append(f"[{NORD3}]{stats['unspecced']} unspecced[/{NORD3}]")
        if stats['questions'] > 0:
            parts.append(f"[{NORD13}]{stats['questions']} questions[/{NORD13}]")
        parts.append(f"[{NORD12}]{stats['pending']} pending[/{NORD12}]")
        parts.append(f"[{NORD14}]{stats['in_progress']} in progress[/{NORD14}]")
        parts.append(f"[dim {NORD14}]{stats['completed']} complete[/dim {NORD14}]")
        if stats['errored'] > 0:
            parts.append(f"[{NORD11}]{stats['errored']} errored[/{NORD11}]")
        lines.append(f"[{NORD6} bold]PRDs:[/{NORD6} bold] [{NORD4}]{' | '.join(parts)}[/{NORD4}]")

        # Story progress (if tasks.json exists)
        story_completed, story_total, story_percent = workflow.get_story_progress()
        if story_total > 0:
            lines.append(f"[{NORD6} bold]Stories:[/{NORD6} bold] [{NORD4}]{story_percent}% ({story_completed}/{story_total} complete)[/{NORD4}]")

        lines.append(f"[{NORD3}]Session: {workflow.completed_this_session} PRDs completed[/{NORD3}]")

        # Error message - Nord aurora red
        if workflow.error_message:
            lines.append(f"\n[{NORD11}]Error: {workflow.error_message}[/{NORD11}]")

        lines.append(f"\n[{NORD3}]Press Ctrl+C to pause[/{NORD3}]")

        content = "\n".join(lines)
        # Panel with Nord aurora green border (active workflow) and Snow Storm title
        return Panel(
            content,
            title=f"[{NORD6} bold]Workflow Running[/{NORD6} bold]",
            border_style=NORD14,
        )

    def _run_workflow(self) -> None:
        """Run the workflow engine."""
        workflow = self._get_workflow()

        if workflow.is_paused:
            workflow.resume()

        self.console.print()
        self._last_status_key = None  # Reset change detection

        try:
            # Higher refresh rate for spinner animation
            with Live(self._build_live_status(), refresh_per_second=10, console=self.console) as live:
                self._live = live
                self._spinner.reset()
                while workflow.step():
                    # Always update to animate spinner during active states
                    live.update(self._build_live_status())
                self._live = None

        except KeyboardInterrupt:
            self._live = None
            workflow.pause()
            self.console.print("\n[yellow]Paused by user[/yellow]")

        # Show final status
        if workflow.state == WorkflowState.IDLE:
            stats = workflow.prd_manager.get_stats()
            if stats["pending"] == 0 and stats["unspecced"] == 0:
                self.console.print("\n[green]All PRDs completed![/green]")
            else:
                self.console.print(f"\n[yellow]Paused. {stats['pending']} PRDs pending.[/yellow]")


def main(project_dir: Path | None = None, debug: bool = False) -> None:
    """Main entry point for the application."""
    if project_dir is None:
        project_dir = Path.cwd()

    app = RalphApp(project_dir, debug=debug)
    app.run()
