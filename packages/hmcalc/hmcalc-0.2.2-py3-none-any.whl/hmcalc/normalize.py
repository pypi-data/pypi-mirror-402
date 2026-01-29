def normalize(value, min_value, max_value, precision=3):
    """
    Normalize a value into a human-readable scale.
    """

    if max_value == min_value:
        return {
            "normalized": None,
            "percent": None,
            "position": "undefined"
        }

    norm = (value - min_value) / (max_value - min_value)
    pct = norm * 100

    if pct < 20:
        position = "very low"
    elif pct < 40:
        position = "low"
    elif pct < 60:
        position = "medium"
    elif pct < 80:
        position = "high"
    else:
        position = "very high"

    return {
        "normalized": round(norm, precision),
        "percent": round(pct, 2),
        "position": position
    }
