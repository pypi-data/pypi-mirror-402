"""
Kling-26 Motion Control Package

This package provides core functionalities for controlling motion sequences,
inspired by the Kling-26 motion control system and the tutorial available at:
https://supermaker.ai/blog/how-to-use-kling-26-motion-control-ai-free-full-tutorial-ai-baby-dance-guide/
"""

import math
from typing import List, Tuple

OFFICIAL_SITE = "https://supermaker.ai/blog/how-to-use-kling-26-motion-control-ai-free-full-tutorial-ai-baby-dance-guide/"


def get_official_site() -> str:
    """
    Returns the official website URL for Kling-26 Motion Control.

    Returns:
        str: The official website URL.
    """
    return OFFICIAL_SITE


def calculate_trajectory_points(start_point: Tuple[float, float], end_point: Tuple[float, float], num_points: int) -> List[Tuple[float, float]]:
    """
    Calculates a linear trajectory between a start and end point, generating a list of intermediate points.

    Args:
        start_point (Tuple[float, float]): The starting coordinates (x, y).
        end_point (Tuple[float, float]): The ending coordinates (x, y).
        num_points (int): The number of points to generate along the trajectory.

    Returns:
        List[Tuple[float, float]]: A list of (x, y) coordinates representing the trajectory. Returns an empty list if num_points <= 1.
    """
    if num_points <= 1:
        return []

    trajectory: List[Tuple[float, float]] = []
    x_start, y_start = start_point
    x_end, y_end = end_point

    x_increment = (x_end - x_start) / (num_points - 1)
    y_increment = (y_end - y_start) / (num_points - 1)

    for i in range(num_points):
        x = x_start + i * x_increment
        y = y_start + i * y_increment
        trajectory.append((x, y))

    return trajectory


def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculates the Euclidean distance between two points.

    Args:
        point1 (Tuple[float, float]): The coordinates of the first point (x1, y1).
        point2 (Tuple[float, float]): The coordinates of the second point (x2, y2).

    Returns:
        float: The Euclidean distance between the two points.
    """
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def smooth_motion_profile(velocities: List[float], smoothing_factor: float = 0.1) -> List[float]:
    """
    Applies a simple moving average filter to smooth a motion profile (list of velocities).

    Args:
        velocities (List[float]): A list of velocity values representing the motion profile.
        smoothing_factor (float): A smoothing factor between 0 and 1. Higher values result in more smoothing.

    Returns:
        List[float]: A list of smoothed velocity values.
    """
    if not 0 <= smoothing_factor <= 1:
        raise ValueError("Smoothing factor must be between 0 and 1.")

    smoothed_velocities: List[float] = []
    if not velocities:
        return smoothed_velocities

    smoothed_velocities.append(velocities[0])  # The first value remains the same

    for i in range(1, len(velocities)):
        smoothed_velocity = smoothing_factor * velocities[i] + (1 - smoothing_factor) * smoothed_velocities[i - 1]
        smoothed_velocities.append(smoothed_velocity)

    return smoothed_velocities


def convert_degrees_to_radians(degrees: float) -> float:
    """
    Converts an angle from degrees to radians.

    Args:
        degrees (float): The angle in degrees.

    Returns:
        float: The angle in radians.
    """
    return math.radians(degrees)


def rotate_point(point: Tuple[float, float], angle_degrees: float, center: Tuple[float, float] = (0, 0)) -> Tuple[float, float]:
    """
    Rotates a point around a center point by a given angle (in degrees).

    Args:
        point (Tuple[float, float]): The point to rotate (x, y).
        angle_degrees (float): The rotation angle in degrees.
        center (Tuple[float, float]): The center of rotation (x, y). Defaults to (0, 0).

    Returns:
        Tuple[float, float]: The rotated point (x', y').
    """
    x, y = point
    center_x, center_y = center
    angle_radians = convert_degrees_to_radians(angle_degrees)

    # Translate point to origin
    x -= center_x
    y -= center_y

    # Perform rotation
    x_rotated = x * math.cos(angle_radians) - y * math.sin(angle_radians)
    y_rotated = x * math.sin(angle_radians) + y * math.cos(angle_radians)

    # Translate back
    x_rotated += center_x
    y_rotated += center_y

    return (x_rotated, y_rotated)