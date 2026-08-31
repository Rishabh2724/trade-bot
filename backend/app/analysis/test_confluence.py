import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.market.binance import get_ohlcv
from app.analysis.structure import analyze_structure
from app.analysis.patterns import (
    detect_fvg as analyze_fvg,
    get_active_fvgs,
)
from app.analysis.liquidity import detect_liquidity as analyze_liquidity
from app.analysis.confluence import analyze_confluence


df = get_ohlcv(
    symbol="BTCUSDT",
    interval="15m",
    limit=500,
)

price = float(df["close"].iloc[-1])

structure = analyze_structure(
    df,
    swing_length=50,
    internal_length=5,
)

fvg = {
    "active": get_active_fvgs(df),
}

liquidity = analyze_liquidity(df)

result = analyze_confluence(
    price=price,
    structure=structure,
    fvg=fvg,
    liquidity=liquidity,
)

print("\n================================")
print("CONFLUENCE ANALYSIS")
print("================================\n")

print(
    json.dumps(
        result,
        indent=2,
        default=str,
    )
)