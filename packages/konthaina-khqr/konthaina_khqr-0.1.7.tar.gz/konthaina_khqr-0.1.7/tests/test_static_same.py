from konthaina_khqr import KHQRGenerator, MerchantType


def test_static_qr_is_stable_when_no_amount() -> None:
    a = (
        KHQRGenerator(MerchantType.INDIVIDUAL)
        .set_bakong_account_id("kon_thaina@cadi")
        .set_merchant_name("Kon Thaina")
        .generate()
        .qr
    )

    b = (
        KHQRGenerator(MerchantType.INDIVIDUAL)
        .set_bakong_account_id("kon_thaina@cadi")
        .set_merchant_name("Kon Thaina")
        .generate()
        .qr
    )

    assert a == b
