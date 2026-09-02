import httpx


BASE_URL = "https://api.coingecko.com/api/v3"


# ---------------------------------------
# Symbol → CoinGecko ID
# ---------------------------------------

COIN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "DOT": "polkadot",
}


# ---------------------------------------
# Current Price
# ---------------------------------------

async def get_crypto_price(
    symbol: str,
    currency: str = "usd",
):
    symbol = symbol.upper()

    if currency.lower() != "usd":
        raise ValueError(
            f"Unsupported currency: {currency}. Only usd is supported."
        )

    if symbol not in COIN_IDS:
        raise ValueError(
            f"Unsupported cryptocurrency: {symbol}"
        )

    pair = f"{symbol}USDT"
    binance_url = "https://api.binance.com/api/v3/ticker/24hr"

    async with httpx.AsyncClient(
        timeout=10,
        trust_env=False,
    ) as client:
        response = await client.get(
            binance_url,
            params={"symbol": pair},
        )

        if response.status_code == 400:
            raise ValueError(
                f"Unsupported cryptocurrency: {symbol}"
            )

        response.raise_for_status()
        data = response.json()

    return {
        "symbol": symbol,
        "currency": currency,
        "price": float(data.get("lastPrice")),
        "change_24h": float(data.get("priceChangePercent", 0.0)),
        "volume_24h": float(data.get("quoteVolume", 0.0)),
        "market_cap": None,
    }


# ---------------------------------------
# Market Chart
# ---------------------------------------

async def get_crypto_market_data(
    symbol: str,
    days: int = 7,
):
    symbol = symbol.upper()

    coin_id = COIN_IDS.get(symbol)

    if not coin_id:
        raise ValueError(
            f"Unsupported cryptocurrency: {symbol}"
        )

    url = (
        f"{BASE_URL}/coins/"
        f"{coin_id}/market_chart"
    )

    params = {
        "vs_currency": "usd",
        "days": days,
    }

    async with httpx.AsyncClient(
        timeout=10,
        trust_env=False,
    ) as client:

        response = await client.get(
            url,
            params=params,
        )

        response.raise_for_status()

        data = response.json()

    return {
        "symbol": symbol,
        "prices": data.get(
            "prices",
            []
        ),
        "market_caps": data.get(
            "market_caps",
            []
        ),
        "volumes": data.get(
            "total_volumes",
            []
        ),
    }