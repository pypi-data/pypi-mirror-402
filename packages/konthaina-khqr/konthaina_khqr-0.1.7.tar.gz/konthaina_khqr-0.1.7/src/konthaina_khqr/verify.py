from __future__ import annotations

from .crc16 import crc16_ccitt_false


def verify(qr: str) -> bool:
    """Verify KHQR string by checking CRC tag (63)."""
    if not qr or len(qr) < 10:
        return False
    # CRC is last 4 hex chars; before it should contain "6304"
    extracted_crc = qr[-4:]
    body = qr[:-4]  # includes 6304
    expected = crc16_ccitt_false(body)
    return extracted_crc.upper() == expected.upper()
