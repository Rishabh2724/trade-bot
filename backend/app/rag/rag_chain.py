import os
import re

from dotenv import load_dotenv
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI,
)
from langchain_core.prompts import ChatPromptTemplate
from pinecone import Pinecone

from app.services.chat_history import get_messages
from app.services.analysis_service import analyze_market


load_dotenv()


# ============================================================
# Configuration
# ============================================================

PINECONE_NAMESPACE = "trading-v1"

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ============================================================
# Validation
# ============================================================

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is missing")

if not PINECONE_INDEX_NAME:
    raise ValueError("PINECONE_INDEX_NAME is missing")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing")


# ============================================================
# Pinecone
# ============================================================

pc = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pc.Index(
    PINECONE_INDEX_NAME
)


# ============================================================
# Embeddings
# ============================================================

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview",
    output_dimensionality=768,
    client_args={"trust_env": False},
)


# ============================================================
# Gemini
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0.2,
)


# ============================================================
# Prompt
# ============================================================

prompt = ChatPromptTemplate.from_template(
    """
You are TradeCopilot, an AI trading research assistant.

Your job is to answer questions using:

1. Conversation history
2. Static trading knowledge from the knowledge base
3. Live deterministic market analysis when provided

IMPORTANT RULES:

1. LIVE MARKET ANALYSIS is authoritative for current market
   information such as:
   - current price
   - trend
   - RSI
   - moving averages
   - market structure
   - BOS
   - CHoCH
   - FVG
   - liquidity
   - confluence
   - trade setup
   - entry
   - stop loss
   - targets
   - risk/reward

2. The KNOWLEDGE BASE contains static trading research.
   Use it for explanations, concepts, definitions, strategies,
   and research-backed information.

3. Do not invent market data.

4. Do not invent values that are missing from LIVE MARKET
   ANALYSIS.

5. If live market analysis is unavailable, clearly state that
   current market data could not be retrieved.

6. Use conversation history to understand references such as:
   "it", "this setup", "that trade", or "what about BTC?"

7. Do not claim that any trading strategy guarantees profits.

8. Clearly distinguish between:
   - factual market data
   - knowledge-base information
   - your interpretation

9. Whenever you make a claim based on the knowledge base,
   include the source citation in this format:

   [Source: filename, p. X]

10. Keep answers structured and easy to understand.

11. When discussing a trade setup, explain the reasoning and
    invalidation conditions. Do not present the setup as a
    guaranteed trade.

12. If the market structure or confluence is conflicting,
    explicitly mention that conflict.

------------------------------------------------------------
CONVERSATION HISTORY
------------------------------------------------------------

{history}

------------------------------------------------------------
KNOWLEDGE BASE
------------------------------------------------------------

{context}

------------------------------------------------------------
LIVE MARKET ANALYSIS
------------------------------------------------------------

{live_analysis}

------------------------------------------------------------
USER QUESTION
------------------------------------------------------------

{question}

------------------------------------------------------------
ANSWER
------------------------------------------------------------
"""
)


# ============================================================
# Conversation History
# ============================================================

def build_conversation_history(
    conversation_id: str,
) -> str:

    messages = get_messages(
        conversation_id=conversation_id,
    )

    # The current user message has already been stored
    # by the chat route and is passed separately as {question}.
    if messages:
        messages = messages[:-1]

    if not messages:
        return "No previous conversation."

    history_lines = []

    for message in messages:

        role = message["role"].upper()

        history_lines.append(
            f"{role}: {message['content']}"
        )

    return "\n\n".join(history_lines)


# ============================================================
# Pinecone Retrieval
# ============================================================

def retrieve_documents(
    query: str,
    top_k: int = 5,
):
    query_vector = embeddings.embed_query(query)

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=PINECONE_NAMESPACE,
    )

    documents = []

    for match in results.matches or []:

        metadata = match.metadata or {}

        documents.append(
            {
                "text": metadata.get(
                    "text",
                    "",
                ),
                "source": metadata.get(
                    "source",
                    "Unknown",
                ),
                "page": metadata.get(
                    "page",
                    "Unknown",
                ),
                "score": match.score,
            }
        )

    return documents


# ============================================================
# Market Query Detection
# ============================================================

MARKET_KEYWORDS = {
    "price",
    "trend",
    "rsi",
    "ema",
    "sma",
    "fvg",
    "liquidity",
    "structure",
    "bos",
    "choch",
    "setup",
    "entry",
    "stop",
    "stoploss",
    "stop-loss",
    "target",
    "targets",
    "long",
    "short",
    "bullish",
    "bearish",
    "confluence",
    "market",
    "trade",
    "trading",
}


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


def is_market_query(question: str) -> bool:

    question_lower = question.lower()

    return any(
        keyword in question_lower
        for keyword in MARKET_KEYWORDS
    )


# ============================================================
# Symbol Extraction
# ============================================================

