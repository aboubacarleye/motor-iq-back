"""Mock OCR service for extracting structured data from police reports.

Returns simulated structured data from a police report file.
Designed so a real OCR backend (Tesseract, Google Document AI, etc.)
can replace the mock without changing callers.
"""

from typing import Any, Dict


def extract_police_report(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract structured fields from a police report.

    Args:
        file_bytes: Raw bytes of the uploaded police report (PDF or image).
        filename:   Original filename (used for logging / future format detection).

    Returns:
        Dict with keys: incident_date, incident_time, location_text,
        plate_number, damage_description.
    """
    # ------------------------------------------------------------------
    # MOCK IMPLEMENTATION
    # In production, replace this body with a call to an OCR engine:
    #   - pytesseract for local processing
    #   - Google Document AI for cloud processing
    #   - Azure Form Recognizer, etc.
    # The return schema must remain the same.
    # ------------------------------------------------------------------
    return {
        "incident_date": "2026-03-15",
        "incident_time": "14:30",
        "location_text": "Accra, Independence Avenue",
        "plate_number": "GR-1234-20",
        "damage_description": (
            "Front bumper severely dented. Right headlight cracked. "
            "Scratches on the hood extending to the right fender."
        ),
    }
