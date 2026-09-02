// Typed client for the TradeCopilot FastAPI backend.
// Types mirror backend/app/schemas/chat.py and backend/app/schemas/analysis.py.

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// ---------------------------------------
// Chat types
// ---------------------------------------

export type Role = "user" | "assistant";

export interface ChatSource {
  text: string;
  source: string;
  page: number | string | null;
  score: number | null;
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  sources: ChatSource[];
}

export interface ChatMessage {
  role: Role;
  content: string;
  created_at: string | null;
}

export interface ConversationHistoryResponse {
  conversation_id: string;
  message_count: number;
  messages: ChatMessage[];
}

// Error body from the backend (schemas/common.py ErrorResponse).
export class ApiError extends Error {
  status: number;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
  }
}

// ---------------------------------------
// Analysis types
// ---------------------------------------
// Mirrors backend/app/schemas/analysis.py.

export type Bias = "bullish" | "bearish" | "mixed";

/**
 * Structure layers have a fourth state the top-level trend does not: no
 * break has happened yet (or there are no confirmed pivots).
 */
export type StructureTrend = Bias | "neutral";

export interface Indicators {
  sma_20: number;
  sma_50: number;
  ema_20: number;
  ema_50: number;
  ema_200: number;
  rsi_14: number;
}

export interface FvgZone {
  type: "bullish" | "bearish";
  timestamp: string | null;
  lower: number;
  upper: number;
  size: number;
  size_percent: number;
  formation_index: number | null;
  mitigated: boolean;
  /*
   * Always null in practice. These are only populated by get_relevant_fvgs()
   * in backend/app/analysis/patterns.py, which the analysis pipeline never
   * calls — market_analysis.py uses get_active_fvgs() instead. Distance is
   * derived client-side from market.current_price.
   */
  position: string | null;
  distance: number | null;
  distance_percent: number | null;
}

export interface LiquidityLevel {
  type: "buy_side" | "sell_side";
  price: number;
  source: string;
  touches: number;
}

/** A clustered equal-high/equal-low level. `points` carries each touch. */
export interface LiquidityCluster {
  price: number;
  touches: number;
  points?: { index: number; timestamp: string; price: number }[];
}

export interface StructureEvent {
  event: "BOS" | "CHoCH";
  direction: "bullish" | "bearish";
  level: number;
  pivot_index: number | null;
  break_index: number | null;
  pivot_timestamp: string | null;
  break_timestamp: string | null;
}

export interface StructurePivot {
  index: number;
  timestamp: string | null;
  price: number;
  type: "high" | "low";
  label: "HH" | "HL" | "LH" | "LL" | null;
}

export interface StructureLayer {
  trend: StructureTrend;
  latest_event: StructureEvent | null;
  events: StructureEvent[];
  pivots: StructurePivot[];
}

export interface Confluence {
  bias: Bias;
  strength: "weak" | "moderate" | "strong";
  /** Integer 0-5, NOT a percentage. */
  score: number;
  bullish_score: number;
  bearish_score: number;
  bullish_factors: string[];
  bearish_factors: string[];
  conflicting_factors: string[];
  latest_swing_event: StructureEvent | null;
  latest_internal_event: StructureEvent | null;
  selected_fvg: FvgZone | null;
  nearby_fvgs: FvgZone[];
  nearest_buy_side_liquidity: LiquidityLevel | null;
  nearest_sell_side_liquidity: LiquidityLevel | null;
  reasons: string[];
}

export interface TradeSetup {
  setup: "LONG" | "SHORT" | "NO_SETUP";
  direction: "bullish" | "bearish" | null;
  confidence: "low" | "moderate" | "high";
  /** Integer 0-5; in practice only 0, 4 or 5. */
  score: number;
  entry_zone: number[] | null;
  entry_source: string | null;
  stop_loss: number | null;
  stop_source: string | null;
  targets: number[];
  target_source: string | null;
  risk: number | null;
  reward: number | null;
  risk_reward: number | null;
  reasons: string[];
  conflicts: string[];
  invalidated_if: string | null;
}

export interface AnalysisResponse {
  market: { symbol: string; timeframe: string; current_price: number };
  trend: Bias;
  indicators: Indicators;
  rsi_condition: "overbought" | "oversold" | "neutral";
  structure: { swing: StructureLayer; internal: StructureLayer };
  fvg: { active_count: number; zones: FvgZone[] };
  liquidity: {
    equal_highs: LiquidityCluster[];
    equal_lows: LiquidityCluster[];
    buy_side_liquidity: LiquidityLevel[];
    sell_side_liquidity: LiquidityLevel[];
  };
  confluence: Confluence;
  setup: TradeSetup;
}

// ---------------------------------------
// Market price types
// ---------------------------------------

export interface PriceResponse {
  symbol: string;
  currency: string;
  // CoinGecko fields are read with .get() in backend/app/market/coingecko.py,
  // so any of them can come back null.
  price: number | null;
  change_24h: number | null;
  volume_24h: number | null;
  market_cap: number | null;
}

// ---------------------------------------
// Internal helpers
// ---------------------------------------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (cause) {
    // An aborted request is a deliberate cancellation, not a dead backend.
    // Rethrow so callers can tell the two apart and stay silent on aborts.
    if (cause instanceof DOMException && cause.name === "AbortError") {
      throw cause;
    }

    throw new ApiError(
      0,
      "Could not reach the API. Is the backend running?",
    );
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      // Non-JSON error body; keep the generic message.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

/** True for the abort we deliberately triggered, which callers should ignore. */
export function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

// ---------------------------------------
// Endpoints
// ---------------------------------------

export function sendChatMessage(
  message: string,
  conversationId: string | null,
): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });
}

export function getConversationHistory(
  conversationId: string,
): Promise<ConversationHistoryResponse> {
  return request<ConversationHistoryResponse>(
    `/api/chat/${encodeURIComponent(conversationId)}/history`,
  );
}

/** `symbol` is a Binance pair, e.g. BTCUSDT. See lib/symbols.ts. */
export function getAnalysis(
  symbol: string,
  timeframe: string,
  signal?: AbortSignal,
): Promise<AnalysisResponse> {
  const query = new URLSearchParams({ timeframe });

  return request<AnalysisResponse>(
    `/api/analysis/${encodeURIComponent(symbol)}?${query}`,
    { signal },
  );
}

/** `ticker` is a bare ticker, e.g. BTC. See lib/symbols.ts. */
export function getPrice(
  ticker: string,
  signal?: AbortSignal,
): Promise<PriceResponse> {
  return request<PriceResponse>(
    `/api/market/${encodeURIComponent(ticker)}/price`,
    { signal },
  );
}