def extract_symbol(question: str) -> str | None:

    # Examples:
    # BTCUSDT
    # BTC/USDT
    # BTC-USDT
    # BTC USDT

    pair_match = re.search(
        r"\b([A-Z]{2,10})\s*(?:/|-|\s)?\s*(USDT|USD)\b",
        question.upper(),
    )

    if pair_match:

        base = pair_match.group(1)
        quote = pair_match.group(2)

        return f"{base}{quote}"

    # Common crypto tickers.
    common_symbols = {
        "BTC",
        "ETH",
        "SOL",
        "BNB",
        "XRP",
        "ADA",
        "DOGE",
        "AVAX",
        "DOT",
        "LINK",
        "LTC",
        "TRX",
        "SHIB",
        "ATOM",
        "UNI",
        "ETC",
        "FIL",
        "NEAR",
        "APT",
        "ARB",
        "OP",
    }

    words = re.findall(
        r"\b[A-Za-z]{2,10}\b",
        question,
    )

    for word in words:

        symbol = word.upper()

        if symbol in common_symbols:
            return f"{symbol}USDT"

    return None


# ============================================================
# Timeframe Extraction
# ============================================================

def extract_timeframe(question: str) -> str:

    # Keep the match case-sensitive because:
    #
    # 1m = one minute
    # 1M = one month
    #
    # The analysis pipeline currently uses Binance-style
    # intraday/day/week intervals.

    timeframe_match = re.search(
        r"\b(1m|3m|5m|15m|30m|1h|2h|4h|6h|8h|12h|1d|3d|1w)\b",
        question,
    )

    if timeframe_match:

        timeframe = timeframe_match.group(1)

        if timeframe in SUPPORTED_TIMEFRAMES:
            return timeframe

    return "15m"


# ============================================================
# Live Market Analysis
# ============================================================

def build_live_market_context(
    question: str,
) -> str:

    if not is_market_query(question):
        return "No live market analysis requested."

    symbol = extract_symbol(question)

    if not symbol:
        return (
            "Live market analysis was not requested with a "
            "specific cryptocurrency symbol."
        )

    timeframe = extract_timeframe(question)

    try:

        analysis = analyze_market(
            symbol=symbol,
            timeframe=timeframe,
            limit=500,
        )

    except Exception as error:

        return (
            "LIVE MARKET ANALYSIS UNAVAILABLE.\n"
            f"Symbol: {symbol}\n"
            f"Timeframe: {timeframe}\n"
            f"Reason: {str(error)}"
        )

    # analysis_service returns the deterministic market-analysis
    # dictionary generated by the existing analysis pipeline.

    market = analysis.get(
        "market",
        {},
    )

    indicators = analysis.get(
        "indicators",
        {},
    )

    structure = analysis.get(
        "structure",
        {},
    )

    fvg = analysis.get(
        "fvg",
        {},
    )

    liquidity = analysis.get(
        "liquidity",
        {},
    )

    confluence = analysis.get(
        "confluence",
        {},
    )

    setup = analysis.get(
        "setup",
        {},
    )

    swing = structure.get(
        "swing",
        {},
    )

    internal = structure.get(
        "internal",
        {},
    )

    lines = []

    lines.append(
        f"Symbol: {market.get('symbol', symbol)}"
    )

    lines.append(
        f"Timeframe: {market.get('timeframe', timeframe)}"
    )

    lines.append(
        f"Current Price: {market.get('current_price')}"
    )

    lines.append(
        f"Overall Trend: {analysis.get('trend')}"
    )

    lines.append("")

    lines.append("INDICATORS")

    lines.append(
        f"SMA 20: {indicators.get('sma_20')}"
    )

    lines.append(
        f"SMA 50: {indicators.get('sma_50')}"
    )

    lines.append(
        f"EMA 20: {indicators.get('ema_20')}"
    )

    lines.append(
        f"EMA 50: {indicators.get('ema_50')}"
    )

    lines.append(
        f"EMA 200: {indicators.get('ema_200')}"
    )

    lines.append(
        f"RSI 14: {indicators.get('rsi_14')}"
    )

    lines.append(
        f"RSI Condition: {analysis.get('rsi_condition')}"
    )

    lines.append("")

    lines.append("MARKET STRUCTURE")

    lines.append(
        f"Swing Trend: {swing.get('trend')}"
    )

    lines.append(
        f"Latest Swing Event: {swing.get('latest_event')}"
    )

    lines.append(
        f"Internal Trend: {internal.get('trend')}"
    )

    lines.append(
        f"Latest Internal Event: {internal.get('latest_event')}"
    )

    lines.append("")

    lines.append("FAIR VALUE GAPS")

    lines.append(
        f"Active FVG Count: {fvg.get('active_count')}"
    )

    zones = fvg.get(
        "zones",
        [],
    )

    for zone in zones[:5]:

        lines.append(
            "FVG: "
            f"{zone.get('type')} | "
            f"lower={zone.get('lower')} | "
            f"upper={zone.get('upper')} | "
            f"mitigated={zone.get('mitigated')} | "
            f"position={zone.get('position')}"
        )

    lines.append("")

    lines.append("LIQUIDITY")

    buy_side = liquidity.get(
        "buy_side_liquidity",
        [],
    )

    sell_side = liquidity.get(
        "sell_side_liquidity",
        [],
    )

    for level in buy_side[:5]:

        lines.append(
            "Buy-side liquidity: "
            f"price={level.get('price')} | "
            f"source={level.get('source')} | "
            f"touches={level.get('touches')}"
        )

    for level in sell_side[:5]:

        lines.append(
            "Sell-side liquidity: "
            f"price={level.get('price')} | "
            f"source={level.get('source')} | "
            f"touches={level.get('touches')}"
        )

    lines.append("")

    lines.append("CONFLUENCE")

    lines.append(
        f"Bias: {confluence.get('bias')}"
    )

    lines.append(
        f"Strength: {confluence.get('strength')}"
    )

    lines.append(
        f"Score: {confluence.get('score')}"
    )

    lines.append(
        f"Bullish Score: {confluence.get('bullish_score')}"
    )

    lines.append(
        f"Bearish Score: {confluence.get('bearish_score')}"
    )

    lines.append(
        f"Bullish Factors: "
        f"{confluence.get('bullish_factors')}"
    )

    lines.append(
        f"Bearish Factors: "
        f"{confluence.get('bearish_factors')}"
    )

    lines.append(
        f"Conflicting Factors: "
        f"{confluence.get('conflicting_factors')}"
    )

    lines.append("")

    lines.append("TRADE SETUP")

    lines.append(
        f"Setup: {setup.get('setup')}"
    )

    lines.append(
        f"Direction: {setup.get('direction')}"
    )

    lines.append(
        f"Confidence: {setup.get('confidence')}"
    )

    lines.append(
        f"Score: {setup.get('score')}"
    )

    lines.append(
        f"Entry Zone: {setup.get('entry_zone')}"
    )

    lines.append(
        f"Entry Source: {setup.get('entry_source')}"
    )

    lines.append(
        f"Stop Loss: {setup.get('stop_loss')}"
    )

    lines.append(
        f"Stop Source: {setup.get('stop_source')}"
    )

    lines.append(
        f"Targets: {setup.get('targets')}"
    )

    lines.append(
        f"Target Source: {setup.get('target_source')}"
    )

    lines.append(
        f"Risk: {setup.get('risk')}"
    )

    lines.append(
        f"Reward: {setup.get('reward')}"
    )

    lines.append(
        f"Risk/Reward: {setup.get('risk_reward')}"
    )

    lines.append(
        f"Reasons: {setup.get('reasons')}"
    )

    lines.append(
        f"Conflicts: {setup.get('conflicts')}"
    )

    lines.append(
        f"Invalidated If: {setup.get('invalidated_if')}"
    )

    return "\n".join(lines)


