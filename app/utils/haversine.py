import math
from typing import Optional, Tuple


def haversine_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Return the great-circle distance in kilometres between two GPS points."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def safe_distance(
    coords1: Optional[Tuple[float, float]],
    coords2: Optional[Tuple[float, float]],
) -> Optional[float]:
    """Return distance in km, or None if either coordinate pair is missing."""
    if coords1 is None or coords2 is None:
        return None
    return haversine_km(coords1[0], coords1[1], coords2[0], coords2[1])
