from fastapi import APIRouter, HTTPException, Query

from app.schemas.analysis import MarketAnalysisResponse
from app.services.analysis_service import analyze_market


router = APIRouter(
    prefix="/api/analysis",
    tags=["Analysis"],
)


VALID_TIMEFRAMES = {
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
    "1M",
}


@router.get(
    "/{symbol}",
    response_model=MarketAnalysisResponse,
)
def analyze_crypto(
    symbol: str,
    timeframe: str = Query(
        default="15m",
        description="Binance candle interval",
    ),
    limit: int = Query(
        default=500,
        ge=200,
        le=1000,
        description="Number of candles",
    ),
):
    symbol = symbol.replace("/", "").upper()

    if timeframe not in VALID_TIMEFRAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported timeframe: {timeframe}",
        )

    try:
        return analyze_market(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(error)}",
        )