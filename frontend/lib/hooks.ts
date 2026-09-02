"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  ApiError,
  getAnalysis,
  getPrice,
  isAbort,
  type AnalysisResponse,
  type PriceResponse,
} from "@/lib/api";
import { findTimeframe, pollIntervalMs } from "@/lib/symbols";

/**
 * A panel's view of one polled request.
 *
 * `error` and `stale` are deliberately exclusive:
 *
 *   error  — nothing to show, the panel renders the message instead
 *   stale  — the last payload is still on screen, the refetch failed
 *
 * On a trading dashboard "these numbers are 4 minutes old" beats an empty
 * box, so a failed *refetch* never blanks a panel that already had real data.
 */
export interface Feed<T> {
  data: T | null;
  error: string | null;
  stale: string | null;
  loading: boolean;
  lastUpdated: Date | null;
  refresh: () => void;
}

function message(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Something went wrong loading this panel.";
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Statuses worth backing off on: rate limit, upstream down, network dead. */
function shouldBackOff(error: unknown): boolean {
  const status = error instanceof ApiError ? error.status : -1;
  return status === 0 || status === 429 || status === 502 || status === 503;
}

/**
 * Analysis for one symbol/timeframe, polled on a cadence derived from the
 * candle size.
 *
 * Chained with setTimeout rather than setInterval: the next run is scheduled
 * only once the current one settles, so a slow backend can never accumulate
 * overlapping in-flight requests. In-flight requests abort on symbol or
 * timeframe change, so a late response for the old symbol cannot land
 * afterwards and show numbers that disagree with the chart.
 */
export function useAnalysis(
  symbol: string,
  timeframe: string,
): Feed<AnalysisResponse> {
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [nonce, setNonce] = useState(0);

  const refresh = useCallback(() => setNonce((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    const interval = pollIntervalMs(findTimeframe(timeframe));

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let backoff = 1;
    let served = false;

    // A symbol change makes the previous payload wrong, not merely stale.
    setData(null);
    setError(null);
    setLoading(true);

    function schedule(ms: number) {
      if (cancelled) return;
      if (timer) clearTimeout(timer);
      timer = setTimeout(run, ms);
    }

    async function run() {
      if (cancelled) return;

      // A forgotten background tab must not keep hammering an uncached
      // backend. Check again later; the visibility listener wakes us sooner.
      //
      // Only *polls* are skipped, never the first load. A dashboard opened in
      // a hidden tab (session restore, cmd-click) or inside an embedded pane
      // that reports hidden while plainly visible would otherwise sit on
      // skeletons forever, waiting for a visibility change that never comes.
      if (served && document.hidden) {
        schedule(interval);
        return;
      }

      try {
        const result = await getAnalysis(symbol, timeframe, controller.signal);
        if (cancelled) return;

        setData(result);
        setError(null);
        setLastUpdated(new Date());
        backoff = 1;
      } catch (cause) {
        if (cancelled || isAbort(cause)) return;

        if (shouldBackOff(cause)) backoff = Math.min(backoff * 2, 10);
        setError(message(cause));
      } finally {
        if (!cancelled) {
          served = true;
          setLoading(false);
          schedule(interval * backoff);
        }
      }
    }

    function onVisibilityChange() {
      // Coming back to the tab should show fresh numbers immediately rather
      // than whatever was on screen when it was backgrounded.
      if (!document.hidden) schedule(0);
    }

    document.addEventListener("visibilitychange", onVisibilityChange);
    run();

    return () => {
      cancelled = true;
      controller.abort();
      if (timer) clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [symbol, timeframe, nonce]);

  const hasData = data !== null;

  return {
    data,
    error: hasData ? null : error,
    stale: hasData ? error : null,
    loading,
    lastUpdated,
    refresh,
  };
}

export interface PriceRow {
  ticker: string;
  price: PriceResponse | null;
  error: string | null;
}

/**
 * Watchlist prices. One HTTP call per coin — the backend has no batch price
 * endpoint.
 *
 * Deliberately sequential with a small stagger rather than Promise.all: every
 * call leaves the backend's single IP against an unauthenticated CoinGecko
 * rate limit, and a simultaneous burst is exactly what trips it and returns
 * 502 for every coin at once. Spreading them over ~1s costs nothing, and each
 * row commits as its own response lands so the table fills progressively
 * instead of waiting on the slowest.
 */
export function usePrices(tickers: string[]): Feed<PriceRow[]> {
  const [rows, setRows] = useState<PriceRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [nonce, setNonce] = useState(0);

  const refresh = useCallback(() => setNonce((value) => value + 1), []);

  // Keyed on contents so a fresh array literal with the same tickers does not
  // restart the cycle on every render.
  const key = tickers.join(",");
  const tickersRef = useRef(tickers);
  tickersRef.current = tickers;

  useEffect(() => {
    const controller = new AbortController();
    const list = tickersRef.current;

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let backoff = 1;
    let served = false;

    setRows(list.map((ticker) => ({ ticker, price: null, error: null })));
    setLoading(true);

    function commit(ticker: string, next: Partial<PriceRow>) {
      setRows((current) =>
        (current ?? []).map((row) =>
          row.ticker === ticker ? { ...row, ...next } : row,
        ),
      );
    }

    function schedule(ms: number) {
      if (cancelled) return;
      if (timer) clearTimeout(timer);
      timer = setTimeout(run, ms);
    }

    async function run() {
      if (cancelled) return;

      // Polls pause in a background tab; the first load never does. See the
      // same guard in useAnalysis for why.
      if (served && document.hidden) {
        schedule(60_000);
        return;
      }

      let failures = 0;

      for (const ticker of list) {
        if (cancelled) return;

        try {
          const price = await getPrice(ticker, controller.signal);
          if (cancelled) return;
          commit(ticker, { price, error: null });
        } catch (cause) {
          if (cancelled || isAbort(cause)) return;

          failures += 1;
          // A per-coin failure only marks its own row. Any price already
          // fetched stays on screen rather than dropping back to a dash.
          commit(ticker, { error: message(cause) });
        }

        await sleep(250);
      }

      if (cancelled) return;

      backoff = failures === list.length ? Math.min(backoff * 2, 8) : 1;

      served = true;

      // Only stamp a time when something actually arrived. "updated 20:08"
      // sitting above "Could not reach the API" reads as fresh data.
      if (failures < list.length) setLastUpdated(new Date());

      setLoading(false);
      schedule(60_000 * backoff);
    }

    function onVisibilityChange() {
      if (!document.hidden) schedule(0);
    }

    document.addEventListener("visibilitychange", onVisibilityChange);
    run();

    return () => {
      cancelled = true;
      controller.abort();
      if (timer) clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [key, nonce]);

  // Only a total wipeout is a panel-level error; partial data is worth showing.
  const wipedOut =
    rows !== null &&
    rows.length > 0 &&
    rows.every((row) => row.price === null && row.error !== null);

  return {
    data: rows,
    error: wipedOut ? rows[0].error : null,
    stale: null,
    loading,
    lastUpdated,
    refresh,
  };
}
