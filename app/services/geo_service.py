"""Mock geocoding service for converting location text to GPS coordinates.

Designed so a real geocoding API (Google Maps, Nominatim, etc.)
can replace the mock without changing callers.
"""

from typing import Tuple

# Mock lookup table — extend as needed for demo/testing
_LOCATION_DB: dict[str, Tuple[float, float]] = {
    "accra, independence avenue": (5.5600, -0.1870),
    "accra": (5.6037, -0.1870),
    "kumasi": (6.6885, -1.6244),
    "tema": (5.6698, -0.0166),
    "takoradi": (4.8845, -1.7554),
    "cape coast": (5.1036, -1.2466),
}

_DEFAULT_COORDS: Tuple[float, float] = (5.6037, -0.1870)  # Accra fallback


def geocode(location_text: str) -> Tuple[float, float]:
    """Convert a location description to (latitude, longitude).

    Args:
        location_text: Free-text location from a police report.

    Returns:
        A (lat, lon) tuple.  Falls back to Accra coordinates
        when the location is not recognized.
    """
    # ------------------------------------------------------------------
    # MOCK IMPLEMENTATION
    # In production, replace with a call to a geocoding API.
    # ------------------------------------------------------------------
    key = location_text.strip().lower()
    return _LOCATION_DB.get(key, _DEFAULT_COORDS)
