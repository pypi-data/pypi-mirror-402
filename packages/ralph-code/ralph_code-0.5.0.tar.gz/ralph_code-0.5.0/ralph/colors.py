"""Nord Theme color constants for ralph-coding.

This module defines the complete Nord Theme color palette (16 colors) for use
throughout the application. Colors are organized into four semantic groups:

POLAR NIGHT (Background colors):
    NORD0-NORD3: Dark background colors, from darkest to lightest.
    Use for backgrounds, panels, and UI chrome.
    - NORD0: Main background
    - NORD1: Elevated surfaces, secondary backgrounds
    - NORD2: Selections, highlights, UI borders
    - NORD3: Comments, inactive elements, subtle text

SNOW STORM (Foreground colors):
    NORD4-NORD6: Light text colors, from dimmest to brightest.
    Use for text and foreground elements.
    - NORD4: Main text color
    - NORD5: Brighter text, emphasis
    - NORD6: Brightest text, maximum contrast

FROST (Accent colors):
    NORD7-NORD10: Cool accent colors for interactive elements.
    - NORD7 (FROST_TEAL): Success states, secondary accents
    - NORD8 (FROST_CYAN): Primary accent, highlights, links
    - NORD9 (FROST_LIGHT_BLUE): Tertiary accents, decorative
    - NORD10 (FROST_BLUE): Primary buttons, key UI elements

AURORA (State colors):
    NORD11-NORD15: Vivid colors for semantic states.
    - NORD11 (AURORA_RED): Errors, destructive actions, critical
    - NORD12 (AURORA_ORANGE): Warnings, caution states
    - NORD13 (AURORA_YELLOW): Attention, pending states, in-progress
    - NORD14 (AURORA_GREEN): Success, completed, positive states
    - NORD15 (AURORA_PURPLE): Special, info, accent states

Color Mappings for Application States:
    - Idle/Inactive: NORD3 (dim polar night)
    - Pending: NORD13 (aurora yellow)
    - In Progress: NORD8 (frost cyan) or NORD13 (aurora yellow)
    - Success/Complete: NORD14 (aurora green)
    - Error/Failed: NORD11 (aurora red)
    - Warning: NORD12 (aurora orange)
    - Info/Special: NORD15 (aurora purple)

Usage Example:
    from ralph.colors import NORD8, AURORA_GREEN, POLAR_NIGHT_0

    # Use hex values directly
    print(f"Primary accent: {NORD8}")

    # Use semantic aliases
    print(f"Success color: {AURORA_GREEN}")
"""

from typing import Final

# =============================================================================
# POLAR NIGHT - Background Colors
# =============================================================================
# Dark base colors for backgrounds and UI surfaces

NORD0: Final[str] = "#2E3440"
"""Darkest background - main application background."""

NORD1: Final[str] = "#3B4252"
"""Elevated surfaces - panels, cards, secondary backgrounds."""

NORD2: Final[str] = "#434C5E"
"""Selection backgrounds - highlights, UI borders, dividers."""

NORD3: Final[str] = "#4C566A"
"""Comments and inactive - subtle text, disabled states."""

# Semantic aliases for Polar Night
POLAR_NIGHT_0: Final[str] = NORD0
POLAR_NIGHT_1: Final[str] = NORD1
POLAR_NIGHT_2: Final[str] = NORD2
POLAR_NIGHT_3: Final[str] = NORD3

# Functional aliases for backgrounds
BG_PRIMARY: Final[str] = NORD0
BG_SECONDARY: Final[str] = NORD1
BG_HIGHLIGHT: Final[str] = NORD2
BG_COMMENT: Final[str] = NORD3

# =============================================================================
# SNOW STORM - Foreground Colors
# =============================================================================
# Light colors for text and foreground elements

NORD4: Final[str] = "#D8DEE9"
"""Main text color - standard foreground text."""

NORD5: Final[str] = "#E5E9F0"
"""Brighter text - emphasis, important content."""

NORD6: Final[str] = "#ECEFF4"
"""Brightest text - maximum contrast, headings."""

# Semantic aliases for Snow Storm
SNOW_STORM_0: Final[str] = NORD4
SNOW_STORM_1: Final[str] = NORD5
SNOW_STORM_2: Final[str] = NORD6

# Functional aliases for foregrounds
FG_PRIMARY: Final[str] = NORD4
FG_BRIGHT: Final[str] = NORD5
FG_BRIGHTEST: Final[str] = NORD6

# =============================================================================
# FROST - Accent Colors
# =============================================================================
# Cool accent colors for interactive and decorative elements

NORD7: Final[str] = "#8FBCBB"
"""Frost teal - secondary accents, success indicators."""

NORD8: Final[str] = "#88C0D0"
"""Frost cyan - primary accent, highlights, links."""

NORD9: Final[str] = "#81A1C1"
"""Frost light blue - tertiary accents, decorative elements."""

NORD10: Final[str] = "#5E81AC"
"""Frost blue - primary buttons, key interactive elements."""

# Semantic aliases for Frost
FROST_TEAL: Final[str] = NORD7
FROST_CYAN: Final[str] = NORD8
FROST_LIGHT_BLUE: Final[str] = NORD9
FROST_BLUE: Final[str] = NORD10

# Functional aliases for accents
ACCENT_PRIMARY: Final[str] = NORD8
ACCENT_SECONDARY: Final[str] = NORD7
ACCENT_TERTIARY: Final[str] = NORD9
ACCENT_BUTTON: Final[str] = NORD10

# =============================================================================
# AURORA - State Colors
# =============================================================================
# Vivid colors for semantic states and feedback

NORD11: Final[str] = "#BF616A"
"""Aurora red - errors, destructive actions, critical alerts."""

NORD12: Final[str] = "#D08770"
"""Aurora orange - warnings, caution states, attention needed."""

NORD13: Final[str] = "#EBCB8B"
"""Aurora yellow - pending states, in-progress, highlights."""

NORD14: Final[str] = "#A3BE8C"
"""Aurora green - success, completed, positive confirmation."""

NORD15: Final[str] = "#B48EAD"
"""Aurora purple - special states, info, accent highlights."""

# Semantic aliases for Aurora
AURORA_RED: Final[str] = NORD11
AURORA_ORANGE: Final[str] = NORD12
AURORA_YELLOW: Final[str] = NORD13
AURORA_GREEN: Final[str] = NORD14
AURORA_PURPLE: Final[str] = NORD15

# Functional aliases for states
STATE_ERROR: Final[str] = NORD11
STATE_WARNING: Final[str] = NORD12
STATE_PENDING: Final[str] = NORD13
STATE_SUCCESS: Final[str] = NORD14
STATE_INFO: Final[str] = NORD15

# =============================================================================
# All colors tuple for iteration
# =============================================================================

ALL_NORD_COLORS: Final[tuple[str, ...]] = (
    NORD0, NORD1, NORD2, NORD3,      # Polar Night
    NORD4, NORD5, NORD6,              # Snow Storm
    NORD7, NORD8, NORD9, NORD10,      # Frost
    NORD11, NORD12, NORD13, NORD14, NORD15,  # Aurora
)
"""All 16 Nord colors in order (NORD0-NORD15)."""
