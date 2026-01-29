def closeness(a, b, precision=2):
    """
    How close are two values, in human terms?
    """

    diff = abs(a - b)

    if b == 0:
        percent = None
    else:
        percent = (diff / abs(b)) * 100

    if percent is None:
        label = "unknown"
    elif percent <= 1:
        label = "extremely close"
    elif percent <= 5:
        label = "very close"
    elif percent <= 10:
        label = "close"
    elif percent <= 25:
        label = "far"
    else:
        label = "very far"

    return {
        "distance": diff,
        "percent": round(percent, precision) if percent is not None else None,
        "label": label
    }
