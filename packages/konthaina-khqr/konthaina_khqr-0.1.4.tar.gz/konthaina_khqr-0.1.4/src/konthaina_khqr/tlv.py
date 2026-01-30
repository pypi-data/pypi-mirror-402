from __future__ import annotations


def format_tag(tag: str, value: str) -> str:
    """Format EMVCo tag-length-value segment."""
    if value is None or value == "":
        return ""
    length = str(len(value)).zfill(2)
    return f"{tag}{length}{value}"


def decode_tlv(payload: str) -> dict[str, str]:
    """Decode a *flat* TLV string into a dict of tag->value.

    Notes:
      - KHQR has nested templates (e.g., tag 29/30/62/64). This helper is intentionally simple:
        it only parses the top-level TLV into raw strings.
      - Use this for debugging/logging; not as a full KHQR parser.
    """
    i = 0
    out: dict[str, str] = {}
    while i + 4 <= len(payload):
        tag = payload[i : i + 2]
        length = int(payload[i + 2 : i + 4])
        start = i + 4
        end = start + length
        if end > len(payload):
            break
        out[tag] = payload[start:end]
        i = end
    return out
