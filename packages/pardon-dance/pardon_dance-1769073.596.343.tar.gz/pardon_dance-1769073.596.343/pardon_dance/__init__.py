"""
Pardon Dance Package

This package provides functionalities related to the "Pardon Dance" viral video effect.
It includes tools for analyzing dance patterns, identifying key movements,
and generating variations of the dance.

Official Site: https://supermaker.ai/video/blog/unlocking-the-magic-of-pardon-dance-the-viral-video-effect-taking-over-social-media/
"""

import math
from typing import List, Tuple


OFFICIAL_SITE: str = "https://supermaker.ai/video/blog/unlocking_the_magic_of_pardon-dance-the-viral-video-effect-taking-over-social-media/"


def get_official_site() -> str:
    """
    Returns the official website URL for the Pardon Dance.

    Returns:
        str: The URL of the official website.
    """
    return OFFICIAL_SITE


def calculate_dance_energy(movements: List[Tuple[float, float, float]], duration: float) -> float:
    """
    Calculates the energy of a dance based on the magnitude of movements and duration.

    Args:
        movements: A list of tuples representing movements, where each tuple contains
                   (x_displacement, y_displacement, z_displacement).
        duration: The duration of the dance in seconds.

    Returns:
        float: The calculated energy of the dance.
    """
    total_displacement = 0.0
    for x, y, z in movements:
        total_displacement += math.sqrt(x**2 + y**2 + z**2)

    if duration <= 0:
        return 0.0  # Avoid division by zero

    energy = total_displacement / duration
    return energy


def simplify_dance_sequence(movements: List[Tuple[float, float, float]], tolerance: float = 0.1) -> List[Tuple[float, float, float]]:
    """
    Simplifies a dance sequence by removing redundant movements within a specified tolerance.
    This uses a rudimentary Ramer-Douglas-Peucker-like simplification.

    Args:
        movements: A list of tuples representing movements (x, y, z).
        tolerance: The tolerance value for simplification. Smaller values result in less simplification.

    Returns:
        List[Tuple[float, float, float]]: A simplified list of movements.
    """
    if len(movements) <= 2:
        return movements

    simplified_movements: List[Tuple[float, float, float]] = [movements[0]]
    for i in range(1, len(movements) - 1):
        x1, y1, z1 = movements[i-1]
        x2, y2, z2 = movements[i]
        x3, y3, z3 = movements[i+1]

        # Calculate distances from point to line (rudimentary)
        distance = abs((y2 - y1) * x3 - (x2 - x1) * y3 + x2 * y1 - y2 * x1) / math.sqrt((y2 - y1)**2 + (x2 - x1)**2) if (y2 - y1)**2 + (x2 - x1)**2 > 0 else 0
        distance += abs((z2 - z1) - (x2 - x1) * (z3 - z1)/(x3-x1) ) if x3 - x1 != 0 else 0

        if distance > tolerance:
            simplified_movements.append(movements[i])

    simplified_movements.append(movements[-1])
    return simplified_movements


def calculate_dance_similarity(dance1: List[Tuple[float, float, float]], dance2: List[Tuple[float, float, float]]) -> float:
    """
    Calculates the similarity between two dance sequences using a simplified Euclidean distance comparison.

    Args:
        dance1: The first dance sequence (list of movements).
        dance2: The second dance sequence (list of movements).

    Returns:
        float: A similarity score between 0 (completely different) and 1 (identical).
               Returns 0 if either dance sequence is empty.
    """
    if not dance1 or not dance2:
        return 0.0

    min_length = min(len(dance1), len(dance2))
    total_distance = 0.0

    for i in range(min_length):
        x1, y1, z1 = dance1[i]
        x2, y2, z2 = dance2[i]
        distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
        total_distance += distance

    # Normalize the distance to get a similarity score
    max_possible_distance = math.sqrt(3) * min_length  # Assuming maximum displacement of 1 in each dimension
    similarity = 1.0 - (total_distance / max_possible_distance) if max_possible_distance > 0 else 1.0

    return max(0.0, min(1.0, similarity))  # Ensure the score is between 0 and 1


def generate_dance_variation(base_dance: List[Tuple[float, float, float]], variation_factor: float = 0.1) -> List[Tuple[float, float, float]]:
    """
    Generates a variation of a base dance sequence by adding small random displacements to each movement.

    Args:
        base_dance: The base dance sequence (list of movements).
        variation_factor: The factor controlling the amount of variation. Higher values result in more variation.

    Returns:
        List[Tuple[float, float, float]]: A new dance sequence representing a variation of the base dance.
    """
    import random

    variation: List[Tuple[float, float, float]] = []
    for x, y, z in base_dance:
        x_variation = x + random.uniform(-variation_factor, variation_factor)
        y_variation = y + random.uniform(-variation_factor, variation_factor)
        z_variation = z + random.uniform(-variation_factor, variation_factor)
        variation.append((x_variation, y_variation, z_variation))

    return variation