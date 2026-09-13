import pandas as pd


def calculate_sma(
    prices: list[float],
    period: int = 20,
):
    series = pd.Series(prices)

    sma = series.rolling(
        window=period
    ).mean()

    return sma.iloc[-1]


def calculate_ema(
    prices: list[float],
    period: int = 20,
):
    series = pd.Series(prices)

    ema = series.ewm(
        span=period,
        adjust=False,
    ).mean()

    return ema.iloc[-1]


def calculate_rsi(
    prices: list[float],
    period: int = 14,
):
    series = pd.Series(prices)

    delta = series.diff()

    gains = delta.clip(
        lower=0
    )

    losses = -delta.clip(
        upper=0
    )

    average_gain = gains.ewm(
        alpha=1 / period,
        adjust=False,
    ).mean()

    average_loss = losses.ewm(
        alpha=1 / period,
        adjust=False,
    ).mean()

    rs = average_gain / average_loss

    rsi = 100 - (
        100 / (1 + rs)
    )

    # A flat stretch makes both averages 0, so rs is 0/0 = NaN and the RSI
    # comes out NaN. FastAPI would serialize that as bare NaN, which is not
    # valid JSON and breaks every client. 50 is the neutral convention.
    rsi = rsi.fillna(50)

    return rsi.iloc[-1]



def calculate_atr(
    df: pd.DataFrame,
    period: int = 14,
) -> pd.Series:
    """
    Calculate Average True Range (ATR).

    Uses Wilder's smoothing through pandas' EWM.

    ATR is used for:
    - displacement detection
    - volatility normalization
    - stop-loss buffers
    """

    required = {"high", "low", "close"}

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = (
        true_range
        .ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period,
        )
        .mean()
    )

    return atr

def analyze_prices(
    prices: list[float],
):
    if len(prices) < 200:
        raise ValueError(
            "At least 200 price points are required."
        )

    return {
        "current_price": prices[-1],

        "sma_20": calculate_sma(
            prices,
            20,
        ),

        "sma_50": calculate_sma(
            prices,
            50,
        ),

        "ema_20": calculate_ema(
            prices,
            20,
        ),

        "ema_50": calculate_ema(
            prices,
            50,
        ),

        "ema_200": calculate_ema(
            prices,
            200,
        ),

        "rsi_14": calculate_rsi(
            prices,
            14,
        ),
    }
if __name__ == "__main__":
    import random

    prices = [50000 + random.uniform(-500, 500) for _ in range(250)]

    result = analyze_prices(prices)

    print("\nTECHNICAL ANALYSIS")
    print("==================")

    for key, value in result.items():
        print(f"{key}: {value}")