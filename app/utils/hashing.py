import hashlib
from typing import Union


def sha256_file(data: Union[bytes, bytearray]) -> str:
    """Compute the SHA-256 hex digest of raw file bytes."""
    return hashlib.sha256(data).hexdigest()
