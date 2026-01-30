from __future__ import annotations

from .tlv import decode_tlv


def decode(qr: str) -> dict[str, str]:
    """Decode top-level TLV fields from a KHQR payload."""
    return decode_tlv(qr)
