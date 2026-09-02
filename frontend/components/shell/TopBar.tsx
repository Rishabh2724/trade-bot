"use client";

import { usePathname } from "next/navigation";

import { useSymbolParams } from "@/lib/params";
import { SYMBOLS, TIMEFRAMES } from "@/lib/symbols";

/*
 * The mockup's top bar also carries a search box, a notification bell and an
 * "Alex Carter" avatar. All three are omitted: there is no auth, no user
 * record and no search index behind them, and a decorative bell that never
 * counts anything is worse than no bell.
 *
 * The symbol/timeframe pickers are fixed lists, not free text — see
 * lib/symbols.ts for why.
 */
export default function TopBar() {
  const pathname = usePathname();
  const { symbol, timeframe, set } = useSymbolParams();

  // Only the dashboard is scoped to a symbol; the chat is not.
  const showPickers = pathname === "/";

  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-line bg-panel px-3">
      <span className="flex items-center gap-2">
        <span
          aria-hidden
          className="h-2 w-2 rounded-full bg-accent shadow-[0_0_8px_var(--color-accent)]"
        />
        <span className="text-[13px] font-bold tracking-[0.16em] text-ink">
          TRADECOPILOT
        </span>
      </span>

      {showPickers ? (
        <div className="ml-auto flex items-center gap-2">
          <label className="sr-only" htmlFor="symbol-select">
            Symbol
          </label>
          <select
            id="symbol-select"
            value={symbol}
            onChange={(event) => set("symbol", event.target.value)}
            className="rounded-md border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-ink outline-none focus-visible:border-accent"
          >
            {SYMBOLS.map((entry) => (
              <option key={entry} value={entry}>
                {entry}
              </option>
            ))}
          </select>

          <div
            role="group"
            aria-label="Timeframe"
            className="hidden items-center gap-0.5 rounded-md border border-line bg-panel-2 p-0.5 sm:flex"
          >
            {TIMEFRAMES.map((entry) => (
              <button
                key={entry.tf}
                type="button"
                aria-pressed={entry.tf === timeframe}
                onClick={() => set("tf", entry.tf)}
                className={`rounded px-1.5 py-0.5 font-mono text-[11px] transition-colors ${
                  entry.tf === timeframe
                    ? "bg-accent/15 text-accent"
                    : "text-muted hover:text-ink"
                }`}
              >
                {entry.tf}
              </button>
            ))}
          </div>

          {/* The button row does not fit on a phone. */}
          <label className="sr-only" htmlFor="timeframe-select">
            Timeframe
          </label>
          <select
            id="timeframe-select"
            value={timeframe}
            onChange={(event) => set("tf", event.target.value)}
            className="rounded-md border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-ink outline-none focus-visible:border-accent sm:hidden"
          >
            {TIMEFRAMES.map((entry) => (
              <option key={entry.tf} value={entry.tf}>
                {entry.tf}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <span className="ml-auto text-[11px] tracking-wider text-muted uppercase">
          AI Assistant
        </span>
      )}
    </header>
  );
}
