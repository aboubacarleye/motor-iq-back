"""Image processing worker.

Orchestrates EXIF extraction, hashing, and (mock) damage detection
for each uploaded claim image.
"""

import logging
from typing import Any, Dict, List, Tuple

from app.services.exif_service import extract_exif
from app.utils.hashing import sha256_file

logger = logging.getLogger(__name__)

# Mock damage labels — placeholder for a real CV model
_MOCK_DAMAGE = "front bumper dent, scratches on hood, cracked headlight"


def process_images(
    file_data_list: List[Tuple[str, bytes]],
) -> List[Dict[str, Any]]:
    """Process a batch of claim images.

    Args:
        file_data_list: List of (filename, raw_bytes) tuples.

    Returns:
        List of result dicts, one per image, containing:
            filename, file_hash, exif (dict), detected_damage (str).
    """
    results: List[Dict[str, Any]] = []

    for filename, file_bytes in file_data_list:
        exif = extract_exif(file_bytes)
        file_hash = sha256_file(file_bytes)

        # ------------------------------------------------------------------
        # MOCK: damage detection placeholder
        # Replace with a real CV model call (e.g. YOLO, Gemini Vision) later.
        # ------------------------------------------------------------------
        detected_damage = _MOCK_DAMAGE

        results.append(
            {
                "filename": filename,
                "file_hash": file_hash,
                "exif": exif,
                "detected_damage": detected_damage,
            }
        )
        logger.debug("Processed image %s (hash=%s)", filename, file_hash[:12])

    return results
