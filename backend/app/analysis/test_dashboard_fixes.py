"""
Regression tests for three bugs the dashboard work exposed.

Unlike test_context.py these need the real backend dependencies (pandas,
pydantic) because they exercise the analysis engine end to end. No network:
get_ohlcv is monkeypatched with synthetic candles.

Run from backend/:
    python3 -m app.analysis.test_dashboard_fixes
"""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.analysis import market_analysis
from app.analysis.indicators import calculate_rsi
from app.schemas.analysis import MarketAnalysisResponse

CANDLES = 250

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"[PASS] {label}")
    else:
        failures.append(label)
        print(f"[FAIL] {label}{f': {detail}' if detail else ''}")


def timestamps(count):
    return pd.date_range(
        "2026-01-01",
        periods=count,
        freq="15min",
        tz="UTC",
    )


def flat_frame(price=100.0, count=CANDLES):
    """Every candle identical: no pivots, no gaps, no price movement."""
    return pd.DataFrame(
        {
            "timestamp": timestamps(count),
            "open": [price] * count,
            "high": [price] * count,
            "low": [price] * count,
            "close": [price] * count,
            "volume": [1.0] * count,
        }
    )


def staircase_frame(count=CANDLES, step=10.0):
    """
    Strictly rising staircase where each candle's low is above the previous
    candle's high. Every consecutive triple therefore forms a bullish FVG,
    and price never trades back down, so none of them are ever mitigated.
    """
    lows = [100.0 + index * step for index in range(count)]

    return pd.DataFrame(
        {
            "timestamp": timestamps(count),
            "open": [low + 1.0 for low in lows],
            "high": [low + step * 0.5 for low in lows],
            "low": lows,
            "close": [low + step * 0.4 for low in lows],
            "volume": [1.0] * count,
        }
    )


def analyze_with(frame):
    original = market_analysis.get_ohlcv
    market_analysis.get_ohlcv = lambda symbol, interval, limit: frame
    try:
        return market_analysis.get_market_analysis("TESTUSDT", "15m", len(frame))
    finally:
        market_analysis.get_ohlcv = original


# ------------------------------------------------------------
# Bug 3: flat price made RSI NaN, which is not valid JSON
# ------------------------------------------------------------

rsi_flat = calculate_rsi([100.0] * 100)

check(
    "flat price gives a finite RSI",
    rsi_flat == rsi_flat,  # NaN is the only value not equal to itself
    f"got {rsi_flat}",
)

check(
    "flat price RSI is the neutral 50",
    rsi_flat == 50,
    f"got {rsi_flat}",
)


# ------------------------------------------------------------
# Bug 1: structure trend "neutral" failed response validation
# ------------------------------------------------------------
# A flat frame has no confirmed pivots, so no structure break can happen and
# both layers come back "neutral". Before the schema fix this raised a
# pydantic ValidationError, which FastAPI turns into a 500.

flat_result = analyze_with(flat_frame())

check(
    "flat frame yields a neutral structure trend",
    flat_result["structure"]["swing"]["trend"] == "neutral",
    f"got {flat_result['structure']['swing']['trend']}",
)

try:
    validated = MarketAnalysisResponse(**flat_result)
    check("neutral structure trend passes response validation", True)
except Exception as error:  # noqa: BLE001 - want the message in the report
    check(
        "neutral structure trend passes response validation",
        False,
        f"{type(error).__name__}: {error}",
    )


# ------------------------------------------------------------
# Bug 2: fvg.zones returned the OLDEST zones, and active_count was capped
# ------------------------------------------------------------

stair_result = analyze_with(staircase_frame())

zones = stair_result["fvg"]["zones"]
active_count = stair_result["fvg"]["active_count"]

check(
    "staircase frame produces more than 20 active FVGs",
    active_count > 20,
    f"got {active_count}",
)

check(
    "active_count is not capped at the 20-zone retention window",
    active_count != 20,
    f"got {active_count}",
)

check(
    "at most 10 zones are returned",
    len(zones) <= 10,
    f"got {len(zones)}",
)

indices = [zone["formation_index"] for zone in zones]

check(
    "zones are the most recent, not the oldest",
    all(index > CANDLES // 2 for index in indices),
    f"formation indices {indices}",
)

check(
    "zones stay in chronological order",
    indices == sorted(indices),
    f"formation indices {indices}",
)

try:
    MarketAnalysisResponse(**stair_result)
    check("staircase result passes response validation", True)
except Exception as error:  # noqa: BLE001
    check(
        "staircase result passes response validation",
        False,
        f"{type(error).__name__}: {error}",
    )


print()
print(
    "RESULT: ALL PASS"
    if not failures
    else f"RESULT: {len(failures)} FAILURE(S) -> {failures}"
)
sys.exit(1 if failures else 0)
