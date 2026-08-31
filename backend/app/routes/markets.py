from fastapi import APIRouter, HTTPException

from app.market.coingecko import (
    get_crypto_price,
    get_crypto_market_data,
)


router = APIRouter(
    prefix="/api/market",
    tags=["Market"],
)


@router.get("/{symbol}/price")
async def crypto_price(symbol: str):

    try:

        return await get_crypto_price(
            symbol
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception:

        raise HTTPException(
            status_code=502,
            detail="Market data provider failed",
        )


@router.get("/{symbol}/chart")
async def crypto_chart(
    symbol: str,
    days: int = 7,
):

    if days < 1 or days > 365:
        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 365",
        )

    try:

        return await get_crypto_market_data(
            symbol,
            days,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception:

        raise HTTPException(
            status_code=502,
            detail="Market data provider failed",
        )