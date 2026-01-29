"""Human Cursor - A library for humanizing cursor movements with Playwright."""

from .cursor import HumanCursor, SyncHumanCursor, OverlayClient, DEFAULT_OPTIONS
from .models import (
    Vector,
    BoundingBox,
    CurveOptions,
    ClickOptions,
    ScrollOptions,
    MoveOptions,
)
from .curve_generator import HumanizeMouseTrajectory, generate_path
from .easing import TWEEN_OPTIONS

__version__ = "0.1.0"

__all__ = [
    "HumanCursor",
    "SyncHumanCursor",
    "OverlayClient",
    "DEFAULT_OPTIONS",
    "Vector",
    "BoundingBox",
    "CurveOptions",
    "ClickOptions",
    "ScrollOptions",
    "MoveOptions",
    "HumanizeMouseTrajectory",
    "generate_path",
    "TWEEN_OPTIONS",
]
