import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.market.binance import get_ohlcv
from app.analysis.liquidity import detect_liquidity


df = get_ohlcv(
    symbol="BTCUSDT",
    interval="15m",
    limit=500,
)

result = detect_liquidity(
    df,
    swing_length=5,
    tolerance_percent=0.10,
)

print("\n================================")
print("LIQUIDITY ANALYSIS")
print("================================\n")

print(
    json.dumps(
        result,
        indent=2,
        default=str,
    )
)