"""Random parameter generation for human-like cursor movement."""

import math
import random
from typing import TypeVar

from .models import Vector, CurveOptions, BoundingBox
from .easing import TWEEN_OPTIONS


T = TypeVar("T")


def weighted_random_choice(items: list[T], weights: list[float]) -> T:
    """
    Select an item randomly based on weights.

    Args:
        items: List of items to choose from
        weights: Weights for each item (don't need to sum to 1)

    Returns:
        Randomly selected item
    """
    total = sum(weights)
    r = random.random() * total
    cumulative = 0.0

    for item, weight in zip(items, weights):
        cumulative += weight
        if r <= cumulative:
            return item

    return items[-1]


def random_from_range(min_val: float, max_val: float) -> float:
    """
    Generate random float in range [min_val, max_val].

    Args:
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Random float in range
    """
    return random.uniform(min_val, max_val)


def random_int_from_range(min_val: int, max_val: int) -> int:
    """
    Generate random integer in range [min_val, max_val].

    Args:
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)

    Returns:
        Random integer in range
    """
    return random.randint(min_val, max_val)


def calculate_distance(start: Vector, end: Vector) -> float:
    """
    Calculate Euclidean distance between two points.

    Args:
        start: Starting point
        end: Ending point

    Returns:
        Distance between points
    """
    dx = end.x - start.x
    dy = end.y - start.y
    return math.sqrt(dx * dx + dy * dy)


def generate_random_curve_parameters(
    start: Vector,
    end: Vector,
    speed: float | None = None
) -> CurveOptions:
    """
    Generate random curve parameters based on distance and speed.

    Parameters are tuned to create natural-looking movements:
    - Shorter movements have less deviation
    - Longer movements have more control points
    - Speed affects the number of output points

    Args:
        start: Starting point
        end: Ending point
        speed: Optional speed multiplier (higher = faster = fewer points)

    Returns:
        CurveOptions with randomized parameters
    """
    distance = calculate_distance(start, end)

    # Scale offset boundaries based on distance
    # Shorter movements should have smaller offsets
    base_offset = min(distance * 0.3, 100)
    offset_boundary_x = random_from_range(base_offset * 0.5, base_offset)
    offset_boundary_y = random_from_range(base_offset * 0.5, base_offset)

    # More knots for longer distances
    if distance < 100:
        knots_count = random_int_from_range(1, 2)
    elif distance < 300:
        knots_count = random_int_from_range(2, 3)
    else:
        knots_count = random_int_from_range(2, 4)

    # Distortion parameters
    distortion_mean = random_from_range(0.5, 2.0)
    distortion_stdev = random_from_range(0.5, 1.5)
    distortion_frequency = random_from_range(0.3, 0.7)

    # Target points based on distance and speed
    base_points = int(distance * 0.5)
    base_points = max(50, min(base_points, 200))

    if speed is not None and speed > 0:
        # Higher speed = fewer points (faster movement)
        base_points = int(base_points / speed)
        base_points = max(20, base_points)

    target_points = base_points + random_int_from_range(-10, 10)
    target_points = max(20, target_points)

    # Random easing function
    tween = random.choice(TWEEN_OPTIONS)

    return CurveOptions(
        offset_boundary_x=offset_boundary_x,
        offset_boundary_y=offset_boundary_y,
        knots_count=knots_count,
        distortion_mean=distortion_mean,
        distortion_stdev=distortion_stdev,
        distortion_frequency=distortion_frequency,
        target_points=target_points,
        tween=tween
    )


def get_random_box_point(box: BoundingBox, padding: float = 0.1) -> Vector:
    """
    Get a random point inside a bounding box.

    The point is biased towards the center to avoid clicking
    near edges where elements might not be clickable.

    Args:
        box: Bounding box
        padding: Padding ratio from edges (0-0.5)

    Returns:
        Random point inside the box
    """
    # Calculate padded boundaries
    padding = max(0, min(padding, 0.4))
    pad_x = box.width * padding
    pad_y = box.height * padding

    # Random point within padded area
    x = box.x + pad_x + random.random() * (box.width - 2 * pad_x)
    y = box.y + pad_y + random.random() * (box.height - 2 * pad_y)

    return Vector(x, y)
