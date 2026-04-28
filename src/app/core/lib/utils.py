import re


def parse_currency_amount(text: str | None) -> float | None:
    """Parses a string like '$73,951.40', '$1.48T', or '1,200,300 BTC' to float."""
    if not text:
        return None

    cleaned = text.strip().replace("$", "").replace(",", "")

    # Handle multipliers if present (T=Trillion, B=Billion, M=Million)
    multipliers = {"T": 1e12, "B": 1e9, "M": 1e6}
    suffix = cleaned[-1].upper() if cleaned else ""

    try:
        if suffix in multipliers:
            val = float(re.sub(r"[^\d.]", "", cleaned[:-1]))
            return val * multipliers[suffix]
        else:
            val_str = re.sub(r"[^\d.]", "", cleaned)
            return float(val_str) if val_str else None
    except (ValueError, IndexError):
        return None


def normalize_string(text: str) -> str:
    return text.split("/")[0].strip().lower()
