import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.market.binance import get_ohlcv

from app.analysis.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
)

from app.analysis.structure import (
    analyze_structure,
)

from app.analysis.patterns import (
    get_active_fvgs,
)

from app.analysis.liquidity import (
    detect_liquidity,
)

from app.analysis.confluence import (
    analyze_confluence,
)

from app.analysis.setup import (
    generate_setup,
)

SUPPORTED_TIMEFRAMES = {
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
}

def get_market_analysis(
    
    symbol: str = "BTCUSDT",
    timeframe: str = "15m",
    limit: int = 500,
) -> dict:

    # ---------------------------------------
    # Market data
    # ---------------------------------------
    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise ValueError(
            f"Unsupported timeframe: {timeframe}"
    )
    if not symbol:
        raise ValueError(
        "Symbol is required."
    )

    symbol = symbol.upper()
    df = get_ohlcv(
        symbol=symbol,
        interval=timeframe,
        limit=limit,
    )

    if len(df) < 200:
        raise ValueError(
            "Not enough candles for analysis."
        )

    current_price = float(
        df["close"].iloc[-1]
    )

    prices = (
        df["close"]
        .astype(float)
        .tolist()
    )

    # ---------------------------------------
    # Indicators
    # ---------------------------------------

    rsi = float(
        calculate_rsi(
            prices,
            14,
        )
    )

    indicators = {
        "sma_20": float(
            calculate_sma(
                prices,
                20,
            )
        ),

        "sma_50": float(
            calculate_sma(
                prices,
                50,
            )
        ),

        "ema_20": float(
            calculate_ema(
                prices,
                20,
            )
        ),

        "ema_50": float(
            calculate_ema(
                prices,
                50,
            )
        ),

        "ema_200": float(
            calculate_ema(
                prices,
                200,
            )
        ),

        "rsi_14": rsi,
    }

    # ---------------------------------------
    # Simple trend context
    # ---------------------------------------

    if (
        current_price > indicators["ema_50"]
        and indicators["ema_50"]
        > indicators["ema_200"]
    ):

        trend = "bullish"

    elif (
        current_price < indicators["ema_50"]
        and indicators["ema_50"]
        < indicators["ema_200"]
    ):

        trend = "bearish"

    else:

        trend = "mixed"

    # ---------------------------------------
    # RSI context
    # ---------------------------------------

    if rsi >= 70:

        rsi_condition = "overbought"

    elif rsi <= 30:

        rsi_condition = "oversold"

    else:

        rsi_condition = "neutral"

    # ---------------------------------------
    # Market structure
    # ---------------------------------------

    structure = analyze_structure(
        df,
        swing_length=50,
        internal_length=5,
    )

    # ---------------------------------------
    # Active FVGs
    # ---------------------------------------

    active_fvgs = get_active_fvgs(
        df,
        min_gap_percent=0.03,
    )

    # Keep the output manageable.
    active_fvgs = active_fvgs[-20:]

    # ---------------------------------------
    # Liquidity
    # ---------------------------------------

    liquidity = detect_liquidity(
        df,
        swing_length=5,
        tolerance_percent=0.10,
    )

    # ---------------------------------------
    # Confluence
    # ---------------------------------------

    confluence = analyze_confluence(
        price=current_price,
        structure=structure,
        fvg=active_fvgs,
        liquidity=liquidity,
    )

    # ---------------------------------------
    # Trade setup
    # ---------------------------------------

    setup = generate_setup(
        price=current_price,
        confluence=confluence,
    )

    # ---------------------------------------
    # Final unified result
    # ---------------------------------------

    return {
        "market": {
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": current_price,
        },

        "trend": trend,

        "indicators": indicators,

        "rsi_condition": rsi_condition,

        "structure": structure,

        "fvg": {
            "active_count": len(active_fvgs),
            "zones": active_fvgs[:10],
        },

        "liquidity": liquidity,

        "confluence": confluence,

        "setup": setup,
    }
