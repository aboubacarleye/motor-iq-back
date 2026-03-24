"""Extract EXIF metadata from image bytes using Pillow.

Designed so this module can later be swapped with a cloud-based
metadata extraction service without changing callers.
"""

import io
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

logger = logging.getLogger(__name__)

# EXIF tag IDs
_TAG_DATETIME_ORIGINAL = 36867
_TAG_CAMERA_MAKE = 271
_TAG_CAMERA_MODEL = 272
_TAG_SOFTWARE = 305

# Known editing software indicators
EDITING_SOFTWARE_KEYWORDS = [
    "photoshop",
    "gimp",
    "canva",
    "lightroom",
    "snapseed",
    "picsart",
    "afterlight",
    "vsco",
]


def _dms_to_decimal(dms: Tuple, ref: str) -> Optional[float]:
    """Convert EXIF GPS DMS (degrees, minutes, seconds) to decimal degrees."""
    try:
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])
        decimal = degrees + minutes / 60.0 + seconds / 3600.0
        if ref in ("S", "W"):
            decimal = -decimal
        return decimal
    except (TypeError, IndexError, ValueError, ZeroDivisionError):
        return None


def _extract_gps(exif_data: dict) -> Tuple[Optional[float], Optional[float]]:
    """Extract GPS latitude and longitude from EXIF GPS info."""
    gps_info = exif_data.get(34853)  # GPSInfo tag
    if not gps_info:
        return None, None

    # Decode GPS sub-tags
    gps_decoded: Dict[str, Any] = {}
    for tag_id, value in gps_info.items():
        tag_name = GPSTAGS.get(tag_id, tag_id)
        gps_decoded[tag_name] = value

    lat = None
    lon = None

    if "GPSLatitude" in gps_decoded and "GPSLatitudeRef" in gps_decoded:
        lat = _dms_to_decimal(gps_decoded["GPSLatitude"], gps_decoded["GPSLatitudeRef"])

    if "GPSLongitude" in gps_decoded and "GPSLongitudeRef" in gps_decoded:
        lon = _dms_to_decimal(
            gps_decoded["GPSLongitude"], gps_decoded["GPSLongitudeRef"]
        )

    return lat, lon


def extract_exif(file_bytes: bytes) -> Dict[str, Any]:
    """Extract EXIF metadata from image bytes.

    Returns a dict with keys:
        datetime_original  – datetime or None
        gps_lat            – float or None
        gps_lon            – float or None
        camera_make        – str or None
        camera_model       – str or None
        software           – str or None (editing software indicator)
        is_edited          – bool (True if editing software detected)
    """
    result: Dict[str, Any] = {
        "datetime_original": None,
        "gps_lat": None,
        "gps_lon": None,
        "camera_make": None,
        "camera_model": None,
        "software": None,
        "is_edited": False,
    }

    try:
        img = Image.open(io.BytesIO(file_bytes))
        exif_data = img._getexif()  # type: ignore[attr-defined]
        if exif_data is None:
            return result
    except Exception:
        logger.debug("Could not read EXIF from image", exc_info=True)
        return result

    # DateTimeOriginal
    raw_dt = exif_data.get(_TAG_DATETIME_ORIGINAL)
    if raw_dt:
        try:
            result["datetime_original"] = datetime.strptime(
                raw_dt, "%Y:%m:%d %H:%M:%S"
            )
        except (ValueError, TypeError):
            pass

    # GPS
    lat, lon = _extract_gps(exif_data)
    result["gps_lat"] = lat
    result["gps_lon"] = lon

    # Camera info
    result["camera_make"] = exif_data.get(_TAG_CAMERA_MAKE)
    result["camera_model"] = exif_data.get(_TAG_CAMERA_MODEL)

    # Software / editing detection
    software = exif_data.get(_TAG_SOFTWARE)
    if software:
        result["software"] = str(software)
        software_lower = software.lower()
        result["is_edited"] = any(
            kw in software_lower for kw in EDITING_SOFTWARE_KEYWORDS
        )

    return result
