from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

import pandas as pd


@dataclass
class Trade:
    entry_time: str
    exit_time: str

    direction: str

    entry_price: float
    stop_loss: float
    target: float
    exit_price: float

    risk: float
    reward: float

    risk_reward: float
    pnl_r: float

    result: str

    setup_index: int
    exit_index: int


class BacktestEngine:
    """
    Simple candle-by-candle backtesting engine.

    Important:
    - Entry happens after the setup is confirmed.
    - SL/TP are evaluated candle by candle.
    - No future candle is used to create a trade.
    """

    def __init__(
        self,
        initial_capital: float = 10_000.0,
        risk_per_trade: float = 0.01,
        fee_percent: float = 0.0,
        slippage_percent: float = 0.0,
    ):
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.fee_percent = fee_percent
        self.slippage_percent = slippage_percent

    # ============================================================
    # ENTRY
    # ============================================================

    def _apply_entry_slippage(
        self,
        price: float,
        direction: str,
    ) -> float:

        slippage = (
            price
            * self.slippage_percent
            / 100
        )

        if direction == "LONG":
            return price + slippage

        return price - slippage

    # ============================================================
    # EXIT
    # ============================================================

    def _apply_exit_slippage(
        self,
        price: float,
        direction: str,
    ) -> float:

        slippage = (
            price
            * self.slippage_percent
            / 100
        )

        if direction == "LONG":
            return price - slippage

        return price + slippage

    # ============================================================
    # FIND EXIT
    # ============================================================

    def _find_exit(
        self,
        df: pd.DataFrame,
        start_index: int,
        direction: str,
        entry_price: float,
        stop_loss: float,
        target: float,
    ) -> Optional[dict]:

        for i in range(
            start_index,
            len(df),
        ):

            candle = df.iloc[i]

            high = float(candle["high"])
            low = float(candle["low"])

            # ----------------------------------------------------
            # LONG
            # ----------------------------------------------------

            if direction == "LONG":

                hit_sl = low <= stop_loss
                hit_tp = high >= target

                if hit_sl and hit_tp:
                    """
                    Both levels were touched in the same candle.

                    Without lower timeframe data we cannot know
                    which happened first.

                    Conservative assumption:
                    SL gets hit first.
                    """

                    exit_price = (
                        self._apply_exit_slippage(
                            stop_loss,
                            direction,
                        )
                    )

                    return {
                        "exit_index": i,
                        "exit_price": exit_price,
                        "result": "LOSS",
                    }

                if hit_sl:

                    exit_price = (
                        self._apply_exit_slippage(
                            stop_loss,
                            direction,
                        )
                    )

                    return {
                        "exit_index": i,
                        "exit_price": exit_price,
                        "result": "LOSS",
                    }

                if hit_tp:

                    exit_price = (
                        self._apply_exit_slippage(
                            target,
                            direction,
                        )
                    )

                    return {
                        "exit_index": i,
                        "exit_price": exit_price,
                        "result": "WIN",
                    }

            # ----------------------------------------------------
            # SHORT
            # ----------------------------------------------------

            else:

                hit_sl = high >= stop_loss
                hit_tp = low <= target

                if hit_sl and hit_tp:

                    exit_price = (
                        self._apply_exit_slippage(
                            stop_loss,
                            direction,
                        )
                    )

                    return {
                        "exit_index": i,
                        "exit_price": exit_price,
                        "result": "LOSS",
                    }

                if hit_sl:

                    exit_price = (
                        self._apply_exit_slippage(
                            stop_loss,
                            direction,
                        )
                    )

                    return {
                        "exit_index": i,
                        "exit_price": exit_price,
                        "result": "LOSS",
                    }

                if hit_tp:

                    exit_price = (
                        self._apply_exit_slippage(
                            target,
                            direction,
                        )
                    )

                    return {
                        "exit_index": i,
                        "exit_price": exit_price,
                        "result": "WIN",
                    }

        # --------------------------------------------------------
        # Neither SL nor TP was reached.
        # --------------------------------------------------------

        return None

    # ============================================================
    # R MULTIPLE
    # ============================================================

    @staticmethod
    def _calculate_r_multiple(
        direction: str,
        entry_price: float,
        exit_price: float,
        stop_loss: float,
    ) -> float:

        if direction == "LONG":

            risk = (
                entry_price
                - stop_loss
            )

            pnl = (
                exit_price
                - entry_price
            )

        else:

            risk = (
                stop_loss
                - entry_price
            )

            pnl = (
                entry_price
                - exit_price
            )

        if risk <= 0:
            return 0.0

        return pnl / risk

    # ============================================================
    # RUN
    # ============================================================

    def run(
        self,
        df: pd.DataFrame,
        setups: list[dict],
    ) -> dict:

        if df.empty:
            return {
                "trades": [],
                "metrics": self._empty_metrics(),
            }

        trades = []

        capital = self.initial_capital

        # Prevent overlapping trades.
        next_available_index = 0

        for setup in setups:

            setup_index = int(
                setup["index"]
            )

            if setup_index < next_available_index:
                continue

            direction = setup[
                "setup"
            ]

            entry_zone = setup[
                "entry_zone"
            ]

            stop_loss = float(
                setup["stop_loss"]
            )

            target = float(
                setup["target"]
            )

            # ----------------------------------------------------
            # Entry
            #
            # We don't enter merely because the FVG exists.
            #
            # We wait for price to enter the overlap zone.
            # ----------------------------------------------------

            entry_index = None
            entry_price = None

            for i in range(
                setup_index + 1,
                len(df),
            ):

                candle = df.iloc[i]

                high = float(
                    candle["high"]
                )

                low = float(
                    candle["low"]
                )

                zone_low = float(
                    entry_zone[0]
                )

                zone_high = float(
                    entry_zone[1]
                )

                touched = (
                    low <= zone_high
                    and high >= zone_low
                )

                if not touched:
                    continue

                # Use midpoint of the overlap zone
                # as the simulated limit entry.
                entry_price = (
                    zone_low + zone_high
                ) / 2

                entry_price = (
                    self._apply_entry_slippage(
                        entry_price,
                        direction,
                    )
                )

                entry_index = i

                break

            if entry_index is None:
                continue

            # ----------------------------------------------------
            # Validate entry
            # ----------------------------------------------------

            if direction == "LONG":

                if entry_price <= stop_loss:
                    continue

                if entry_price >= target:
                    continue

            else:

                if entry_price >= stop_loss:
                    continue

                if entry_price <= target:
                    continue

            # ----------------------------------------------------
            # Risk
            # ----------------------------------------------------

            if direction == "LONG":

                risk_per_unit = (
                    entry_price
                    - stop_loss
                )

            else:

                risk_per_unit = (
                    stop_loss
                    - entry_price
                )

            if risk_per_unit <= 0:
                continue

            # ----------------------------------------------------
            # Position size
            # ----------------------------------------------------

            capital_at_risk = (
                capital
                * self.risk_per_trade
            )

            quantity = (
                capital_at_risk
                / risk_per_unit
            )

            # ----------------------------------------------------
            # Find exit
            # ----------------------------------------------------

            exit_data = self._find_exit(
                df=df,
                start_index=entry_index,
                direction=direction,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
            )

            if exit_data is None:
                continue

            exit_index = exit_data[
                "exit_index"
            ]

            exit_price = float(
                exit_data["exit_price"]
            )

            result = exit_data[
                "result"
            ]

            pnl_per_unit = (
                exit_price - entry_price
                if direction == "LONG"
                else entry_price - exit_price
            )

            gross_pnl = (
                pnl_per_unit
                * quantity
            )

            # ----------------------------------------------------
            # Fees
            # ----------------------------------------------------

            entry_value = (
                entry_price * quantity
            )

            exit_value = (
                exit_price * quantity
            )

            fees = (
                entry_value
                + exit_value
            ) * (
                self.fee_percent / 100
            )

            net_pnl = (
                gross_pnl - fees
            )

            # ----------------------------------------------------
            # R multiple
            # ----------------------------------------------------

            pnl_r = (
                net_pnl
                / capital_at_risk
                if capital_at_risk > 0
                else 0.0
            )

            risk = (
                abs(
                    entry_price
                    - stop_loss
                )
            )

            reward = (
                abs(
                    target
                    - entry_price
                )
            )

            risk_reward = (
                reward / risk
                if risk > 0
                else 0.0
            )

            # ----------------------------------------------------
            # Update capital
            # ----------------------------------------------------

            capital += net_pnl

            trade = Trade(
                entry_time=str(
                    df.iloc[entry_index][
                        "timestamp"
                    ]
                ),
                exit_time=str(
                    df.iloc[exit_index][
                        "timestamp"
                    ]
                ),

                direction=direction,

                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                exit_price=exit_price,

                risk=risk,
                reward=reward,

                risk_reward=risk_reward,
                pnl_r=pnl_r,

                result=result,

                setup_index=setup_index,
                exit_index=exit_index,
            )

            trades.append(
                trade
            )

            # ----------------------------------------------------
            # Don't allow overlapping positions.
            # ----------------------------------------------------

            next_available_index = (
                exit_index + 1
            )

        metrics = self._calculate_metrics(
            trades
        )

        metrics["final_capital"] = capital
        metrics["total_return_percent"] = (
            (
                capital
                - self.initial_capital
            )
            / self.initial_capital
        ) * 100

        return {
            "trades": [
                asdict(trade)
                for trade in trades
            ],
            "metrics": metrics,
        }

    # ============================================================
    # METRICS
    # ============================================================

    def _calculate_metrics(
        self,
        trades: list[Trade],
    ) -> dict:

        if not trades:
            return self._empty_metrics()

        pnl_values = [
            trade.pnl_r
            for trade in trades
        ]

        wins = [
            trade
            for trade in trades
            if trade.pnl_r > 0
        ]

        losses = [
            trade
            for trade in trades
            if trade.pnl_r <= 0
        ]

        gross_profit = sum(
            trade.pnl_r
            for trade in wins
        )

        gross_loss = abs(
            sum(
                trade.pnl_r
                for trade in losses
            )
        )

        if gross_loss > 0:
            profit_factor = (
                gross_profit
                / gross_loss
            )
        else:
            profit_factor = float("inf")

        win_rate = (
            len(wins)
            / len(trades)
        ) * 100

        average_r = (
            sum(pnl_values)
            / len(pnl_values)
        )

        # --------------------------------------------------------
        # Max drawdown in R
        # --------------------------------------------------------

        equity = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for pnl in pnl_values:

            equity += pnl

            peak = max(
                peak,
                equity,
            )

            drawdown = (
                peak - equity
            )

            max_drawdown = max(
                max_drawdown,
                drawdown,
            )

        return {
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),

            "win_rate": win_rate,

            "profit_factor": (
                profit_factor
            ),

            "average_r": average_r,

            "total_r": sum(
                pnl_values
            ),

            "max_drawdown_r": (
                max_drawdown
            ),

            "largest_win_r": max(
                pnl_values
            ),

            "largest_loss_r": min(
                pnl_values
            ),
        }

    @staticmethod
    def _empty_metrics() -> dict:

        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,

            "win_rate": 0.0,

            "profit_factor": 0.0,

            "average_r": 0.0,
            "total_r": 0.0,

            "max_drawdown_r": 0.0,

            "largest_win_r": 0.0,
            "largest_loss_r": 0.0,

            "final_capital": 0.0,
            "total_return_percent": 0.0,
        }