"""Human-like mouse trajectory generator."""

import math
import random
from typing import Callable

from .models import Vector, CurveOptions
from .bezier import calculate_points_in_curve
from .easing import TWEEN_OPTIONS, ease_out_quint


class HumanizeMouseTrajectory:
    """
    Generates human-like mouse movement trajectories using Bezier curves
    with random distortions and easing.
    """

    def __init__(
        self,
        from_point: Vector,
        to_point: Vector,
        options: CurveOptions | None = None
    ):
        """
        Initialize trajectory generator.

        Args:
            from_point: Starting point
            to_point: Destination point
            options: Curve generation options
        """
        self.from_point = from_point
        self.to_point = to_point
        self.options = options or CurveOptions()

    def generate_curve(self) -> list[Vector]:
        """
        Generate a human-like mouse movement curve.

        Returns:
            List of points representing the trajectory
        """
        # Generate internal knots (control points)
        knots = self.generate_internal_knots(
            self.from_point,
            self.to_point,
            self.options.offset_boundary_x,
            self.options.offset_boundary_y,
            self.options.knots_count
        )

        # Generate points along the Bezier curve
        points = self.generate_points(knots)

        # Add distortion to make movement more natural
        if self.options.distortion_mean > 0:
            points = self.distort_points(
                points,
                self.options.distortion_mean,
                self.options.distortion_stdev,
                self.options.distortion_frequency
            )

        # Apply easing function
        tween = self.options.tween or random.choice(TWEEN_OPTIONS)
        points = self.tween_points(points, tween, self.options.target_points)

        return points

    def generate_internal_knots(
        self,
        from_point: Vector,
        to_point: Vector,
        offset_boundary_x: float,
        offset_boundary_y: float,
        knots_count: int
    ) -> list[Vector]:
        """
        Generate random control points between start and end.

        Args:
            from_point: Starting point
            to_point: Ending point
            offset_boundary_x: Maximum X offset from straight line
            offset_boundary_y: Maximum Y offset from straight line
            knots_count: Number of internal control points

        Returns:
            List of control points including start and end
        """
        knots = [from_point]

        for i in range(1, knots_count + 1):
            # Calculate position along the line
            t = i / (knots_count + 1)

            # Linear interpolation between start and end
            base_x = from_point.x + (to_point.x - from_point.x) * t
            base_y = from_point.y + (to_point.y - from_point.y) * t

            # Add random offset
            offset_x = random.uniform(-offset_boundary_x, offset_boundary_x)
            offset_y = random.uniform(-offset_boundary_y, offset_boundary_y)

            knots.append(Vector(base_x + offset_x, base_y + offset_y))

        knots.append(to_point)
        return knots

    def generate_points(self, knots: list[Vector]) -> list[Vector]:
        """
        Generate points along the Bezier curve defined by knots.

        Args:
            knots: Control points

        Returns:
            Points along the curve
        """
        # Generate more points initially for smoother distortion
        initial_points = max(self.options.target_points * 2, 100)
        return calculate_points_in_curve(initial_points, knots)

    def distort_points(
        self,
        points: list[Vector],
        distortion_mean: float,
        distortion_stdev: float,
        distortion_frequency: float
    ) -> list[Vector]:
        """
        Add random distortions to points for more natural movement.

        Args:
            points: Original points
            distortion_mean: Mean distortion magnitude
            distortion_stdev: Standard deviation of distortion
            distortion_frequency: How often to apply distortion (0-1)

        Returns:
            Distorted points
        """
        distorted = []

        for i, point in enumerate(points):
            # Don't distort first and last points
            if i == 0 or i == len(points) - 1:
                distorted.append(point)
                continue

            # Apply distortion with given frequency
            if random.random() < distortion_frequency:
                delta = self.random_normal(distortion_mean, distortion_stdev)
                distorted.append(Vector(
                    point.x + delta,
                    point.y + delta
                ))
            else:
                distorted.append(point)

        return distorted

    def tween_points(
        self,
        points: list[Vector],
        tween: Callable[[float], float],
        target_count: int
    ) -> list[Vector]:
        """
        Resample points using an easing function for non-uniform spacing.

        This makes the cursor slow down or speed up along the path.

        Args:
            points: Original points
            tween: Easing function
            target_count: Number of output points

        Returns:
            Resampled points with easing applied
        """
        if len(points) < 2:
            return points

        result = []
        n = len(points) - 1

        for i in range(target_count):
            # Calculate progress with easing
            t = i / (target_count - 1) if target_count > 1 else 0
            eased_t = tween(t)

            # Map eased progress to point index
            index_float = eased_t * n
            index = int(index_float)
            fraction = index_float - index

            # Clamp index
            if index >= n:
                result.append(points[-1])
            elif index < 0:
                result.append(points[0])
            else:
                # Linear interpolation between two points
                p1 = points[index]
                p2 = points[index + 1]
                result.append(Vector(
                    p1.x + (p2.x - p1.x) * fraction,
                    p1.y + (p2.y - p1.y) * fraction
                ))

        return result

    @staticmethod
    def random_normal(mean: float, stdev: float) -> float:
        """
        Generate random number using Box-Muller transform.

        Args:
            mean: Mean of the distribution
            stdev: Standard deviation

        Returns:
            Random number from normal distribution
        """
        u1 = random.random()
        u2 = random.random()

        # Avoid log(0)
        while u1 == 0:
            u1 = random.random()

        # Box-Muller transform
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return z0 * stdev + mean


def generate_path(
    from_point: Vector,
    to_point: Vector,
    options: CurveOptions | None = None
) -> list[Vector]:
    """
    Convenience function to generate a human-like path.

    Args:
        from_point: Starting point
        to_point: Destination point
        options: Curve options

    Returns:
        List of points representing the trajectory
    """
    generator = HumanizeMouseTrajectory(from_point, to_point, options)
    return generator.generate_curve()
