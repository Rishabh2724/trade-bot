from app.analysis.market_analysis import get_market_analysis


def analyze_market(
    symbol: str,
    timeframe: str = "15m",
    limit: int = 500,
) -> dict:

    return get_market_analysis(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )