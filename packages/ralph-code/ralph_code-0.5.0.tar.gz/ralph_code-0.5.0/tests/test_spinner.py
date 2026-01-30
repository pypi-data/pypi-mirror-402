"""Unit tests for spinner utilities."""

from ralph.spinner import RichSpinner, SpinnerStyle, spinner_frames


def test_rich_spinner_advances_and_wraps() -> None:
    """Spinner advances through frames and wraps to the start."""
    spinner = RichSpinner(style=SpinnerStyle.DOTS_6)
    frames = spinner.frames

    observed = [spinner.current_frame]
    for _ in range(len(frames)):
        observed.append(spinner.next_frame())

    assert observed == list(frames) + [frames[0]]


def test_spinner_frames_generator_cycles() -> None:
    """Generator yields frames in order and wraps indefinitely."""
    frames = SpinnerStyle.DOTS_6.value
    generator = spinner_frames(SpinnerStyle.DOTS_6)

    observed = [next(generator) for _ in range(len(frames) + 1)]

    assert observed == list(frames) + [frames[0]]
