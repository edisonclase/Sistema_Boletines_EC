def safe_value(value, default=""):
    if value is None:
        return default
    return value