from __future__ import annotations

import pandas as pd


BULLISH = "bullish"
BEARISH = "bearish"

BOS = "BOS"
CHOCH = "CHoCH"


def find_pivots(
    df: pd.DataFrame,
    length: int,
) -> tuple[list[dict], list[dict]]:
    """
    Detect confirmed swing highs and swing lows.

    A pivot is confirmed only after `length` candles
    have formed on both sides of it.

    This avoids using future/unconfirmed price information
    when generating historical structure.
    """

    highs = []
    lows = []

    if len(df) < (length * 2 + 1):
        return highs, lows

    high_values = df["high"].astype(float).tolist()
    low_values = df["low"].astype(float).tolist()

    timestamps = (
        df["timestamp"].tolist()
        if "timestamp" in df.columns
        else list(range(len(df)))
    )

    for i in range(length, len(df) - length):

        current_high = high_values[i]
        current_low = low_values[i]

        left_highs = high_values[i - length:i]
        right_highs = high_values[i + 1:i + length + 1]

        left_lows = low_values[i - length:i]
        right_lows = low_values[i + 1:i + length + 1]

        # -----------------------------------------
        # Pivot High
        # -----------------------------------------

        if (
            current_high >= max(left_highs)
            and current_high >= max(right_highs)
        ):
            highs.append(
                {
                    "index": i,
                    "timestamp": str(timestamps[i]),
                    "price": current_high,
                }
            )

        # -----------------------------------------
        # Pivot Low
        # -----------------------------------------

        if (
            current_low <= min(left_lows)
            and current_low <= min(right_lows)
        ):
            lows.append(
                {
                    "index": i,
                    "timestamp": str(timestamps[i]),
                    "price": current_low,
                }
            )

    return highs, lows


def classify_swings(
    pivots: list[dict],
) -> list[dict]:
    """
    Classify pivots independently by type.

    Highs are compared only with previous highs.
    Lows are compared only with previous lows.

    High:
        HH = Higher High
        LH = Lower High

    Low:
        HL = Higher Low
        LL = Lower Low
    """

    classified = []

    previous_high = None
    previous_low = None

    for pivot in pivots:

        item = {
            **pivot,
            "label": None,
        }

        # -----------------------------------------
        # High
        # -----------------------------------------

        if pivot["type"] == "high":

            if previous_high is not None:

                if pivot["price"] > previous_high:
                    item["label"] = "HH"
                else:
                    item["label"] = "LH"

            previous_high = pivot["price"]

        # -----------------------------------------
        # Low
        # -----------------------------------------

        elif pivot["type"] == "low":

            if previous_low is not None:

                if pivot["price"] > previous_low:
                    item["label"] = "HL"
                else:
                    item["label"] = "LL"

            previous_low = pivot["price"]

        classified.append(item)

    return classified

def build_structure(
    df: pd.DataFrame,
    swing_length: int = 50,
    internal_length: int = 5,
) -> dict:
    """
    Build swing + internal market structure.

    Swing structure:
        Larger market structure.

    Internal structure:
        Shorter-term structure.

    The two lengths intentionally mirror the idea
    used by LuxAlgo, where swing structure and internal
    structure are calculated separately.
    """

    swing_highs, swing_lows = find_pivots(
        df,
        swing_length,
    )

    internal_highs, internal_lows = find_pivots(
        df,
        internal_length,
    )

    swing_pivots = []

    for pivot in swing_highs:
        swing_pivots.append(
            {
                **pivot,
                "type": "high",
            }
        )

    for pivot in swing_lows:
        swing_pivots.append(
            {
                **pivot,
                "type": "low",
            }
        )

    swing_pivots.sort(key=lambda x: x["index"])

    internal_pivots = []

    for pivot in internal_highs:
        internal_pivots.append(
            {
                **pivot,
                "type": "high",
            }
        )

    for pivot in internal_lows:
        internal_pivots.append(
            {
                **pivot,
                "type": "low",
            }
        )

    internal_pivots.sort(key=lambda x: x["index"])

    swing_pivots = classify_swings(swing_pivots)
    internal_pivots = classify_swings(internal_pivots)

    return {
        "swing": {
            "pivots": swing_pivots,
        },
        "internal": {
            "pivots": internal_pivots,
        },
    }

