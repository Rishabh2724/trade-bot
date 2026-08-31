import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.market.binance import get_ohlcv
from app.analysis.patterns import detect_fvg


df = get_ohlcv(
    symbol="BTCUSDT",
    interval="15m",
    limit=500,
)


fvgs = detect_fvg(df)


print("\n================================")
print("FVG DETECTION")
print("================================")

print(
    f"Total FVGs detected: {len(fvgs)}"
)


for fvg in fvgs[-10:]:

    print(
        f"\nType: {fvg['type']}"
    )

    print(
        f"Time: {fvg['timestamp']}"
    )

    print(
        f"Zone: "
        f"{fvg['lower']} - "
        f"{fvg['upper']}"
    )