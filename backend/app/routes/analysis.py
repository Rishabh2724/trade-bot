import re

from fastapi import APIRouter, HTTPException, Query

from app.analysis.market_analysis import SUPPORTED_TIMEFRAMES
from app.schemas.analysis import MarketAnalysisResponse
from app.schemas.common import (
    RESPONSE_400,
    RESPONSE_404,
    RESPONSE_500,
    RESPONSE_502,
)
from app.services.analysis_service import analyze_market


router = APIRouter(
    prefix="/api/analysis",
    tags=["Analysis"],
)


# Binance spot symbols are uppercase alphanumeric, e.g. BTCUSDT.
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


def _normalize_symbol(symbol: str) -> str:

    cleaned = (
        symbol.replace("/", "")
        .replace("-", "")
        .replace(" ", "")
        .upper()
    )

    if not SYMBOL_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid symbol: {symbol!r}. Expected a Binance pair "
                "such as BTCUSDT."
            ),
        )

    return cleaned


@router.get(
    "/{symbol}",
    response_model=MarketAnalysisResponse,
    summary="Deterministic technical / SMC analysis for a symbol",
    responses={
        400: RESPONSE_400,
        404: RESPONSE_404,
        502: RESPONSE_502,
        500: RESPONSE_500,
    },
)
def analyze_crypto(
    symbol: str,
    timeframe: str = Query(
        default="15m",
        description="Binance candle interval, e.g. 15m, 1h, 4h, 1d.",
    ),
    limit: int = Query(
        default=500,
        ge=200,
        le=1000,
        description="Number of candles (200-1000).",
    ),
):
    symbol = _normalize_symbol(symbol)

    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported timeframe: {timeframe}. "
                f"Supported: {', '.join(sorted(SUPPORTED_TIMEFRAMES))}."
            ),
        )

    try:
        return analyze_market(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

    except ValueError as error:
        # Unknown symbol / insufficient data / bad input.
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except RuntimeError as error:
        # Upstream Binance failure.
        raise HTTPException(
            status_code=502,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(error)}",
        )
