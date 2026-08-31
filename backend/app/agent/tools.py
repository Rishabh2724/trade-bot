from langchain_core.tools import tool

from app.market.coingecko import (
    get_crypto_price,
    get_crypto_market_data,
)

from app.rag.rag_chain import (
    retrieve_documents,
)

from app.analysis.market_analysis import (
    get_market_analysis,
)
# ---------------------------------------
# RAG Tool
# ---------------------------------------

@tool
def search_trading_knowledge(query: str) -> str:
    """
    Search the TradeCopilot knowledge base
    for information about cryptocurrency trading,
    technical analysis, trading strategies,
    risk management, and related research.

    Use this when the user asks about concepts
    or information that may be contained in the
    uploaded trading documents.
    """

    documents = retrieve_documents(
        query,
        top_k=5,
    )

    if not documents:
        return "No relevant information found."

    results = []

    for i, document in enumerate(
        documents,
        start=1,
    ):

        results.append(
            f"""
SOURCE {i}
File: {document['source']}
Page: {document['page']}

{document['text']}
"""
        )

    return "\n".join(results)

# ---------------------------------------
# Market Analysis Tool
# ---------------------------------------

@tool
def analyze_market(
    symbol: str,
    timeframe: str = "15m",
) -> str:
    """
    Run the complete deterministic TradeCopilot
    market-analysis pipeline.

    Uses real OHLCV data and calculates:

    - technical indicators
    - swing market structure
    - internal market structure
    - BOS and CHoCH
    - active Fair Value Gaps
    - buy-side and sell-side liquidity
    - confluence and directional bias
    - validated LONG / SHORT / NO_SETUP
    - risk
    - reward
    - risk/reward ratio

    Python performs the deterministic analysis.
    The LLM should interpret and explain the result
    rather than independently calculating these values.

    Use this when the user asks to analyze a
    cryptocurrency market or trading setup.
    """

    result = get_market_analysis(
        symbol=symbol,
        timeframe=timeframe,
    )

    return str(result)

# ---------------------------------------
# Current Price Tool
# ---------------------------------------

@tool
async def get_current_crypto_price(
    symbol: str,
) -> str:
    """
    Get the current cryptocurrency price,
    24-hour percentage change, market cap,
    and 24-hour volume.

    Use this when the user asks for current
    or live cryptocurrency price information.
    """

    data = await get_crypto_price(
        symbol
    )

    return str(data)


# ---------------------------------------
# Market Data Tool
# ---------------------------------------

@tool
async def get_crypto_chart_data(
    symbol: str,
    days: int = 7,
) -> str:
    """
    Get historical cryptocurrency market data
    including prices, market capitalization,
    and trading volume.

    Use this when the user asks about recent
    price behavior or historical market data.
    """

    data = await get_crypto_market_data(
        symbol,
        days,
    )

    return str(data)