import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agent.tools import (
    search_trading_knowledge,
    get_current_crypto_price,
    get_crypto_chart_data,
    analyze_market,
)


print("\nAVAILABLE TOOLS")
print("================")

for tool in [
    search_trading_knowledge,
    get_current_crypto_price,
    get_crypto_chart_data,
    analyze_market,
]:

    print(
        f"\nName: {tool.name}"
    )

    print(
        f"Description: {tool.description}"
    )

    print(
        f"Schema: {tool.args_schema.model_json_schema()}"
    )