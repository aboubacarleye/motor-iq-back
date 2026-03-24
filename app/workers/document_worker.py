"""Document processing worker.

Orchestrates OCR extraction, geocoding, and hashing for an uploaded
police report.
"""

import logging
from typing import Any, Dict

from app.services.geo_service import geocode
from app.services.ocr_service import extract_police_report
from app.utils.hashing import sha256_file

logger = logging.getLogger(__name__)


def process_report(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Process a police report file.

    Args:
        file_bytes: Raw bytes of the uploaded police report.
        filename:   Original filename.

    Returns:
        Dict containing OCR-extracted fields plus geocoded GPS
        and a file hash.
    """
    report_data = extract_police_report(file_bytes, filename)

    # Geocode the location text to GPS coordinates
    lat, lon = geocode(report_data.get("location_text", ""))
    report_data["gps_lat"] = lat
    report_data["gps_lon"] = lon

    # File integrity hash
    report_data["file_hash"] = sha256_file(file_bytes)
    report_data["filename"] = filename

    logger.debug(
        "Processed report %s → location (%s, %s)",
        filename,
        lat,
        lon,
    )
    return report_data
