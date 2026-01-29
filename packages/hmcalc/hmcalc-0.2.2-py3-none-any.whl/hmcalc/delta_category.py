def delta_category(old, new, precision=2):
    """
    Categorize the magnitude of change.
    """

    diff = new - old

    if old == 0:
        percent = None
    else:
        percent = (diff / abs(old)) * 100

    if percent is None:
        category = "unknown"
    elif percent == 0:
        category = "no change"
    elif percent < 5:
        category = "tiny increase" if diff > 0 else "tiny decrease"
    elif percent < 20:
        category = "small increase" if diff > 0 else "small decrease"
    elif percent < 50:
        category = "moderate increase" if diff > 0 else "moderate decrease"
    else:
        category = "large increase" if diff > 0 else "large decrease"

    return {
        "absolute": diff,
        "percent": round(percent, precision) if percent is not None else None,
        "category": category
    }
