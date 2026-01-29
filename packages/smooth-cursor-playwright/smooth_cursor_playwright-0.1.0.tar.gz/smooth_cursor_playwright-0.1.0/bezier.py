"""Bezier curve calculations using Bernstein polynomials."""

from math import factorial
from typing import Callable

from .models import Vector


def binomial(n: int, k: int) -> int:
    """Calculate binomial coefficient C(n, k)."""
    return factorial(n) // (factorial(k) * factorial(n - k))


def bernstein_polynomial_point(x: float, i: int, n: int) -> float:
    """
    Calculate single point of Bernstein polynomial.

    Args:
        x: Parameter value (0 to 1)
        i: Index of the control point
        n: Degree of the polynomial

    Returns:
        Bernstein basis polynomial value
    """
    return binomial(n, i) * (x ** i) * ((1 - x) ** (n - i))


def bernstein_polynomial(points: list[Vector]) -> Callable[[float], Vector]:
    """
    Create a Bezier curve function from control points.

    Args:
        points: List of control points

    Returns:
        Function that takes parameter t (0-1) and returns point on curve
    """
    n = len(points) - 1

    def curve(t: float) -> Vector:
        x = 0.0
        y = 0.0
        for i, point in enumerate(points):
            bern = bernstein_polynomial_point(t, i, n)
            x += point.x * bern
            y += point.y * bern
        return Vector(x, y)

    return curve


def calculate_points_in_curve(n: int, points: list[Vector]) -> list[Vector]:
    """
    Generate n points along a Bezier curve.

    Args:
        n: Number of points to generate
        points: Control points of the Bezier curve

    Returns:
        List of n points along the curve
    """
    curve = bernstein_polynomial(points)
    result = []

    for i in range(n):
        t = i / (n - 1) if n > 1 else 0
        result.append(curve(t))

    return result
