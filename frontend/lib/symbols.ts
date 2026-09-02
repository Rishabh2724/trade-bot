// The backend uses two different symbol conventions on the same API:
//
//   GET /api/analysis/{symbol}      wants a Binance pair, e.g. BTCUSDT
//   GET /api/market/{symbol}/price  wants a bare ticker,  e.g. BTC
//
// This module is the single place that knows about both.

// Mirrors COIN_IDS in backend/app/market/coingecko.py. Anything outside this
// list gets a 400 from /api/market, so the picker only ever offers these.
export const TICKERS = [
  "BTC",
  "ETH",
  "SOL",
  "BNB",
  "XRP",
  "ADA",
  "DOGE",
  "AVAX",
  "LINK",
  "DOT",
] as const;

export type Ticker = (typeof TICKERS)[number];

export const SYMBOLS = TICKERS.map((ticker) => `${ticker}USDT`);

// Shown in the market feed and the compact right-hand rows.
export const WATCHLIST: Ticker[] = ["BTC", "ETH", "SOL", "BNB"];

export const DEFAULT_SYMBOL = "BTCUSDT";
export const DEFAULT_TIMEFRAME = "1h";

export function pairToTicker(pair: string): string {
  return pair.replace(/USDT$/, "");
}

export function tickerToPair(ticker: string): string {
  return `${ticker}USDT`;
}

/*
 * Timeframes.
 *
 * The backend supports 14 (SUPPORTED_TIMEFRAMES in
 * backend/app/analysis/market_analysis.py), but TradingView's free Advanced
 * Chart embed only accepts 1, 3, 5, 15, 30, 60, 120, 180, 240, D, W, M — so
 * 6h, 8h, 12h and 3d have no chart representation.
 *
 * Those four are deliberately left out. Offering them would mean the chart
 * silently renders a different timeframe than the one the insight panels
 * analyzed, and a chart/analysis mismatch on a trading dashboard is worse
 * than a missing option.
 */
export interface Timeframe {
  /** Value the backend expects. */
  tf: string;
  /** TradingView Advanced Chart `interval` value. */
  tv: string;
  /** Seconds per candle, used to derive the poll interval. */
  seconds: number;
}

export const TIMEFRAMES: Timeframe[] = [
  { tf: "1m", tv: "1", seconds: 60 },
  { tf: "3m", tv: "3", seconds: 180 },
  { tf: "5m", tv: "5", seconds: 300 },
  { tf: "15m", tv: "15", seconds: 900 },
  { tf: "30m", tv: "30", seconds: 1800 },
  { tf: "1h", tv: "60", seconds: 3600 },
  { tf: "2h", tv: "120", seconds: 7200 },
  { tf: "4h", tv: "240", seconds: 14400 },
  { tf: "1d", tv: "D", seconds: 86400 },
  { tf: "1w", tv: "W", seconds: 604800 },
];

export function findTimeframe(tf: string): Timeframe {
  return (
    TIMEFRAMES.find((entry) => entry.tf === tf) ??
    TIMEFRAMES.find((entry) => entry.tf === DEFAULT_TIMEFRAME)!
  );
}

/**
 * How often to re-run the analysis for a given timeframe.
 *
 * The backend has no cache: every call pulls 500 candles from Binance and
 * walks them against every pivot. Re-analyzing a daily chart every 30s is
 * pure waste, so the cadence scales with the candle size.
 */
export function pollIntervalMs(timeframe: Timeframe): number {
  const quarterCandle = (timeframe.seconds / 4) * 1000;
  return Math.min(Math.max(quarterCandle, 30_000), 300_000);
}
