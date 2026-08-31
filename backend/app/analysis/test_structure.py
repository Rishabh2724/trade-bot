import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.market.binance import get_ohlcv
from app.analysis.structure import analyze_structure


df = get_ohlcv(
    symbol="BTCUSDT",
    interval="15m",
    limit=500,
)

result = analyze_structure(
    df,
    swing_length=50,
    internal_length=5,
)

print("\n================================")
print("MARKET STRUCTURE")
print("================================\n")

print(
    json.dumps(
        result,
        indent=2,
        default=str,
    )
)