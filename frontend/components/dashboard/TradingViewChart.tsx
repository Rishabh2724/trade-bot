"use client";

import { useEffect, useRef } from "react";

interface Props {
  /** Binance pair, e.g. BTCUSDT. */
  symbol: string;
  /** TradingView `interval` value from lib/symbols.ts, e.g. "60". */
  tvInterval: string;
}

const SCRIPT_SRC =
  "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";

/**
 * TradingView Advanced Chart embed.
 *
 * Three things about this widget drive the shape of the code:
 *
 *  1. Config is passed as the script tag's innerHTML (the embed script reads
 *     document.currentScript), not as a constructor argument.
 *  2. There is no in-place update API, so a symbol or interval change means
 *     rebuilding the container.
 *  3. When the script finally executes it walks up to its own parent and
 *     queries inside it. If we have already detached the script by then, that
 *     parent is null and the script throws
 *     "Cannot read properties of null (reading 'querySelector')".
 *
 * Point 3 is why teardown removes a per-instance *wrapper* rather than doing
 * `host.innerHTML = ""`. Clearing innerHTML orphans the script element, so a
 * request still in flight lands with a null parent — which happens on every
 * React StrictMode double-mount and on every fast timeframe click. Removing
 * the wrapper keeps `script.parentElement` pointing at the (now detached)
 * wrapper, so a late script injects into a node nobody can see and is then
 * garbage collected. No throw, no orphan widget.
 *
 * The build is also delayed a frame or two. Tearing the widget down while it
 * is still initializing makes TradingView log "contentWindow is not
 * available", and StrictMode's synchronous mount/unmount/mount does exactly
 * that. The delay lets the discarded pass cancel before anything is built,
 * and doubles as a debounce when the user clicks through timeframes quickly.
 *
 * SMC zones, BOS levels and FVGs are NOT drawn here — the embed has no
 * drawing API for external data. They live in the panels around the chart.
 */
export default function TradingViewChart({ symbol, tvInterval }: Props) {
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const parent = host.current;
    if (!parent) return;

    let wrapper: HTMLDivElement | null = null;

    const timer = setTimeout(() => {
      wrapper = document.createElement("div");
      wrapper.className = "tradingview-widget-container";

      const widget = document.createElement("div");
      widget.className = "tradingview-widget-container__widget";

      const script = document.createElement("script");
      script.src = SCRIPT_SRC;
      script.async = true;
      script.innerHTML = JSON.stringify({
        autosize: true,
        symbol: `BINANCE:${symbol}`,
        interval: tvInterval,
        timezone: "Etc/UTC",
        theme: "dark",
        style: "1",
        locale: "en",
        hide_side_toolbar: true,
        // The top bar owns the symbol. Letting the chart change it too would
        // silently desync it from every analysis panel around it.
        allow_symbol_change: false,
        backgroundColor: "rgba(18, 23, 29, 1)",
        gridColor: "rgba(35, 44, 54, 0.6)",
        support_host: "https://www.tradingview.com",
      });

      wrapper.append(widget, script);
      parent.appendChild(wrapper);
    }, 80);

    return () => {
      clearTimeout(timer);
      wrapper?.remove();
    };
  }, [symbol, tvInterval]);

  return <div ref={host} className="h-full w-full" />;
}