def detect_structure_events(
    df: pd.DataFrame,
    pivots: list[dict],
) -> dict:
    """
    Detect BOS and CHoCH using confirmed pivots.

    Important:
    - Uses candle CLOSE for confirmation.
    - Each pivot can only be broken once.
    - BOS/CHoCH depends on previous structure bias.
    """

    if df.empty or not pivots:
        return {
            "trend": "neutral",
            "events": [],
            "latest_event": None,
        }

    closes = df["close"].astype(float).tolist()
    timestamps = (
        df["timestamp"].tolist()
        if "timestamp" in df.columns
        else list(range(len(df)))
    )

    bullish_pivots = [
        p for p in pivots
        if p["type"] == "high"
    ]

    bearish_pivots = [
        p for p in pivots
        if p["type"] == "low"
    ]

    # Track whether each pivot has already been crossed.
    crossed_highs = set()
    crossed_lows = set()

    bias = "neutral"

    events = []

    # Start checking only after pivot confirmation.
    for i in range(len(closes)):

        close = closes[i]

        # -----------------------------------------
        # Bullish structure break
        # -----------------------------------------

        for pivot_number, pivot in enumerate(
            bullish_pivots
        ):

            pivot_index = pivot["index"]
            pivot_price = pivot["price"]

            # Pivot must already be confirmed
            if pivot_index >= i:
                continue

            if pivot_number in crossed_highs:
                continue

            if close > pivot_price:

                if bias == BEARISH:
                    event_type = CHOCH
                else:
                    event_type = BOS

                event = {
                    "event": event_type,
                    "direction": BULLISH,
                    "level": pivot_price,
                    "pivot_index": pivot_index,
                    "break_index": i,
                    "pivot_timestamp": pivot[
                        "timestamp"
                    ],
                    "break_timestamp": str(
                        timestamps[i]
                    ),
                }

                events.append(event)

                crossed_highs.add(
                    pivot_number
                )

                bias = BULLISH

        # -----------------------------------------
        # Bearish structure break
        # -----------------------------------------

        for pivot_number, pivot in enumerate(
            bearish_pivots
        ):

            pivot_index = pivot["index"]
            pivot_price = pivot["price"]

            if pivot_index >= i:
                continue

            if pivot_number in crossed_lows:
                continue

            if close < pivot_price:

                if bias == BULLISH:
                    event_type = CHOCH
                else:
                    event_type = BOS

                event = {
                    "event": event_type,
                    "direction": BEARISH,
                    "level": pivot_price,
                    "pivot_index": pivot_index,
                    "break_index": i,
                    "pivot_timestamp": pivot[
                        "timestamp"
                    ],
                    "break_timestamp": str(
                        timestamps[i]
                    ),
                }

                events.append(event)

                crossed_lows.add(
                    pivot_number
                )

                bias = BEARISH

    return {
        "trend": bias,
        "events": events,
        "latest_event": (
            events[-1]
            if events
            else None
        ),
    }

def analyze_structure(
    df: pd.DataFrame,
    swing_length: int = 50,
    internal_length: int = 5,
) -> dict:

    structure = build_structure(
        df,
        swing_length=swing_length,
        internal_length=internal_length,
    )

    swing_events = detect_structure_events(
        df,
        structure["swing"]["pivots"],
    )

    internal_events = detect_structure_events(
        df,
        structure["internal"]["pivots"],
    )

    return {
        "swing": {
            "trend": swing_events["trend"],
            "latest_event": swing_events[
                "latest_event"
            ],
            "events": swing_events["events"][-10:],
            "pivots": structure[
                "swing"
            ]["pivots"][-10:],
        },

        "internal": {
            "trend": internal_events["trend"],
            "latest_event": internal_events[
                "latest_event"
            ],
            "events": internal_events["events"][-10:],
            "pivots": structure[
                "internal"
            ]["pivots"][-10:],
        },
    }