# ============================================================
# RAG Pipeline
# ============================================================

def ask_trade_copilot(
    question: str,
    conversation_id: str | None = None,
):

    # --------------------------------------------------------
    # Conversation history
    # --------------------------------------------------------

    if conversation_id:

        history = build_conversation_history(
            conversation_id
        )

    else:

        history = "No previous conversation."

    # --------------------------------------------------------
    # Static knowledge retrieval
    # --------------------------------------------------------

    documents = retrieve_documents(
        question
    )

    context_parts = []

    for i, document in enumerate(
        documents,
        start=1,
    ):

        context_parts.append(
            f"""
SOURCE {i}
File: {document['source']}
Page: {document['page']}

{document['text']}
"""
        )

    context = "\n".join(
        context_parts
    )

    if not context:
        context = "No relevant knowledge-base context found."

    # --------------------------------------------------------
    # Live market analysis
    # --------------------------------------------------------

    live_analysis = build_live_market_context(
        question
    )

    # --------------------------------------------------------
    # Gemini prompt
    # --------------------------------------------------------

    formatted_prompt = prompt.format(
        history=history,
        context=context,
        live_analysis=live_analysis,
        question=question,
    )

    # --------------------------------------------------------
    # Gemini
    # --------------------------------------------------------

    response = llm.invoke(
        formatted_prompt
    )

    answer = response.content

    if isinstance(answer, list):

        answer = "\n".join(
            item.get(
                "text",
                str(item),
            )
            if isinstance(item, dict)
            else str(item)
            for item in answer
        )

    return {
        "answer": answer,
        "sources": documents,
    }


# ============================================================
# Local Test
# ============================================================

if __name__ == "__main__":

    question = (
        "What is the current BTC price and trend?"
    )

    result = ask_trade_copilot(
        question
    )

    print(
        "\n================================"
    )
    print(
        "TRADE COPILOT"
    )
    print(
        "================================\n"
    )

    print(
        result["answer"]
    )

    print(
        "\n\nSOURCES"
    )
    print(
        "================================"
    )

    for source in result["sources"]:

        print(
            f"\n{source['source']}"
            f" — Page {source['page']}"
            f" — Score {source['score']}"
        )
