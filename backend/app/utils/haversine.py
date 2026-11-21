import math
from typing import Tuple


EARTH_RADIUS_KM = 6371.0


def calculate_haversine_distance(
    coord1: Tuple[float, float],
    coord2: Tuple[float, float]
) -> float:
    """
    Calculates the great-circle distance between two points on Earth in kilometers.
    coord1: (latitude, longitude) of point 1 in decimal degrees
    coord2: (latitude, longitude) of point 2 in decimal degrees
    Returns distance rounded to 2 decimal places.
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Convert decimal degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    # Clamp 'a' to [0, 1] to prevent math domain error due to floating point rounding
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = EARTH_RADIUS_KM * c
    return round(distance, 2)


def is_within_radius(
    center_coord: Tuple[float, float],
    target_coord: Tuple[float, float],
    radius_km: float = 10.0
) -> Tuple[bool, float]:
    """
    Determines if target coordinate falls within the specified radius from center.
    Returns (is_match, calculated_distance_km).
    """
    dist = calculate_haversine_distance(center_coord, target_coord)
    return (dist <= radius_km), dist