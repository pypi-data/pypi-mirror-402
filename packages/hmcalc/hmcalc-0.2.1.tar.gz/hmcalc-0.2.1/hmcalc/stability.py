def stability(values, precision=2):
    """
    Determine whether a sequence is stable or noisy.
    """

    if not values or len(values) < 2:
        return {
            "stable": True,
            "variation_percent": 0.0,
            "label": "stable"
        }

    min_v = min(values)
    max_v = max(values)

    if min_v == 0:
        variation = None
    else:
        variation = ((max_v - min_v) / abs(min_v)) * 100

    if variation is None:
        label = "unknown"
        stable = False
    elif variation <= 5:
        label = "very stable"
        stable = True
    elif variation <= 15:
        label = "stable"
        stable = True
    elif variation <= 30:
        label = "unstable"
        stable = False
    else:
        label = "very unstable"
        stable = False

    return {
        "stable": stable,
        "variation_percent": round(variation, precision) if variation is not None else None,
        "label": label
    }
