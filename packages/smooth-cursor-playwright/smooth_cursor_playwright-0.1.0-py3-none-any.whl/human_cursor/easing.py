"""Easing functions for smooth animations."""

import math
from typing import Callable


def linear(t: float) -> float:
    """Linear easing - no acceleration."""
    return t


# Quadratic easing functions
def ease_in_quad(t: float) -> float:
    """Quadratic ease-in - accelerating from zero velocity."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out - decelerating to zero velocity."""
    return t * (2 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out - acceleration until halfway, then deceleration."""
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


# Cubic easing functions
def ease_in_cubic(t: float) -> float:
    """Cubic ease-in - accelerating from zero velocity."""
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out - decelerating to zero velocity."""
    t1 = t - 1
    return t1 * t1 * t1 + 1


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out - acceleration until halfway, then deceleration."""
    if t < 0.5:
        return 4 * t * t * t
    return (t - 1) * (2 * t - 2) * (2 * t - 2) + 1


# Quartic easing functions
def ease_in_quart(t: float) -> float:
    """Quartic ease-in - accelerating from zero velocity."""
    return t * t * t * t


def ease_out_quart(t: float) -> float:
    """Quartic ease-out - decelerating to zero velocity."""
    t1 = t - 1
    return 1 - t1 * t1 * t1 * t1


def ease_in_out_quart(t: float) -> float:
    """Quartic ease-in-out - acceleration until halfway, then deceleration."""
    if t < 0.5:
        return 8 * t * t * t * t
    t1 = t - 1
    return 1 - 8 * t1 * t1 * t1 * t1


# Quintic easing functions
def ease_in_quint(t: float) -> float:
    """Quintic ease-in - accelerating from zero velocity."""
    return t * t * t * t * t


def ease_out_quint(t: float) -> float:
    """Quintic ease-out - decelerating to zero velocity."""
    t1 = t - 1
    return 1 + t1 * t1 * t1 * t1 * t1


def ease_in_out_quint(t: float) -> float:
    """Quintic ease-in-out - acceleration until halfway, then deceleration."""
    if t < 0.5:
        return 16 * t * t * t * t * t
    t1 = t - 1
    return 1 + 16 * t1 * t1 * t1 * t1 * t1


# Sinusoidal easing functions
def ease_in_sine(t: float) -> float:
    """Sinusoidal ease-in - accelerating from zero velocity."""
    return 1 - math.cos(t * math.pi / 2)


def ease_out_sine(t: float) -> float:
    """Sinusoidal ease-out - decelerating to zero velocity."""
    return math.sin(t * math.pi / 2)


def ease_in_out_sine(t: float) -> float:
    """Sinusoidal ease-in-out - acceleration until halfway, then deceleration."""
    return -(math.cos(math.pi * t) - 1) / 2


# Exponential easing functions
def ease_in_expo(t: float) -> float:
    """Exponential ease-in - accelerating from zero velocity."""
    if t == 0:
        return 0
    return math.pow(2, 10 * (t - 1))


def ease_out_expo(t: float) -> float:
    """Exponential ease-out - decelerating to zero velocity."""
    if t == 1:
        return 1
    return 1 - math.pow(2, -10 * t)


def ease_in_out_expo(t: float) -> float:
    """Exponential ease-in-out - acceleration until halfway, then deceleration."""
    if t == 0:
        return 0
    if t == 1:
        return 1
    if t < 0.5:
        return math.pow(2, 20 * t - 10) / 2
    return (2 - math.pow(2, -20 * t + 10)) / 2


# Circular easing functions
def ease_in_circ(t: float) -> float:
    """Circular ease-in - accelerating from zero velocity."""
    return 1 - math.sqrt(1 - t * t)


def ease_out_circ(t: float) -> float:
    """Circular ease-out - decelerating to zero velocity."""
    t1 = t - 1
    return math.sqrt(1 - t1 * t1)


def ease_in_out_circ(t: float) -> float:
    """Circular ease-in-out - acceleration until halfway, then deceleration."""
    if t < 0.5:
        return (1 - math.sqrt(1 - 4 * t * t)) / 2
    return (math.sqrt(1 - (-2 * t + 2) ** 2) + 1) / 2


# Collection of all easing functions for random selection
TWEEN_OPTIONS: list[Callable[[float], float]] = [
    linear,
    ease_in_quad,
    ease_out_quad,
    ease_in_out_quad,
    ease_in_cubic,
    ease_out_cubic,
    ease_in_out_cubic,
    ease_in_quart,
    ease_out_quart,
    ease_in_out_quart,
    ease_in_quint,
    ease_out_quint,
    ease_in_out_quint,
    ease_in_sine,
    ease_out_sine,
    ease_in_out_sine,
    ease_in_expo,
    ease_out_expo,
    ease_in_out_expo,
    ease_in_circ,
    ease_out_circ,
    ease_in_out_circ,
]
