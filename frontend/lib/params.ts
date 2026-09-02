"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

import {
  DEFAULT_SYMBOL,
  DEFAULT_TIMEFRAME,
  SYMBOLS,
  TIMEFRAMES,
} from "@/lib/symbols";

/**
 * Symbol and timeframe live in the URL (`/?symbol=BTCUSDT&tf=1h`) so the view
 * is shareable and survives a reload, and so the chart and the analysis
 * panels read one source instead of a context.
 *
 * Both values are clamped to the lists we know the backend accepts. A
 * hand-edited `?symbol=NONSENSE` would otherwise come back as a 400 the user
 * has no way to diagnose.
 *
 * Callers must be inside a <Suspense> boundary — Next requires it for
 * useSearchParams.
 */
export function useSymbolParams() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const rawSymbol = params.get("symbol")?.toUpperCase() ?? "";
  const rawTimeframe = params.get("tf")?.toLowerCase() ?? "";

  const symbol = SYMBOLS.includes(rawSymbol) ? rawSymbol : DEFAULT_SYMBOL;
  const timeframe = TIMEFRAMES.some((entry) => entry.tf === rawTimeframe)
    ? rawTimeframe
    : DEFAULT_TIMEFRAME;

  const set = useCallback(
    (key: "symbol" | "tf", value: string) => {
      const next = new URLSearchParams(params.toString());
      next.set(key, value);

      // replace, not push: flipping a timeframe should not fill the back stack.
      router.replace(`${pathname}?${next}`, { scroll: false });
    },
    [params, pathname, router],
  );

  return { symbol, timeframe, set };
}
