from __future__ import annotations

import pandas as pd

from app.analysis.indicators import calculate_atr


BULLISH = "bullish"
BEARISH = "bearish"


def detect_displacement(
    df: pd.DataFrame,
    atr_period: int = 14,
    atr_multiplier: float = 1.5,
) -> list[dict]:
    """
    Detect strong directional candles.

    Bullish displacement:

        close > open
        body >= ATR * multiplier

    Bearish displacement:

        close < open
        body >= ATR * multiplier

    This intentionally does not define displacement
    using subjective concepts such as "strong candle".
    """

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

    if len(df) < atr_period:
        return []

    atr = calculate_atr(
        df,
        period=atr_period,
    )

    results = []

    for i in range(len(df)):

        current_atr = atr.iloc[i]

        if pd.isna(current_atr):
            continue

        candle = df.iloc[i]

        open_price = float(candle["open"])
        close_price = float(candle["close"])

        body = abs(
            close_price - open_price
        )

        threshold = (
            float(current_atr)
            * atr_multiplier
        )

        if body < threshold:
            continue

        if close_price > open_price:
            direction = BULLISH

        elif close_price < open_price:
            direction = BEARISH

        else:
            continue

        results.append(
            {
                "index": i,
                "timestamp": str(
                    candle["timestamp"]
                ),
                "direction": direction,
                "open": open_price,
                "close": close_price,
                "body": body,
                "atr": float(current_atr),
                "atr_multiplier": (
                    body / float(current_atr)
                ),
            }
        )

    return results