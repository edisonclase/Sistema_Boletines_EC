import pandas as pd


def safe_value(value, default=""):
    if pd.isna(value):
        return default
    return str(value).strip()


def format_grade(value):
    text = safe_value(value)

    if text in {"", "0", "0.0"}:
        return ""

    if "/" in text or "%" in text:
        return text

    try:
        number = float(text)
        if number == 0:
            return ""
        if number.is_integer():
            return str(int(number))
        return str(number)
    except ValueError:
        return text


def is_low_grade(value, passing_grade=70):
    text = safe_value(value)

    if not text or "/" in text or "%" in text:
        return False

    try:
        return float(text) < passing_grade
    except ValueError:
        return False