from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------
# Basic market information
# ---------------------------------------

class MarketInfo(BaseModel):

    symbol: str
    timeframe: str
    current_price: float


# ---------------------------------------
# Indicators
# ---------------------------------------

class Indicators(BaseModel):

    sma_20: float
    sma_50: float
    ema_20: float
    ema_50: float
    ema_200: float
    rsi_14: float


# ---------------------------------------
# FVG
# ---------------------------------------

class FVGZone(BaseModel):

    type: Literal["bullish", "bearish"]

    timestamp: str | None = None

    lower: float
    upper: float

    size: float
    size_percent: float

    formation_index: int | None = None

    mitigated: bool = False

    position: str | None = None
    distance: float | None = None
    distance_percent: float | None = None


class FVGAnalysis(BaseModel):

    active_count: int
    zones: list[FVGZone]


# ---------------------------------------
# Liquidity
# ---------------------------------------

class LiquidityLevel(BaseModel):

    type: Literal["buy_side", "sell_side"]

    price: float
    source: str
    touches: int


class LiquidityAnalysis(BaseModel):

    equal_highs: list[dict[str, Any]] = Field(
        default_factory=list
    )

    equal_lows: list[dict[str, Any]] = Field(
        default_factory=list
    )

    buy_side_liquidity: list[LiquidityLevel] = Field(
        default_factory=list
    )

    sell_side_liquidity: list[LiquidityLevel] = Field(
        default_factory=list
    )


# ---------------------------------------
# Structure
# ---------------------------------------

class StructureEvent(BaseModel):

    event: Literal["BOS", "CHoCH"]

    direction: Literal["bullish", "bearish"]

    level: float

    pivot_index: int | None = None
    break_index: int | None = None

    pivot_timestamp: str | None = None
    break_timestamp: str | None = None


class StructurePivot(BaseModel):

    index: int
    timestamp: str | None = None

    price: float

    type: Literal["high", "low"]

    label: Literal["HH", "HL", "LH", "LL"] | None = None


class StructureLayer(BaseModel):

    # "neutral" is a real fourth state: no structure break has happened yet
    # (or there are no confirmed pivots). It is distinct from "mixed", which
    # means the swing and internal layers conflict.
    trend: Literal[
        "bullish",
        "bearish",
        "mixed",
        "neutral",
    ]

    latest_event: StructureEvent | None = None

    events: list[StructureEvent] = Field(
        default_factory=list
    )

    pivots: list[StructurePivot] = Field(
        default_factory=list
    )


class StructureAnalysis(BaseModel):

    swing: StructureLayer

    internal: StructureLayer


# ---------------------------------------
# Confluence
# ---------------------------------------

class Confluence(BaseModel):

    bias: Literal[
        "bullish",
        "bearish",
        "mixed",
    ]

    strength: Literal[
        "weak",
        "moderate",
        "strong",
    ]

    score: int

    bullish_score: int
    bearish_score: int

    bullish_factors: list[str] = Field(
        default_factory=list
    )

    bearish_factors: list[str] = Field(
        default_factory=list
    )

    conflicting_factors: list[str] = Field(
        default_factory=list
    )

    latest_swing_event: StructureEvent | None = None

    latest_internal_event: StructureEvent | None = None

    bullish_fvg: FVGZone | None = None
    bearish_fvg: FVGZone | None = None

    selected_fvg: FVGZone | None = None

    nearby_fvgs: list[FVGZone] = Field(
        default_factory=list
    )

    nearest_buy_side_liquidity: LiquidityLevel | None = None

    nearest_sell_side_liquidity: LiquidityLevel | None = None

    reasons: list[str] = Field(
        default_factory=list
    )


# ---------------------------------------
# Trade setup
# ---------------------------------------

class TradeSetup(BaseModel):

    setup: Literal[
        "LONG",
        "SHORT",
        "NO_SETUP",
    ]

    direction: Literal[
        "bullish",
        "bearish",
    ] | None = None

    confidence: Literal[
        "low",
        "moderate",
        "high",
    ]

    score: int

    entry_zone: list[float] | None = None

    entry_source: str | None = None

    stop_loss: float | None = None

    stop_source: str | None = None

    targets: list[float] = Field(
        default_factory=list
    )

    target_source: str | None = None

    risk: float | None = None

    reward: float | None = None

    risk_reward: float | None = None

    reasons: list[str] = Field(
        default_factory=list
    )

    conflicts: list[str] = Field(
        default_factory=list
    )

    invalidated_if: str | None = None


# ---------------------------------------
# Complete analysis response
# ---------------------------------------

class MarketAnalysisResponse(BaseModel):

    market: MarketInfo

    trend: Literal[
        "bullish",
        "bearish",
        "mixed",
    ]

    indicators: Indicators

    rsi_condition: Literal[
        "overbought",
        "oversold",
        "neutral",
    ]

    structure: StructureAnalysis

    fvg: FVGAnalysis

    liquidity: LiquidityAnalysis

    confluence: Confluence

    setup: TradeSetup
