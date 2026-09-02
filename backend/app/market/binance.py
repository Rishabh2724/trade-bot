import requests
import pandas as pd


BASE_URL = "https://api.binance.com"


# ---------------------------------------
# Binance OHLCV
# ---------------------------------------

def get_ohlcv(
    symbol: str = "BTCUSDT",
    interval: str = "15m",
    limit: int = 500,
) -> pd.DataFrame:

    symbol = symbol.upper()

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }

    try:
        response = requests.get(
            f"{BASE_URL}/api/v3/klines",
            params=params,
            timeout=10,
        )

    except requests.RequestException as error:
        raise RuntimeError(
            f"Binance market data request failed: {error}"
        ) from error

    # Binance returns HTTP 400 with a coded body for bad input
    # (e.g. -1121 "Invalid symbol", -1120 "Invalid interval").
    # Surface these as ValueError so the API layer maps them to 400
    # instead of treating them as an upstream (502) failure.
    if response.status_code == 400:
        try:
            error_body = response.json()
        except ValueError:
            error_body = {}

        message = error_body.get("msg", "Invalid request")

        raise ValueError(
            f"{message} (symbol={symbol}, interval={interval})"
        )

    try:
        response.raise_for_status()

    except requests.RequestException as error:
        raise RuntimeError(
            f"Binance market data request failed: {error}"
        ) from error

    data = response.json()

    if not data:
        raise ValueError(
            f"No OHLCV data returned for {symbol}"
        )

    columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trades",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
        "ignore",
    ]

    df = pd.DataFrame(
        data,
        columns=columns,
    )

    # -----------------------------------
    # Convert numeric columns
    # -----------------------------------

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # -----------------------------------
    # Timestamp
    # -----------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="ms",
        utc=True,
    )

    df["close_time"] = pd.to_datetime(
        df["close_time"],
        unit="ms",
        utc=True,
    )

    return df