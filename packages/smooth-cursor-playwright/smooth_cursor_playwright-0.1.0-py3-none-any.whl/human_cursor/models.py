"""Type definitions for human_cursor library."""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Vector:
    """2D vector representing a point or direction."""
    x: float
    y: float

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector") -> "Vector":
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector":
        return Vector(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector":
        return self.__mul__(scalar)


@dataclass
class BoundingBox:
    """Bounding box of an element."""
    x: float
    y: float
    width: float
    height: float


@dataclass
class CurveOptions:
    """Options for curve generation."""
    offset_boundary_x: float = 80.0
    offset_boundary_y: float = 80.0
    knots_count: int = 2
    distortion_mean: float = 1.0
    distortion_stdev: float = 1.0
    distortion_frequency: float = 0.5
    target_points: int = 100
    tween: Callable[[float], float] | None = None


@dataclass
class ClickOptions:
    """Options for click operations."""
    move_speed: float | None = None
    hesitate: int = 0
    wait_for_click: int = 50
    move_delay: int = 0
    button: str = "left"
    click_count: int = 1


@dataclass
class ScrollOptions:
    """Options for scroll operations."""
    scroll_speed: int = 100
    scroll_delay: int = 200


@dataclass
class MoveOptions:
    """Options for move operations."""
    move_speed: float | None = None
    move_delay: int = 0
