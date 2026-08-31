import pandas as pd


# ============================================================
# FAIR VALUE GAPS
# ============================================================

def detect_fvg(
    df: pd.DataFrame,
    min_gap_percent: float = 0.03,
) -> list[dict]:

    required = {
        "timestamp",
        "open",
        "high",
        "low",
        "close",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    fvgs = []

    for i in range(2, len(df)):

        candle_1 = df.iloc[i - 2]
        candle_2 = df.iloc[i - 1]
        candle_3 = df.iloc[i]

        # ====================================================
        # BULLISH FVG
        #
        # Candle 1 high < Candle 3 low
        # ====================================================

        if candle_1["high"] < candle_3["low"]:

            lower = float(candle_1["high"])
            upper = float(candle_3["low"])

            gap_size = upper - lower

            gap_percent = (
                gap_size / lower
            ) * 100

            if gap_percent >= min_gap_percent:

                fvgs.append({
                    "type": "bullish",
                    "timestamp": str(
                        candle_3["timestamp"]
                    ),
                    "lower": lower,
                    "upper": upper,
                    "size": gap_size,
                    "size_percent": gap_percent,
                    "formation_index": i,
                })

        # ====================================================
        # BEARISH FVG
        #
        # Candle 1 low > Candle 3 high
        # ====================================================

        if candle_1["low"] > candle_3["high"]:

            lower = float(candle_3["high"])
            upper = float(candle_1["low"])

            gap_size = upper - lower

            gap_percent = (
                gap_size / upper
            ) * 100

            if gap_percent >= min_gap_percent:

                fvgs.append({
                    "type": "bearish",
                    "timestamp": str(
                        candle_3["timestamp"]
                    ),
                    "lower": lower,
                    "upper": upper,
                    "size": gap_size,
                    "size_percent": gap_percent,
                    "formation_index": i,
                })

    return fvgs


def get_relevant_fvgs(
    df: pd.DataFrame,
    current_price: float,
    min_gap_percent: float = 0.03,
    max_distance_percent: float = 2.0,
) -> list[dict]:

    active_fvgs = get_active_fvgs(
        df,
        min_gap_percent=min_gap_percent,
    )

    relevant = []

    for fvg in active_fvgs:

        lower = fvg["lower"]
        upper = fvg["upper"]

        # Distance from current price to the zone
        if current_price < lower:
            distance = lower - current_price

        elif current_price > upper:
            distance = current_price - upper

        else:
            distance = 0

        distance_percent = (
            distance / current_price
        ) * 100

        if distance_percent <= max_distance_percent:

            fvg["distance"] = distance
            fvg["distance_percent"] = distance_percent

            # Price is currently inside the FVG
            if lower <= current_price <= upper:
                fvg["position"] = "inside"

            elif current_price < lower:
                fvg["position"] = "above_price"

            else:
                fvg["position"] = "below_price"

            relevant.append(fvg)

    # Nearest FVGs first
    relevant.sort(
        key=lambda x: x["distance"]
    )

    return relevant

# ============================================================
# FVG MITIGATION
# ============================================================

def check_fvg_mitigation(
    df: pd.DataFrame,
    fvg: dict,
) -> bool:

    formation_index = fvg["formation_index"]

    future_candles = df.iloc[
        formation_index + 1:
    ]

    lower = fvg["lower"]
    upper = fvg["upper"]

    for _, candle in future_candles.iterrows():

        candle_low = float(candle["low"])
        candle_high = float(candle["high"])

        # --------------------------------------------
        # Bullish FVG
        # --------------------------------------------

        if fvg["type"] == "bullish":

            # Price completely trades through the zone
            if candle_low <= lower:
                return True

        # --------------------------------------------
        # Bearish FVG
        # --------------------------------------------

        elif fvg["type"] == "bearish":

            # Price completely trades through the zone
            if candle_high >= upper:
                return True

    return False


# ============================================================
# ACTIVE FVGs
# ============================================================

def get_active_fvgs(
    df: pd.DataFrame,
    min_gap_percent: float = 0.03,
) -> list[dict]:

    fvgs = detect_fvg(
        df,
        min_gap_percent=min_gap_percent,
    )

    active_fvgs = []

    for fvg in fvgs:

        mitigated = check_fvg_mitigation(
            df,
            fvg,
        )

        fvg["mitigated"] = mitigated

        if not mitigated:
            active_fvgs.append(fvg)

    return active_fvgs


# ============================================================
# SWING HIGH / SWING LOW
# ============================================================

def detect_swings(
    df: pd.DataFrame,
    lookback: int = 3,
) -> dict:

    swing_highs = []
    swing_lows = []

    for i in range(
        lookback,
        len(df) - lookback,
    ):

        current_high = df["high"].iloc[i]
        current_low = df["low"].iloc[i]

        left_highs = df["high"].iloc[
            i - lookback:i
        ]

        right_highs = df["high"].iloc[
            i + 1:i + lookback + 1
        ]

        left_lows = df["low"].iloc[
            i - lookback:i
        ]

        right_lows = df["low"].iloc[
            i + 1:i + lookback + 1
        ]

        # Swing high
        if (
            current_high > left_highs.max()
            and current_high > right_highs.max()
        ):

            swing_highs.append({
                "index": i,
                "timestamp": str(
                    df["timestamp"].iloc[i]
                ),
                "price": float(
                    current_high
                ),
            })

        # Swing low
        if (
            current_low < left_lows.min()
            and current_low < right_lows.min()
        ):

            swing_lows.append({
                "index": i,
                "timestamp": str(
                    df["timestamp"].iloc[i]
                ),
                "price": float(
                    current_low
                ),
            })

    return {
        "swing_highs": swing_highs,
        "swing_lows": swing_lows,
    }


# ============================================================
# MARKET STRUCTURE
# ============================================================

def analyze_market_structure(
    df: pd.DataFrame,
    lookback: int = 3,
) -> dict:

    swings = detect_swings(
        df,
        lookback=lookback,
    )

    highs = swings["swing_highs"]
    lows = swings["swing_lows"]

    structure = "unknown"

    if len(highs) >= 2 and len(lows) >= 2:

        previous_high = highs[-2]["price"]
        latest_high = highs[-1]["price"]

        previous_low = lows[-2]["price"]
        latest_low = lows[-1]["price"]

        if (
            latest_high > previous_high
            and latest_low > previous_low
        ):
            structure = "bullish"

        elif (
            latest_high < previous_high
            and latest_low < previous_low
        ):
            structure = "bearish"

        else:
            structure = "mixed"

    return {
        "structure": structure,

        "latest_swing_high": (
            highs[-1]
            if highs
            else None
        ),

        "previous_swing_high": (
            highs[-2]
            if len(highs) >= 2
            else None
        ),

        "latest_swing_low": (
            lows[-1]
            if lows
            else None
        ),

        "previous_swing_low": (
            lows[-2]
            if len(lows) >= 2
            else None
        ),
    }