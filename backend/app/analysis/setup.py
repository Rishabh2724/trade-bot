from typing import Any


MIN_RISK_REWARD = 1.5
MIN_TARGET_DISTANCE_PERCENT = 0.10


def _level(zone: dict[str, Any] | None) -> float | None:
    if not isinstance(zone, dict):
        return None

    for key in ("price", "level", "upper", "lower"):
        value = zone.get(key)

        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

    return None


def _nearest_fvg(
    fvgs: list[dict[str, Any]],
    price: float,
    fvg_type: str,
) -> dict[str, Any] | None:

    candidates = [
        fvg
        for fvg in fvgs
        if fvg.get("type") == fvg_type
        and not fvg.get("mitigated", False)
    ]

    if not candidates:
        return None

    def distance(fvg: dict[str, Any]) -> float:
        lower = float(fvg["lower"])
        upper = float(fvg["upper"])

        if lower <= price <= upper:
            return 0.0

        if upper < price:
            return price - upper

        return lower - price

    return min(candidates, key=distance)


def _liquidity_source(
    zone: dict[str, Any] | None,
    fallback: str,
) -> str:

    if not isinstance(zone, dict):
        return fallback

    source = zone.get("source")

    if source:
        return str(source)

    return fallback


def _target_is_meaningful(
    entry_reference: float,
    target: float,
) -> bool:

    if entry_reference <= 0:
        return False

    distance_percent = (
        abs(target - entry_reference)
        / entry_reference
        * 100
    )

    return (
        distance_percent
        >= MIN_TARGET_DISTANCE_PERCENT
    )


def _no_setup(
    result: dict[str, Any],
    reasons: list[str],
) -> dict[str, Any]:

    result["reasons"] = reasons.copy()

    return result


