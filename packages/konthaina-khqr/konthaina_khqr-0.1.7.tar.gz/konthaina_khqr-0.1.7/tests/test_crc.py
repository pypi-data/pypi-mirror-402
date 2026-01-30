from konthaina_khqr.crc16 import crc16_ccitt_false


def test_crc16_ccitt_false_known_vector() -> None:
    # Standard test vector for CRC-16/CCITT-FALSE
    assert crc16_ccitt_false("123456789") == "29B1"
