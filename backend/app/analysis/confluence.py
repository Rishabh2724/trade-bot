from typing import Any


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _distance_from_price(
    level: float,
    price: float,
) -> float:
    return abs(level - price)


def _distance_from_zone(
    level: float,
    entry_low: float,
    entry_high: float,
) -> float:
    """
    Distance from a price level to an entry zone.

    0.0 means the level is inside the zone.
    Otherwise returns distance to the nearest edge.
    """
    if entry_low <= level <= entry_high:
        return 0.0

    return min(
        abs(level - entry_low),
        abs(level - entry_high),
    )


def _filter_liquidity(
    liquidity: list[dict[str, Any]],
    *,
    direction: str,
    entry_low: float,
    entry_high: float,
) -> list[dict[str, Any]]:

    valid = []

    for level in liquidity:

        price = _safe_float(level.get("price"))

        if price is None:
            continue

        if direction == "bullish":

            # LONG stop liquidity must be below entry.
            if price < entry_low:
                valid.append(level)

        elif direction == "bearish":

            # SHORT stop liquidity must be above entry.
            if price > entry_high:
                valid.append(level)

    return valid


def _filter_target_liquidity(
    liquidity: list[dict[str, Any]],
    *,
    direction: str,
    entry_low: float,
    entry_high: float,
) -> list[dict[str, Any]]:

    valid = []

    for level in liquidity:

        price = _safe_float(level.get("price"))

        if price is None:
            continue

        if direction == "bullish":

            # LONG target must be above entry.
            if price > entry_high:
                valid.append(level)

        elif direction == "bearish":

            # SHORT target must be below entry.
            if price < entry_low:
                valid.append(level)

    return valid


def _nearest(
    levels: list[dict[str, Any]],
    entry_low: float,
    entry_high: float,
) -> dict[str, Any] | None:

    if not levels:
        return None

    valid_levels = []

    for level in levels:

        price = _safe_float(level.get("price"))

        if price is None:
            continue

        distance = _distance_from_zone(
            price,
            entry_low,
            entry_high,
        )

        valid_levels.append(
            (
                distance,
                price,
                level,
            )
        )

    if not valid_levels:
        return None

    valid_levels.sort(
        key=lambda item: item[0]
    )

    return valid_levels[0][2]


