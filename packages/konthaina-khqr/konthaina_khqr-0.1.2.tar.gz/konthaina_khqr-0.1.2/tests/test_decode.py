from konthaina_khqr import KHQRGenerator, decode


def test_decode_top_level_tags() -> None:
    res = KHQRGenerator().set_bakong_account_id("user@bank").set_merchant_name("Test").generate()
    data = decode(res.qr)
    assert data["00"] == "01"
    assert data["58"] == "KH"
    assert data["63"].startswith("")  # top-level decode will store '63' value (CRC)
