from __future__ import annotations

from enum import Enum


class Currency(str, Enum):
    """Currency numeric codes used in KHQR."""

    KHR = "116"
    USD = "840"


class MerchantType(str, Enum):
    """Merchant account structure used in KHQR."""

    INDIVIDUAL = "individual"
    MERCHANT = "merchant"