def _select_candidate_fvg(
    price: float,
    fvgs: list[dict[str, Any]],
    direction: str,
) -> dict[str, Any] | None:

    candidates = []

    for fvg in fvgs:

        if fvg.get("mitigated", False):
            continue

        if fvg.get("type") != direction:
            continue

        lower = _safe_float(
            fvg.get("lower")
        )

        upper = _safe_float(
            fvg.get("upper")
        )

        if lower is None or upper is None:
            continue

        if lower > upper:
            lower, upper = upper, lower

        if lower <= price <= upper:

            distance = 0.0

        else:

            distance = min(
                abs(price - lower),
                abs(price - upper),
            )

        candidates.append(
            (
                distance,
                -int(
                    fvg.get(
                        "formation_index",
                        0,
                    )
                ),
                fvg,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    selected = candidates[0][2]

    selected_lower = _safe_float(
        selected.get("lower")
    )

    selected_upper = _safe_float(
        selected.get("upper")
    )

    if selected_lower is not None and selected_upper is not None:

        selected = dict(selected)

        selected["lower"] = min(
            selected_lower,
            selected_upper,
        )

        selected["upper"] = max(
            selected_lower,
            selected_upper,
        )

        selected["distance"] = candidates[0][0]

    return selected


def _select_best_directional_fvg(
    price: float,
    fvgs: list[dict[str, Any]],
    direction: str,
) -> dict[str, Any] | None:
    """
    Select the nearest unmitigated FVG in the requested direction.

    Preference:
    1. FVG containing current price.
    2. Nearest FVG to current price.
    3. Most recent FVG when distances are equal.
    """

    return _select_candidate_fvg(
        price,
        fvgs,
        direction,
    )


def _liquidity_description(
    liquidity: dict[str, Any] | None,
) -> str | None:

    if not liquidity:
        return None

    price = _safe_float(
        liquidity.get("price")
    )

    if price is None:
        return None

    source = liquidity.get(
        "source",
        "liquidity",
    )

    touches = liquidity.get(
        "touches"
    )

    if touches is not None:
        return (
            f"{source} near {price:.2f} "
            f"({touches} touches)"
        )

    return (
        f"{source} near {price:.2f}"
    )


def analyze_confluence(
    price: float,
    structure: dict[str, Any],
    fvg: list[dict[str, Any]],
    liquidity: dict[str, Any],
) -> dict[str, Any]:

    # ---------------------------------------
    # Structure
    # ---------------------------------------

    swing_trend = structure.get(
        "swing_trend",
        structure.get(
            "swing",
            {}
        ).get(
            "trend",
            "mixed",
        ),
    )

    internal_trend = structure.get(
        "internal_trend",
        structure.get(
            "internal",
            {}
        ).get(
            "trend",
            "mixed",
        ),
    )

    swing_events = structure.get(
        "swing_events",
        structure.get(
            "swing",
            {}
        ).get(
            "events",
            [],
        ),
    )

    internal_events = structure.get(
        "internal_events",
        structure.get(
            "internal",
            {}
        ).get(
            "events",
            [],
        ),
    )

    latest_swing_event = (
        swing_events[-1]
        if swing_events
        else None
    )

    latest_internal_event = (
        internal_events[-1]
        if internal_events
        else None
    )

    # ---------------------------------------
    # Structure scoring
    # ---------------------------------------

    bullish_score = 0
    bearish_score = 0

    bullish_factors: list[str] = []
    bearish_factors: list[str] = []
    conflicting_factors: list[str] = []

    if (
        swing_trend == "bullish"
        and internal_trend == "bullish"
    ):

        bullish_score += 2

        bullish_factors.append(
            "Swing and internal structure are bullish"
        )

    elif (
        swing_trend == "bearish"
        and internal_trend == "bearish"
    ):

        bearish_score += 2

        bearish_factors.append(
            "Swing and internal structure are bearish"
        )

    else:

        conflicting_factors.append(
            "Swing and internal structure are not aligned"
        )

    # ---------------------------------------
    # Latest structural events
    # ---------------------------------------

    if latest_swing_event:

        event = latest_swing_event.get(
            "event"
        )

        direction = latest_swing_event.get(
            "direction"
        )

        if direction == "bullish":

            bullish_score += 1

            bullish_factors.append(
                f"Latest swing event: "
                f"{event} bullish"
            )

        elif direction == "bearish":

            bearish_score += 1

            bearish_factors.append(
                f"Latest swing event: "
                f"{event} bearish"
            )

    if latest_internal_event:

        event = latest_internal_event.get(
            "event"
        )

        direction = latest_internal_event.get(
            "direction"
        )

        if direction == "bullish":

            bullish_score += 1

            bullish_factors.append(
                f"Latest internal event: "
                f"{event} bullish"
            )

        elif direction == "bearish":

            bearish_score += 1

            bearish_factors.append(
                f"Latest internal event: "
                f"{event} bearish"
            )

    # ---------------------------------------
    # Candidate FVGs
    # ---------------------------------------

    bullish_fvg = _select_best_directional_fvg(
        price,
        fvg,
        "bullish",
    )

    bearish_fvg = _select_best_directional_fvg(
        price,
        fvg,
        "bearish",
    )

    # ---------------------------------------
    # FVG scoring
    # ---------------------------------------

    if bullish_fvg:

        distance = _safe_float(
            bullish_fvg.get(
                "distance",
                0,
            )
        )

        if distance is None:
            distance = 0.0

        bullish_score += 1

        bullish_factors.append(
            f"Nearby bullish FVG is "
            f"{distance:.2f} away"
        )

    if bearish_fvg:

        distance = _safe_float(
            bearish_fvg.get(
                "distance",
                0,
            )
        )

        if distance is None:
            distance = 0.0

        bearish_score += 1

        bearish_factors.append(
            f"Nearby bearish FVG is "
            f"{distance:.2f} away"
        )

    # ---------------------------------------
    # Determine directional bias
    # ---------------------------------------

    if bullish_score > bearish_score:

        bias = "bullish"

    elif bearish_score > bullish_score:

        bias = "bearish"

    else:

        bias = "mixed"

    # ---------------------------------------
    # Liquidity
    # ---------------------------------------

    buy_side = liquidity.get(
        "buy_side_liquidity",
        [],
    )

    sell_side = liquidity.get(
        "sell_side_liquidity",
        [],
    )

    nearest_buy_side = None
    nearest_sell_side = None

    selected_fvg = None

    # ---------------------------------------
    # Bullish setup context
    # ---------------------------------------

    if bias == "bullish" and bullish_fvg:

        selected_fvg = bullish_fvg

        entry_low = float(
            bullish_fvg["lower"]
        )

        entry_high = float(
            bullish_fvg["upper"]
        )

        valid_stops = _filter_liquidity(
            sell_side,
            direction="bullish",
            entry_low=entry_low,
            entry_high=entry_high,
        )

        valid_targets = _filter_target_liquidity(
            buy_side,
            direction="bullish",
            entry_low=entry_low,
            entry_high=entry_high,
        )

        nearest_sell_side = _nearest(
            valid_stops,
            entry_low,
            entry_high,
        )

        nearest_buy_side = _nearest(
            valid_targets,
            entry_low,
            entry_high,
        )

    # ---------------------------------------
    # Bearish setup context
    # ---------------------------------------

    elif bias == "bearish" and bearish_fvg:

        selected_fvg = bearish_fvg

        entry_low = float(
            bearish_fvg["lower"]
        )

        entry_high = float(
            bearish_fvg["upper"]
        )

        valid_stops = _filter_liquidity(
            buy_side,
            direction="bearish",
            entry_low=entry_low,
            entry_high=entry_high,
        )

        valid_targets = _filter_target_liquidity(
            sell_side,
            direction="bearish",
            entry_low=entry_low,
            entry_high=entry_high,
        )

        nearest_buy_side = _nearest(
            valid_stops,
            entry_low,
            entry_high,
        )

        nearest_sell_side = _nearest(
            valid_targets,
            entry_low,
            entry_high,
        )

    # ---------------------------------------
    # Liquidity context
    # ---------------------------------------

    if nearest_buy_side:

        description = _liquidity_description(
            nearest_buy_side
        )

        if description:

            if bias == "bullish":
                bullish_factors.append(
                    f"Target {description}"
                )

            elif bias == "bearish":
                bearish_factors.append(
                    f"Stop {description}"
                )

    if nearest_sell_side:

        description = _liquidity_description(
            nearest_sell_side
        )

        if description:

            if bias == "bullish":
                bullish_factors.append(
                    f"Stop {description}"
                )

            elif bias == "bearish":
                bearish_factors.append(
                    f"Target {description}"
                )

    # ---------------------------------------
    # Strength
    # ---------------------------------------

    dominant_score = max(
        bullish_score,
        bearish_score,
    )

    if dominant_score >= 5:

        strength = "strong"

    elif dominant_score >= 3:

        strength = "moderate"

    else:

        strength = "weak"

    # ---------------------------------------
    # Reasons
    # ---------------------------------------

    reasons = (
        bullish_factors
        + bearish_factors
        + conflicting_factors
    )

    # ---------------------------------------
    # Result
    # ---------------------------------------

    return {
        "bias": bias,
        "strength": strength,

        "score": dominant_score,

        "bullish_score": bullish_score,
        "bearish_score": bearish_score,

        "bullish_factors": bullish_factors,
        "bearish_factors": bearish_factors,

        "conflicting_factors": conflicting_factors,

        "latest_swing_event": latest_swing_event,
        "latest_internal_event": latest_internal_event,

        "bullish_fvg": bullish_fvg,
        "bearish_fvg": bearish_fvg,

        "selected_fvg": selected_fvg,

        "nearby_fvgs": fvg,

        "nearest_buy_side_liquidity": (
            nearest_buy_side
        ),

        "nearest_sell_side_liquidity": (
            nearest_sell_side
        ),

        "reasons": reasons,
    }
