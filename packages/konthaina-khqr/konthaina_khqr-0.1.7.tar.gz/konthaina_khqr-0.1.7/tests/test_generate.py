from konthaina_khqr import Currency, KHQRGenerator, MerchantType, verify


def test_generate_and_verify() -> None:
    res = (
        KHQRGenerator(MerchantType.INDIVIDUAL)
        .set_bakong_account_id("john_smith@devb")
        .set_merchant_name("John Smith")
        .set_currency(Currency.USD)
        .set_amount(1.25)
        .generate()
    )
    assert res.qr.startswith("000201010212")
    assert verify(res.qr) is True
