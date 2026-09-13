import pandas as pd

from app.analysis.strategies.liquidity_fvg_fib import (
    LiquidityFvgFibStrategy,
)


def create_test_data():

    data = []

    price = 100.0

    for i in range(300):

        open_price = price

        high = price + 1.0
        low = price - 1.0
        close = price + 0.2

        data.append(
            {
                "timestamp": pd.Timestamp(
                    "2025-01-01"
                ) + pd.Timedelta(
                    minutes=15 * i
                ),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": 1000,
            }
        )

        price = close

    return pd.DataFrame(data)


def test_strategy_does_not_crash():

    df = create_test_data()

    strategy = LiquidityFvgFibStrategy()

    setups = strategy.generate_setups(df)

    assert isinstance(
        setups,
        list,
    )