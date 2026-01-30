# konthaina-khqr

KHQR / EMVCo merchant-presented QR payload generator for **Bakong / Cambodia** (NBC KHQR spec v2.7-style TLV) with **CRC-16/CCITT-FALSE** verification.

> This package generates the **payload string** (the EMV tag-length-value text) that you can encode into a QR image.

## Install

```bash
pip install konthaina-khqr
```

Optional: generate QR images (PNG) using `qrcode`:

```bash
pip install "konthaina-khqr[qrcode]"
```

## Quick start

```python
from konthaina_khqr import KHQRGenerator, MerchantType, Currency

result = (
    KHQRGenerator(MerchantType.INDIVIDUAL)
    .set_bakong_account_id("john_smith@devb")
    .set_merchant_name("John Smith")
    .set_currency(Currency.USD)
    .set_amount(100.50)
    .set_merchant_city("Phnom Penh")
    .generate()
)

print(result.qr)     # KHQR payload string
print(result.md5)    # md5 of payload
```

## Verify / decode

```python
from konthaina_khqr import verify, decode

ok = verify(result.qr)
data = decode(result.qr)   # simple TLV decode
```

## CLI

```bash
khqr --type individual --bakong john_smith@devb --name "John Smith" --amount 1.25 --currency USD
```

Generate a PNG (requires extras):

```bash
khqr --type individual --bakong john_smith@devb --name "John Smith" --amount 1.25 --currency USD --png out.png
```

## Development

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff check .
mypy src
```

## Build & publish

Build:

```bash
python -m build
twine check dist/*
```

Publish to **TestPyPI**:

```bash
twine upload -r testpypi dist/*
```

Publish to **PyPI**:

```bash
twine upload dist/*
```

For GitHub Actions + Trusted Publishing, see `.github/workflows/publish.yml`.
