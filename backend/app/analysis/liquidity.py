import pandas as pd


def _cluster_levels(
    levels: list[dict],
    tolerance_percent: float,
) -> list[dict]:
    """
    Group nearby swing levels into liquidity clusters.

    Instead of creating every possible pair of approximately
    equal highs/lows, this produces one representative level
    per cluster.
    """

    if not levels:
        return []

    sorted_levels = sorted(
        levels,
        key=lambda x: x["price"],
    )

    clusters = []

    for level in sorted_levels:

        if not clusters:
            clusters.append([level])
            continue

        cluster = clusters[-1]

        representative_price = sum(
            item["price"]
            for item in cluster
        ) / len(cluster)

        difference = (
            abs(level["price"] - representative_price)
            / representative_price
            * 100
        )

        if difference <= tolerance_percent:
            cluster.append(level)

        else:
            clusters.append([level])

    liquidity = []

    for cluster in clusters:

        if len(cluster) < 2:
            continue

        representative_price = (
            sum(
                item["price"]
                for item in cluster
            )
            / len(cluster)
        )

        # Sort chronologically so first/second remain
        # deterministic.
        cluster = sorted(
            cluster,
            key=lambda x: x["index"],
        )

        liquidity.append(
            {
                "price": round(
                    representative_price,
                    2,
                ),
                "touches": len(cluster),
                "first": cluster[0],
                "second": cluster[1],
                "points": cluster,
            }
        )

    return liquidity



def detect_liquidity(
    df: pd.DataFrame,
    swing_length: int = 5,
    tolerance_percent: float = 0.10,
):
    """
    Detect swing highs/lows and cluster approximately
    equal levels into liquidity pools.

    Equal highs:
        Buy-side liquidity.

    Equal lows:
        Sell-side liquidity.
    """

    if len(df) < (swing_length * 2 + 1):

        return {
            "equal_highs": [],
            "equal_lows": [],
            "buy_side_liquidity": [],
            "sell_side_liquidity": [],
        }

    highs = []
    lows = []

    # ---------------------------------------
    # Detect swing highs / lows
    # ---------------------------------------

    for i in range(
        swing_length,
        len(df) - swing_length,
    ):

        current_high = float(
            df.iloc[i]["high"]
        )

        current_low = float(
            df.iloc[i]["low"]
        )

        left_highs = df.iloc[
            i - swing_length:i
        ]["high"]

        right_highs = df.iloc[
            i + 1:i + swing_length + 1
        ]["high"]

        left_lows = df.iloc[
            i - swing_length:i
        ]["low"]

        right_lows = df.iloc[
            i + 1:i + swing_length + 1
        ]["low"]

        # Swing high
        if (
            current_high >= left_highs.max()
            and current_high >= right_highs.max()
        ):

            highs.append(
                {
                    "index": i,
                    "timestamp": str(
                        df.iloc[i]["timestamp"]
                    ),
                    "price": current_high,
                }
            )

        # Swing low
        if (
            current_low <= left_lows.min()
            and current_low <= right_lows.min()
        ):

            lows.append(
                {
                    "index": i,
                    "timestamp": str(
                        df.iloc[i]["timestamp"]
                    ),
                    "price": current_low,
                }
            )

    # ---------------------------------------
    # Cluster equal highs/lows
    # ---------------------------------------

    equal_highs = _cluster_levels(
        highs,
        tolerance_percent,
    )

    equal_lows = _cluster_levels(
        lows,
        tolerance_percent,
    )

    # ---------------------------------------
    # Liquidity classification
    # ---------------------------------------

    buy_side_liquidity = [
        {
            "type": "buy_side",
            "price": level["price"],
            "source": "equal_highs",
            "touches": level["touches"],
        }
        for level in equal_highs
    ]

    sell_side_liquidity = [
        {
            "type": "sell_side",
            "price": level["price"],
            "source": "equal_lows",
            "touches": level["touches"],
        }
        for level in equal_lows
    ]

    return {
        "equal_highs": equal_highs,
        "equal_lows": equal_lows,
        "buy_side_liquidity": buy_side_liquidity,
        "sell_side_liquidity": sell_side_liquidity,
    }
def detect_liquidity_sweeps(
    df: pd.DataFrame,
    liquidity: dict,
    reclaim_required: bool = True,
) -> list[dict]:
    """
    Detect price sweeping known liquidity levels.

    Sell-side liquidity sweep:

        candle low < liquidity level
        AND
        candle closes back above liquidity level

    Buy-side liquidity sweep:

        candle high > liquidity level
        AND
        candle closes back below liquidity level

    Important:
    liquidity levels must be generated using data
    available before the sweep candle when used
    inside a backtest.
    """

    required = {
        "timestamp",
        "high",
        "low",
        "close",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    buy_side = liquidity.get(
        "buy_side_liquidity",
        [],
    )

    sell_side = liquidity.get(
        "sell_side_liquidity",
        [],
    )

    sweeps = []

    for i in range(len(df)):

        candle = df.iloc[i]

        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])

        # =====================================
        # SELL-SIDE LIQUIDITY
        # =====================================

        for level in sell_side:

            liquidity_price = float(
                level["price"]
            )

            if low >= liquidity_price:
                continue

            reclaimed = (
                close > liquidity_price
            )

            if reclaim_required and not reclaimed:
                continue

            sweeps.append(
                {
                    "index": i,
                    "timestamp": str(
                        candle["timestamp"]
                    ),
                    "type": "sell_side_sweep",
                    "direction": "bullish",
                    "liquidity_price": (
                        liquidity_price
                    ),
                    "sweep_price": low,
                    "reclaimed": reclaimed,
                    "liquidity": level,
                }
            )

        # =====================================
        # BUY-SIDE LIQUIDITY
        # =====================================

        for level in buy_side:

            liquidity_price = float(
                level["price"]
            )

            if high <= liquidity_price:
                continue

            reclaimed = (
                close < liquidity_price
            )

            if reclaim_required and not reclaimed:
                continue

            sweeps.append(
                {
                    "index": i,
                    "timestamp": str(
                        candle["timestamp"]
                    ),
                    "type": "buy_side_sweep",
                    "direction": "bearish",
                    "liquidity_price": (
                        liquidity_price
                    ),
                    "sweep_price": high,
                    "reclaimed": reclaimed,
                    "liquidity": level,
                }
            )

    sweeps.sort(
        key=lambda x: x["index"]
    )

    return sweeps