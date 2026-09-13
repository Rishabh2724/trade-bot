from __future__ import annotations

from typing import Any


DEFAULT_FIB_LEVELS = (
    0.382,
    0.500,
    0.618,
    0.786,
)


def calculate_fib_levels(
    swing_low: float,
    swing_high: float,
    levels: tuple[float, ...] = DEFAULT_FIB_LEVELS,
) -> dict[float, float]:
    """
    Calculate Fibonacci retracement levels.

    Assumes an upward swing:

        swing_low → swing_high

    Retracement levels are measured downward
    from the swing high.
    """

    swing_low = float(swing_low)
    swing_high = float(swing_high)

    if swing_high <= swing_low:
        raise ValueError(
            "swing_high must be greater than swing_low"
        )

    range_size = swing_high - swing_low

    return {
        level: swing_high - (
            range_size * level
        )
        for level in levels
    }


def calculate_bullish_fib_zone(
    swing_low: float,
    swing_high: float,
    lower_level: float = 0.500,
    upper_level: float = 0.786,
) -> dict[str, Any]:
    """
    Fibonacci retracement zone for a bullish setup.

    Example:

        0.500 → 102
        0.786 → 98

    Returned zone is normalized as:

        lower < upper
    """

    levels = calculate_fib_levels(
        swing_low,
        swing_high,
        levels=(
            lower_level,
            upper_level,
        ),
    )

    prices = list(levels.values())

    lower = min(prices)
    upper = max(prices)

    return {
        "type": "bullish",
        "lower_level": lower_level,
        "upper_level": upper_level,
        "lower": lower,
        "upper": upper,
        "levels": levels,
        "swing_low": float(swing_low),
        "swing_high": float(swing_high),
    }


def calculate_bearish_fib_zone(
    swing_high: float,
    swing_low: float,
    lower_level: float = 0.500,
    upper_level: float = 0.786,
) -> dict[str, Any]:
    """
    Fibonacci retracement zone for a bearish setup.

    Assumes a downward swing:

        swing_high → swing_low
    """

    swing_high = float(swing_high)
    swing_low = float(swing_low)

    if swing_high <= swing_low:
        raise ValueError(
            "swing_high must be greater than swing_low"
        )

    range_size = swing_high - swing_low

    levels = {
        lower_level: swing_low + (
            range_size * lower_level
        ),
        upper_level: swing_low + (
            range_size * upper_level
        ),
    }

    prices = list(levels.values())

    return {
        "type": "bearish",
        "lower_level": lower_level,
        "upper_level": upper_level,
        "lower": min(prices),
        "upper": max(prices),
        "levels": levels,
        "swing_low": swing_low,
        "swing_high": swing_high,
    }


def zones_overlap(
    zone_a: dict[str, Any],
    zone_b: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Return the overlapping portion of two price zones.

    Returns None when there is no overlap.
    """

    a_lower = float(zone_a["lower"])
    a_upper = float(zone_a["upper"])

    b_lower = float(zone_b["lower"])
    b_upper = float(zone_b["upper"])

    lower = max(
        a_lower,
        b_lower,
    )

    upper = min(
        a_upper,
        b_upper,
    )

    if lower >= upper:
        return None

    return {
        "lower": lower,
        "upper": upper,
        "size": upper - lower,
        "zone_a": zone_a,
        "zone_b": zone_b,
    }


def price_in_zone(
    price: float,
    zone: dict[str, Any],
) -> bool:
    """
    Check whether a price is inside a zone.
    """

    price = float(price)

    return (
        float(zone["lower"])
        <= price
        <= float(zone["upper"])
    )