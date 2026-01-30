from __future__ import annotations

import argparse
from pathlib import Path

from .enums import Currency, MerchantType
from .generator import KHQRGenerator
from .verify import verify


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="khqr", description="Generate KHQR payload strings (Bakong / Cambodia)"
    )
    p.add_argument("--type", choices=["individual", "merchant"], default="individual")
    p.add_argument("--bakong", required=True, help="Bakong account ID / username")
    p.add_argument("--name", required=True, help="Merchant name")
    p.add_argument("--merchant-id", help="Merchant ID (required for merchant type)")
    p.add_argument("--bank", help="Acquiring bank (required for merchant type)")
    p.add_argument("--currency", choices=["KHR", "USD"], default="KHR")
    p.add_argument("--amount", type=float, help="Amount (optional)")
    p.add_argument("--city", default="Phnom Penh")
    p.add_argument("--bill", help="Bill number (optional)")
    p.add_argument("--mobile", help="Mobile number (optional)")
    p.add_argument("--png", help="Output PNG path (requires konthaina-khqr[qrcode])")
    p.add_argument(
        "--verify", action="store_true", help="Verify generated payload CRC and exit 0/1"
    )
    return p.parse_args()


def _write_png(payload: str, out_path: str) -> None:
    try:
        import qrcode  # type: ignore
    except Exception as e:  # pragma: no cover
        raise SystemExit(
            'PNG output requires optional dependency. Install: pip install "konthaina-khqr[qrcode]"'
        ) from e

    img = qrcode.make(payload)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def main() -> None:
    ns = _parse_args()

    mtype = MerchantType.INDIVIDUAL if ns.type == "individual" else MerchantType.MERCHANT
    g = KHQRGenerator(mtype).set_bakong_account_id(ns.bakong).set_merchant_name(ns.name)

    if ns.type == "merchant":
        if ns.merchant_id:
            g.set_merchant_id(ns.merchant_id)
        if ns.bank:
            g.set_acquiring_bank(ns.bank)

    g.set_currency(Currency.KHR if ns.currency == "KHR" else Currency.USD)
    if ns.amount is not None:
        g.set_amount(ns.amount)
    if ns.city:
        g.set_merchant_city(ns.city)
    if ns.bill:
        g.set_bill_number(ns.bill)
    if ns.mobile:
        g.set_mobile_number(ns.mobile)

    res = g.generate()
    print(res.qr)

    if ns.png:
        _write_png(res.qr, ns.png)

    if ns.verify:
        raise SystemExit(0 if verify(res.qr) else 1)
