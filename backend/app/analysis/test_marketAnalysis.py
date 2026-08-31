import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from app.analysis.market_analysis import (
    get_market_analysis,
)


result = get_market_analysis(
    symbol="BTCUSDT",
    timeframe="15m",
    limit=500,
)


print("\n================================")
print("MARKET ANALYSIS")
print("================================\n")

print(
    json.dumps(
        result,
        indent=2,
    )
)