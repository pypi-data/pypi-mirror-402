from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Union

from .crc16 import crc16_ccitt_false
from .enums import Currency, MerchantType
from .exceptions import KHQRValidationError
from .tlv import format_tag


@dataclass(frozen=True)
class KHQRResult:
    qr: str
    timestamp: str
    type: str
    md5: str


class KHQRGenerator:
    """KHQR payload generator (merchant-presented).

    Generates KHQR payment payload strings compliant with the NBC KHQR v2.7-style layout.
    """

    def __init__(self, merchant_type: MerchantType = MerchantType.INDIVIDUAL):
        self.merchant_type = merchant_type
        self.data: dict[str, str] = {}

    # -----------------------
    # Builder setters
    # -----------------------
    def set_bakong_account_id(self, account_id: str) -> KHQRGenerator:
        self.data["bakong_account_id"] = (account_id or "")[:32]
        return self

    def set_merchant_name(self, name: str) -> KHQRGenerator:
        self.data["merchant_name"] = (name or "")[:25]
        return self

    def set_merchant_id(self, merchant_id: str) -> KHQRGenerator:
        self.data["merchant_id"] = (merchant_id or "")[:32]
        return self

    def set_acquiring_bank(self, bank: str) -> KHQRGenerator:
        self.data["acquiring_bank"] = (bank or "")[:32]
        return self

    def set_account_information(self, info: str) -> KHQRGenerator:
        self.data["account_information"] = (info or "")[:32]
        return self

    def set_currency(self, currency: Union[str, Currency]) -> KHQRGenerator:
        if isinstance(currency, str):
            cur = currency.upper().strip()
            currency = Currency.KHR if cur == "KHR" else Currency.USD
        self.data["currency"] = currency.value
        return self

    def set_amount(self, amount: float) -> KHQRGenerator:
        self.data["amount"] = f"{amount:.2f}"
        return self

    def set_merchant_city(self, city: str) -> KHQRGenerator:
        self.data["merchant_city"] = (city or "")[:15]
        return self

    def set_bill_number(self, bill_number: str) -> KHQRGenerator:
        self.data["bill_number"] = (bill_number or "")[:25]
        return self

    def set_mobile_number(self, mobile: str) -> KHQRGenerator:
        self.data["mobile_number"] = (mobile or "")[:25]
        return self

    def set_store_label(self, label: str) -> KHQRGenerator:
        self.data["store_label"] = (label or "")[:25]
        return self

    def set_terminal_label(self, label: str) -> KHQRGenerator:
        self.data["terminal_label"] = (label or "")[:25]
        return self

    def set_purpose_of_transaction(self, purpose: str) -> KHQRGenerator:
        self.data["purpose_of_transaction"] = (purpose or "")[:25]
        return self

    def set_upi_account_information(self, upi: str) -> KHQRGenerator:
        self.data["upi_account_information"] = (upi or "")[:31]
        return self

    def set_language_preference(self, lang: str) -> KHQRGenerator:
        self.data["language_preference"] = (lang or "")[:2]
        return self

    def set_merchant_name_alternate(self, name: str) -> KHQRGenerator:
        self.data["merchant_name_alternate"] = (name or "")[:25]
        return self

    def set_merchant_city_alternate(self, city: str) -> KHQRGenerator:
        self.data["merchant_city_alternate"] = (city or "")[:15]
        return self

    # -----------------------
    # Generate
    # -----------------------
    def generate(self) -> KHQRResult:
        self._validate()

        qr = ""
        qr += format_tag("00", "01")  # Payload Format Indicator
        qr += format_tag("01", "12")  # Point of Initiation Method (static)

        # UPI Merchant Account (Tag 15) - Optional
        if self.data.get("upi_account_information"):
            qr += format_tag("15", self.data["upi_account_information"])

        # Account information template
        if self.merchant_type == MerchantType.INDIVIDUAL:
            tag29 = format_tag("00", self.data["bakong_account_id"])
            if self.data.get("account_information"):
                tag29 += format_tag("01", self.data["account_information"])
            if self.data.get("acquiring_bank"):
                tag29 += format_tag("02", self.data["acquiring_bank"])
            qr += format_tag("29", tag29)
        else:
            tag30 = format_tag("00", self.data["bakong_account_id"])
            tag30 += format_tag("01", self.data["merchant_id"])
            tag30 += format_tag("02", self.data["acquiring_bank"])
            qr += format_tag("30", tag30)

        qr += format_tag("52", "5999")  # Merchant Category Code
        qr += format_tag("53", self.data.get("currency", Currency.KHR.value))  # Currency

        if self.data.get("amount"):
            qr += format_tag("54", self.data["amount"])

        qr += format_tag("58", "KH")  # Country Code
        qr += format_tag("59", self.data["merchant_name"])
        qr += format_tag("60", self.data.get("merchant_city", "Phnom Penh"))

        # Additional Data Field (Tag 62)
        tag62 = ""
        if self.data.get("bill_number"):
            tag62 += format_tag("01", self.data["bill_number"])
        if self.data.get("mobile_number"):
            tag62 += format_tag("02", self.data["mobile_number"])
        if self.data.get("store_label"):
            tag62 += format_tag("03", self.data["store_label"])
        if self.data.get("terminal_label"):
            tag62 += format_tag("07", self.data["terminal_label"])
        if self.data.get("purpose_of_transaction"):
            tag62 += format_tag("08", self.data["purpose_of_transaction"])
        if tag62:
            qr += format_tag("62", tag62)

        # Merchant Alternate Language (Tag 64)
        tag64 = ""
        if self.data.get("language_preference"):
            tag64 += format_tag("00", self.data["language_preference"])
        if self.data.get("merchant_name_alternate"):
            tag64 += format_tag("01", self.data["merchant_name_alternate"])
        if self.data.get("merchant_city_alternate"):
            tag64 += format_tag("02", self.data["merchant_city_alternate"])
        if tag64:
            qr += format_tag("64", tag64)

        # Timestamp (Tag 99) - proprietary
        timestamp = str(int(time.time() * 1000))
        qr += format_tag("99", format_tag("00", timestamp))

        # CRC (Tag 63)
        crc = crc16_ccitt_false(qr + "6304")
        qr += "6304" + crc

        return KHQRResult(
            qr=qr,
            timestamp=timestamp,
            type=self.merchant_type.value,
            md5=hashlib.md5(qr.encode("utf-8")).hexdigest(),
        )

    def _validate(self) -> None:
        if not self.data.get("bakong_account_id") or not self.data.get("merchant_name"):
            raise KHQRValidationError("Bakong Account ID and Merchant Name are required")

        if self.merchant_type == MerchantType.MERCHANT:
            if not self.data.get("merchant_id") or not self.data.get("acquiring_bank"):
                raise KHQRValidationError(
                    "Merchant ID and Acquiring Bank are required for merchant type"
                )