def generate_setup(
    price: float,
    confluence: dict[str, Any],
) -> dict[str, Any]:

    bias = confluence.get("bias", "mixed")

    bullish_score = int(
        confluence.get("bullish_score", 0)
    )

    bearish_score = int(
        confluence.get("bearish_score", 0)
    )

    bullish_factors = confluence.get(
        "bullish_factors",
        [],
    )

    bearish_factors = confluence.get(
        "bearish_factors",
        [],
    )

    conflicting_factors = confluence.get(
        "conflicting_factors",
        [],
    )

    fvgs = confluence.get(
        "nearby_fvgs",
        [],
    )

    buy_side = confluence.get(
        "nearest_buy_side_liquidity"
    )

    sell_side = confluence.get(
        "nearest_sell_side_liquidity"
    )

    # ---------------------------------------
    # Default result
    # ---------------------------------------

    result = {
        "setup": "NO_SETUP",
        "direction": None,
        "confidence": "low",
        "score": 0,

        "entry_zone": None,
        "entry_source": None,

        "stop_loss": None,
        "stop_source": None,

        "targets": [],
        "target_source": None,

        "risk": None,
        "reward": None,
        "risk_reward": None,

        "reasons": [],
        "conflicts": conflicting_factors.copy(),
        "invalidated_if": None,
    }

    # ---------------------------------------
    # LONG SETUP
    # ---------------------------------------

    if bias == "bullish":

        if bullish_score < 4:

            return _no_setup(
                result,
                [
                    "Bullish bias exists but "
                    "confluence score is insufficient"
                ],
            )

        bullish_fvg = _nearest_fvg(
            fvgs,
            price,
            "bullish",
        )

        if not bullish_fvg:

            return _no_setup(
                result,
                bullish_factors
                + [
                    "No active bullish FVG "
                    "available for entry"
                ],
            )

        lower = float(
            bullish_fvg["lower"]
        )

        upper = float(
            bullish_fvg["upper"]
        )

        # -----------------------------------
        # Stop-loss
        # -----------------------------------

        stop_loss = _level(
            sell_side
        )

        if stop_loss is None:

            return _no_setup(
                result,
                bullish_factors
                + [
                    "No valid sell-side liquidity "
                    "available for stop-loss"
                ],
            )

        # Stop must be below the entire
        # long entry zone.
        if stop_loss >= lower:

            return _no_setup(
                result,
                bullish_factors
                + [
                    "Invalid LONG stop-loss geometry: "
                    "stop-loss must be below entry zone"
                ],
            )

        # -----------------------------------
        # Target
        # -----------------------------------

        target = _level(
            buy_side
        )

        if target is None:

            return _no_setup(
                result,
                bullish_factors
                + [
                    "No valid buy-side liquidity "
                    "available for target"
                ],
            )

        # Target must be above the entire
        # long entry zone.
        if target <= upper:

            return _no_setup(
                result,
                bullish_factors
                + [
                    "Invalid LONG target geometry: "
                    "target must be above entry zone"
                ],
            )

        # -----------------------------------
        # Risk / reward
        # -----------------------------------

        # Conservative calculation:
        # enter at the worst side of the zone.
        risk = lower - stop_loss
        reward = target - upper

        if risk <= 0 or reward <= 0:

            return _no_setup(
                result,
                bullish_factors
                + [
                    "Invalid LONG risk/reward geometry"
                ],
            )

        if not _target_is_meaningful(
            upper,
            target,
        ):

            return _no_setup(
                result,
                bullish_factors
                + [
                    "LONG target is too close "
                    "to the entry zone"
                ],
            )

        risk_reward = reward / risk

        if risk_reward < MIN_RISK_REWARD:

            return _no_setup(
                result,
                bullish_factors
                + [
                    f"Risk/reward is only "
                    f"{risk_reward:.2f}R"
                ],
            )

        # -----------------------------------
        # Valid LONG
        # -----------------------------------

        result.update({
            "setup": "LONG",
            "direction": "bullish",
            "confidence": (
                "high"
                if (
                    bullish_score >= 5
                    and risk_reward >= 2
                )
                else "moderate"
            ),
            "score": bullish_score,

            "entry_zone": [
                lower,
                upper,
            ],

            "entry_source": (
                f"bullish FVG "
                f"{bullish_fvg.get('timestamp', '')}"
            ),

            "stop_loss": stop_loss,

            "stop_source": _liquidity_source(
                sell_side,
                "sell-side liquidity",
            ),

            "targets": [
                target
            ],

            "target_source": _liquidity_source(
                buy_side,
                "buy-side liquidity",
            ),

            "risk": round(
                risk,
                2,
            ),

            "reward": round(
                reward,
                2,
            ),

            "risk_reward": round(
                risk_reward,
                2,
            ),

            "reasons": bullish_factors.copy(),

            "invalidated_if": (
                f"Price closes below "
                f"{lower:.2f}"
            ),
        })

        return result

    # ---------------------------------------
    # SHORT SETUP
    # ---------------------------------------

    if bias == "bearish":

        if bearish_score < 4:

            return _no_setup(
                result,
                [
                    "Bearish bias exists but "
                    "confluence score is insufficient"
                ],
            )

        bearish_fvg = _nearest_fvg(
            fvgs,
            price,
            "bearish",
        )

        if not bearish_fvg:

            return _no_setup(
                result,
                bearish_factors
                + [
                    "No active bearish FVG "
                    "available for entry"
                ],
            )

        lower = float(
            bearish_fvg["lower"]
        )

        upper = float(
            bearish_fvg["upper"]
        )

        # -----------------------------------
        # Stop-loss
        # -----------------------------------

        stop_loss = _level(
            buy_side
        )

        if stop_loss is None:

            return _no_setup(
                result,
                bearish_factors
                + [
                    "No valid buy-side liquidity "
                    "available for stop-loss"
                ],
            )

        # Stop must be above the entire
        # short entry zone.
        if stop_loss <= upper:

            return _no_setup(
                result,
                bearish_factors
                + [
                    "Invalid SHORT stop-loss geometry: "
                    "stop-loss must be above entry zone"
                ],
            )

        # -----------------------------------
        # Target
        # -----------------------------------

        target = _level(
            sell_side
        )

        if target is None:

            return _no_setup(
                result,
                bearish_factors
                + [
                    "No valid sell-side liquidity "
                    "available for target"
                ],
            )

        # Target must be below the entire
        # short entry zone.
        if target >= lower:

            return _no_setup(
                result,
                bearish_factors
                + [
                    "Invalid SHORT target geometry: "
                    "target must be below entry zone"
                ],
            )

        # -----------------------------------
        # Risk / reward
        # -----------------------------------

        # Conservative calculation:
        # enter at the worst side of the zone.
        risk = stop_loss - upper
        reward = lower - target

        if risk <= 0 or reward <= 0:

            return _no_setup(
                result,
                bearish_factors
                + [
                    "Invalid SHORT risk/reward geometry"
                ],
            )

        if not _target_is_meaningful(
            lower,
            target,
        ):

            return _no_setup(
                result,
                bearish_factors
                + [
                    "SHORT target is too close "
                    "to the entry zone"
                ],
            )

        risk_reward = reward / risk

        if risk_reward < MIN_RISK_REWARD:

            return _no_setup(
                result,
                bearish_factors
                + [
                    f"Risk/reward is only "
                    f"{risk_reward:.2f}R"
                ],
            )

        # -----------------------------------
        # Valid SHORT
        # -----------------------------------

        result.update({
            "setup": "SHORT",
            "direction": "bearish",
            "confidence": (
                "high"
                if (
                    bearish_score >= 5
                    and risk_reward >= 2
                )
                else "moderate"
            ),
            "score": bearish_score,

            "entry_zone": [
                lower,
                upper,
            ],

            "entry_source": (
                f"bearish FVG "
                f"{bearish_fvg.get('timestamp', '')}"
            ),

            "stop_loss": stop_loss,

            "stop_source": _liquidity_source(
                buy_side,
                "buy-side liquidity",
            ),

            "targets": [
                target
            ],

            "target_source": _liquidity_source(
                sell_side,
                "sell-side liquidity",
            ),

            "risk": round(
                risk,
                2,
            ),

            "reward": round(
                reward,
                2,
            ),

            "risk_reward": round(
                risk_reward,
                2,
            ),

            "reasons": bearish_factors.copy(),

            "invalidated_if": (
                f"Price closes above "
                f"{upper:.2f}"
            ),
        })

        return result

    # ---------------------------------------
    # MIXED / UNKNOWN
    # ---------------------------------------

    if bias == "mixed":

        result["reasons"].append(
            "Market structure is mixed"
        )

    elif bias == "bullish":

        result["reasons"].append(
            "Bullish bias exists but "
            "setup conditions are incomplete"
        )

    elif bias == "bearish":

        result["reasons"].append(
            "Bearish bias exists but "
            "setup conditions are incomplete"
        )

    return result