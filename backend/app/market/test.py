import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.market.binance import get_ohlcv


df = get_ohlcv(
    symbol="BTCUSDT",
    interval="15m",
    limit=10,
)


print("\n================================")
print("BINANCE OHLCV TEST")
print("================================")

print(df[
    [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
].to_string(index=False))