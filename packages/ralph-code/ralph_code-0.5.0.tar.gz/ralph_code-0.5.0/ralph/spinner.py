"""Rich-based spinner utility module for ralph-coding.

This module provides spinner functionality using Rich's rendering system,
allowing spinners to be embedded in Live displays and panels.

The module provides:
- Multiple braille spinner styles including 6-dot rotating pattern
- Integration with Rich's Live display system
- Nord theme color support
- Thread-safe operation for background spinning

Usage Example:
    from ralph.spinner import RichSpinner, SpinnerStyle
    from rich.live import Live
    from rich.panel import Panel

    # Create spinner for use in Live display
    spinner = RichSpinner("Processing...", style=SpinnerStyle.DOTS_6)

    with Live(Panel(spinner), refresh_per_second=10) as live:
        while working:
            live.update(Panel(spinner))  # Spinner auto-advances

    # Or use standalone with context manager
    with RichSpinner("Loading...") as spinner:
        do_work()
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator

from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.style import Style
from rich.text import Text

from ralph.colors import FROST_CYAN, FG_PRIMARY


class SpinnerStyle(Enum):
    """Available spinner animation styles using braille patterns.

    DOTS_6: Six dots rotating around the braille cell (2x3 pattern)
    DOTS_8: Eight dots rotating around the full braille cell (2x4 pattern)
    DOTS_BOUNCE: Dots bouncing left-right pattern
    DOTS_GROW: Dots growing/shrinking pattern
    CLASSIC: Traditional |/-\\ spinner
    """

    # Six dots rotating around the 2x3 braille cell
    # Pattern: top-left -> mid-left -> bot-left -> top-right -> mid-right -> bot-right
    DOTS_6 = ("⠁", "⠂", "⠄", "⠈", "⠐", "⠠")

    # Eight dots rotating around full 2x4 braille cell
    DOTS_8 = ("⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷")

    # Classic braille dots pattern (10 frames)
    DOTS = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    # Dots bouncing
    DOTS_BOUNCE = ("⠁", "⠂", "⠄", "⠂")

    # Growing dots
    DOTS_GROW = ("⠀", "⠁", "⠃", "⠇", "⠏", "⠟", "⠿", "⠟", "⠏", "⠇", "⠃", "⠁")

    # Classic ASCII spinner
    CLASSIC = ("|", "/", "-", "\\")

    # Circle quadrants
    CIRCLE = ("◴", "◷", "◶", "◵")

    # Half circles
    HALF_CIRCLE = ("◐", "◓", "◑", "◒")


@dataclass
class RichSpinner:
    """A Rich-compatible spinner that can be rendered in Live displays.

    This spinner implements Rich's console protocol, allowing it to be
    used directly in Rich's rendering system including Live, Panel, etc.

    The spinner automatically advances frames on each render, or can be
    manually advanced with next_frame().

    Attributes:
        message: Text displayed next to the spinner.
        style: The spinner animation style.
        spinner_color: Color for the spinner character.
        message_color: Color for the message text.
        interval: Time between frames in seconds (for threaded mode).

    Example:
        # In a Live display (auto-advances on render)
        spinner = RichSpinner("Loading...")
        with Live(spinner, refresh_per_second=10):
            time.sleep(2)

        # Standalone with threading
        with RichSpinner("Working...") as spinner:
            time.sleep(2)
    """

    message: str = ""
    style: SpinnerStyle = SpinnerStyle.DOTS_6
    spinner_color: str = FROST_CYAN
    message_color: str = FG_PRIMARY
    interval: float = 0.1

    _frame_index: int = field(default=0, init=False, repr=False)
    _running: bool = field(default=False, init=False, repr=False)
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _console: Console | None = field(default=None, init=False, repr=False)
    _live: Live | None = field(default=None, init=False, repr=False)

    @property
    def frames(self) -> tuple[str, ...]:
        """Get the frame sequence for the current style."""
        value: tuple[str, ...] = self.style.value
        return value

    @property
    def current_frame(self) -> str:
        """Get the current spinner frame character."""
        return self.frames[self._frame_index % len(self.frames)]

    def next_frame(self) -> str:
        """Advance to the next frame and return it."""
        with self._lock:
            self._frame_index = (self._frame_index + 1) % len(self.frames)
            return self.current_frame

    def reset(self) -> None:
        """Reset the spinner to the first frame."""
        with self._lock:
            self._frame_index = 0

    def update_message(self, message: str) -> None:
        """Update the spinner message."""
        self.message = message

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Render the spinner for Rich console output.

        This method is called by Rich when rendering the spinner.
        It advances the frame on each render for automatic animation
        when used with Live displays.
        """
        # Build the text with styled spinner and message
        text = Text()
        text.append(self.current_frame, style=Style(color=self.spinner_color))
        if self.message:
            text.append(" ")
            text.append(self.message, style=Style(color=self.message_color))

        # Advance frame for next render (makes Live auto-animate)
        self.next_frame()

        yield text

    def _spin_loop(self) -> None:
        """Internal loop for threaded spinning."""
        while self._running:
            if self._live:
                self._live.update(self)
            time.sleep(self.interval)

    def start(self, console: Console | None = None) -> None:
        """Start the spinner with its own Live display.

        Args:
            console: Optional Rich console to use. Creates one if not provided.
        """
        if self._running:
            return

        self._console = console or Console()
        self._running = True
        self.reset()

        # Create Live display for standalone usage
        self._live = Live(
            self,
            console=self._console,
            refresh_per_second=int(1 / self.interval),
            transient=True,
        )
        self._live.start()

        # Start background thread to keep updating
        self._thread = threading.Thread(target=self._spin_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the spinner and clean up."""
        self._running = False

        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

        if self._live:
            self._live.stop()
            self._live = None

    def __enter__(self) -> RichSpinner:
        """Context manager entry - start the spinner."""
        self.start()
        return self

    def __exit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object | None) -> None:
        """Context manager exit - stop the spinner."""
        self.stop()


def create_spinner_text(
    message: str = "",
    style: SpinnerStyle = SpinnerStyle.DOTS_6,
    spinner_color: str = FROST_CYAN,
    message_color: str = FG_PRIMARY,
    frame_index: int = 0,
) -> Text:
    """Create a Rich Text object with spinner and message.

    This is a utility function for creating spinner text without
    the full RichSpinner class. Useful for manual frame control.

    Args:
        message: Text to display after the spinner.
        style: Spinner animation style.
        spinner_color: Color for the spinner character.
        message_color: Color for the message text.
        frame_index: Which frame to display (0-indexed).

    Returns:
        Rich Text object with styled spinner and message.

    Example:
        for i in range(20):
            text = create_spinner_text("Loading...", frame_index=i)
            console.print(text, end="\\r")
            time.sleep(0.1)
    """
    frames = style.value
    frame = frames[frame_index % len(frames)]

    text = Text()
    text.append(frame, style=Style(color=spinner_color))
    if message:
        text.append(" ")
        text.append(message, style=Style(color=message_color))

    return text


# Convenience aliases for backwards compatibility
SpinnerManager = RichSpinner


def spinner_frames(style: SpinnerStyle = SpinnerStyle.DOTS_6) -> Iterator[str]:
    """Generate infinite spinner frames.

    Args:
        style: Spinner animation style.

    Yields:
        Spinner frame characters in sequence, repeating indefinitely.

    Example:
        frames = spinner_frames(SpinnerStyle.DOTS_6)
        for _ in range(30):
            print(next(frames), end="\\r", flush=True)
            time.sleep(0.1)
    """
    frames_tuple = style.value
    index = 0
    while True:
        yield frames_tuple[index % len(frames_tuple)]
        index += 1
