def range_summary(values):
    """
    Summarize the spread of values.
    """

    if not values:
        return {
            "min": None,
            "max": None,
            "range": None,
            "label": "empty"
        }

    min_v = min(values)
    max_v = max(values)
    spread = max_v - min_v

    if spread == 0:
        label = "flat"
    elif spread <= abs(min_v) * 0.1:
        label = "tight"
    elif spread <= abs(min_v) * 0.3:
        label = "moderate"
    else:
        label = "wide"

    return {
        "min": min_v,
        "max": max_v,
        "range": spread,
        "label": label
    }
