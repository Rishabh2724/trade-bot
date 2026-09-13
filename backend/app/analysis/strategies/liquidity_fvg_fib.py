from __future__ import annotations

from typing import Any

import pandas as pd

from app.analysis.indicators import calculate_atr
from app.analysis.fibonacci import (
    calculate_bullish_fib_zone,
    calculate_bearish_fib_zone,
    zones_overlap,
)
from app.analysis.displacement import (
    detect_displacement,
)
from app.analysis.patterns import detect_fvg
from app.analysis.liquidity import (
    detect_liquidity,
    detect_liquidity_sweeps,
)
from app.analysis.structure import (
    build_structure,
)


class LiquidityFvgFibStrategy:
    """
    V1:

        Liquidity Sweep
            +
        Displacement
            +
        FVG
            +
        Fibonacci 0.50-0.786 overlap
            =
        Reversal Setup

    This class is intentionally deterministic.
    """

    def __init__(
        self,
        swing_length: int = 5,
        internal_length: int = 5,
        liquidity_tolerance_percent: float = 0.10,
        fvg_min_gap_percent: float = 0.03,
        atr_period: int = 14,
        displacement_atr_multiplier: float = 1.5,
        fib_lower: float = 0.500,
        fib_upper: float = 0.786,
        stop_atr_buffer: float = 0.20,
        minimum_risk_reward: float = 1.5,
    ):
        self.swing_length = swing_length
        self.internal_length = internal_length
        self.liquidity_tolerance_percent = (
            liquidity_tolerance_percent
        )
        self.fvg_min_gap_percent = (
            fvg_min_gap_percent
        )
        self.atr_period = atr_period
        self.displacement_atr_multiplier = (
            displacement_atr_multiplier
        )
        self.fib_lower = fib_lower
        self.fib_upper = fib_upper
        self.stop_atr_buffer = stop_atr_buffer
        self.minimum_risk_reward = (
            minimum_risk_reward
        )

    def _find_fvg_after(
        self,
        fvgs: list[dict],
        index: int,
        direction: str,
    ) -> list[dict]:
        """
        Find FVGs formed on or after the sweep.
        """

        return [
            fvg
            for fvg in fvgs
            if (
                fvg["formation_index"] >= index
                and fvg["type"] == direction
                and not fvg.get(
                    "mitigated",
                    False,
                )
            )
        ]

    def _find_latest_fvg(
        self,
        fvgs: list[dict],
        direction: str,
        max_index: int,
    ) -> dict | None:

        candidates = [
            fvg
            for fvg in fvgs
            if (
                fvg["formation_index"]
                <= max_index
                and fvg["type"] == direction
            )
        ]

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: x[
                "formation_index"
            ],
            reverse=True,
        )

        return candidates[0]

    def _find_swing_range(
        self,
        structure: dict,
        direction: str,
        current_index: int,
    ) -> tuple[dict, dict] | None:
        """
        Find the most recent confirmed swing
        pair available before the current event.

        For bullish:
            low → high

        For bearish:
            high → low
        """

        pivots = structure[
            "swing"
        ][
            "pivots"
        ]

        confirmed = [
            pivot
            for pivot in pivots
            if pivot["index"] < current_index
        ]

        if len(confirmed) < 2:
            return None

        highs = [
            p
            for p in confirmed
            if p["type"] == "high"
        ]

        lows = [
            p
            for p in confirmed
            if p["type"] == "low"
        ]

        if not highs or not lows:
            return None

        latest_high = highs[-1]
        latest_low = lows[-1]

        if direction == "bullish":

            if latest_low["index"] >= latest_high["index"]:
                return None

            return (
                latest_low,
                latest_high,
            )

        if direction == "bearish":

            if latest_high["index"] >= latest_low["index"]:
                return None

            return (
                latest_high,
                latest_low,
            )

        return None

    def _build_long_setup(
        self,
        df: pd.DataFrame,
        sweep: dict,
        displacement: dict,
        fvg: dict,
        fib_zone: dict,
        overlap: dict,
        target_liquidity: list[dict],
    ) -> dict | None:

        atr = float(
            displacement["atr"]
        )

        sweep_low = float(
            sweep["sweep_price"]
        )

        entry_low = float(
            overlap["lower"]
        )

        entry_high = float(
            overlap["upper"]
        )

        stop_loss = (
            sweep_low
            - atr * self.stop_atr_buffer
        )

        valid_targets = [
            level
            for level in target_liquidity
            if float(level["price"])
            > entry_high
        ]

        if not valid_targets:
            return None

        valid_targets.sort(
            key=lambda x: float(
                x["price"]
            )
        )

        target = float(
            valid_targets[0]["price"]
        )

        risk = (
            entry_low - stop_loss
        )

        reward = (
            target - entry_high
        )

        if risk <= 0 or reward <= 0:
            return None

        risk_reward = reward / risk

        if (
            risk_reward
            < self.minimum_risk_reward
        ):
            return None

        return {
            "setup": "LONG",
            "direction": "bullish",

            "sweep": sweep,
            "displacement": displacement,

            "fvg": fvg,

            "fib_zone": fib_zone,
            "overlap_zone": overlap,

            "entry_zone": [
                entry_low,
                entry_high,
            ],

            "stop_loss": stop_loss,
            "target": target,

            "risk": risk,
            "reward": reward,
            "risk_reward": risk_reward,

            "target_source": target,
        }

    def _build_short_setup(
        self,
        df: pd.DataFrame,
        sweep: dict,
        displacement: dict,
        fvg: dict,
        fib_zone: dict,
        overlap: dict,
        target_liquidity: list[dict],
    ) -> dict | None:

        atr = float(
            displacement["atr"]
        )

        sweep_high = float(
            sweep["sweep_price"]
        )

        entry_low = float(
            overlap["lower"]
        )

        entry_high = float(
            overlap["upper"]
        )

        stop_loss = (
            sweep_high
            + atr * self.stop_atr_buffer
        )

        valid_targets = [
            level
            for level in target_liquidity
            if float(level["price"])
            < entry_low
        ]

        if not valid_targets:
            return None

        valid_targets.sort(
            key=lambda x: float(
                x["price"],
                )
        )

        target = float(
            valid_targets[0]["price"]
        )

        risk = (
            stop_loss - entry_high
        )

        reward = (
            entry_low - target
        )

        if risk <= 0 or reward <= 0:
            return None

        risk_reward = reward / risk

        if (
            risk_reward
            < self.minimum_risk_reward
        ):
            return None

        return {
            "setup": "SHORT",
            "direction": "bearish",

            "sweep": sweep,
            "displacement": displacement,

            "fvg": fvg,

            "fib_zone": fib_zone,
            "overlap_zone": overlap,

            "entry_zone": [
                entry_low,
                entry_high,
            ],

            "stop_loss": stop_loss,
            "target": target,

            "risk": risk,
            "reward": reward,
            "risk_reward": risk_reward,

            "target_source": target,
        }

    def generate_setups(
        self,
        df: pd.DataFrame,
    ) -> list[dict]:
        """
        Generate historical strategy setups.

        NOTE:
        This first version is primarily the detector.
        The production backtester must process candles
        chronologically and prevent future-data leakage.
        """

        if df.empty:
            return []

        structure = build_structure(
            df,
            swing_length=self.swing_length,
            internal_length=self.internal_length,
        )

        liquidity = detect_liquidity(
            df,
            swing_length=self.swing_length,
            tolerance_percent=(
                self.liquidity_tolerance_percent
            ),
        )

        sweeps = detect_liquidity_sweeps(
            df,
            liquidity,
            reclaim_required=True,
        )

        fvgs = detect_fvg(
            df,
            min_gap_percent=(
                self.fvg_min_gap_percent
            ),
        )

        displacements = detect_displacement(
            df,
            atr_period=self.atr_period,
            atr_multiplier=(
                self.displacement_atr_multiplier
            ),
        )

        displacement_by_index = {
            item["index"]: item
            for item in displacements
        }

        setups = []

        for sweep in sweeps:

            sweep_index = sweep["index"]

            direction = sweep[
                "direction"
            ]

            # ----------------------------------
            # Find displacement after sweep
            # ----------------------------------

            displacement = None

            for index in range(
                sweep_index + 1,
                len(df),
            ):

                candidate = (
                    displacement_by_index.get(
                        index
                    )
                )

                if not candidate:
                    continue

                if (
                    candidate["direction"]
                    != direction
                ):
                    continue

                displacement = candidate

                break

            if displacement is None:
                continue

            displacement_index = (
                displacement["index"]
            )

            # ----------------------------------
            # Find FVG created by displacement
            # ----------------------------------

            candidate_fvgs = [
                fvg
                for fvg in fvgs
                if (
                    fvg[
                        "formation_index"
                    ]
                    >= displacement_index
                    and
                    fvg["type"]
                    == direction
                )
            ]

            if not candidate_fvgs:
                continue

            fvg = candidate_fvgs[0]

            # ----------------------------------
            # Fibonacci swing
            # ----------------------------------

            swing_range = (
                self._find_swing_range(
                    structure,
                    direction,
                    sweep_index,
                )
            )

            if swing_range is None:
                continue

            first_swing, second_swing = (
                swing_range
            )

            if direction == "bullish":

                swing_low = float(
                    first_swing["price"]
                )

                swing_high = float(
                    second_swing["price"]
                )

                fib_zone = (
                    calculate_bullish_fib_zone(
                        swing_low,
                        swing_high,
                        self.fib_lower,
                        self.fib_upper,
                    )
                )

            else:

                swing_high = float(
                    first_swing["price"]
                )

                swing_low = float(
                    second_swing["price"]
                )

                fib_zone = (
                    calculate_bearish_fib_zone(
                        swing_high,
                        swing_low,
                        self.fib_lower,
                        self.fib_upper,
                    )
                )

            # ----------------------------------
            # FVG zone
            # ----------------------------------

            fvg_zone = {
                "lower": float(
                    fvg["lower"]
                ),
                "upper": float(
                    fvg["upper"]
                ),
                "type": fvg["type"],
            }

            overlap = zones_overlap(
                fib_zone,
                fvg_zone,
            )

            if overlap is None:
                continue

            # ----------------------------------
            # Targets
            # ----------------------------------

            if direction == "bullish":

                target_liquidity = (
                    liquidity[
                        "buy_side_liquidity"
                    ]
                )

                setup = (
                    self._build_long_setup(
                        df,
                        sweep,
                        displacement,
                        fvg,
                        fib_zone,
                        overlap,
                        target_liquidity,
                    )
                )

            else:

                target_liquidity = (
                    liquidity[
                        "sell_side_liquidity"
                    ]
                )

                setup = (
                    self._build_short_setup(
                        df,
                        sweep,
                        displacement,
                        fvg,
                        fib_zone,
                        overlap,
                        target_liquidity,
                    )
                )

            if setup is None:
                continue

            setup["index"] = sweep_index

            setup["timestamp"] = str(
                df.iloc[sweep_index][
                    "timestamp"
                ]
            )

            setups.append(setup)

        return setups