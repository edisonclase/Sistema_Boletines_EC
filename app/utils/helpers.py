import pandas as pd


def safe_value(value, default=""):
    if pd.isna(value):
        return default
    return str(value).strip()