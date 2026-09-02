"use client";

import Panel from "@/components/ui/Panel";
import { formatCompact, formatPercent, formatPrice, signClass } from "@/lib/format";
import { usePrices } from "@/lib/hooks";
import { clockOf } from "@/lib/time";
import { tickerToPair, WATCHLIST } from "@/lib/symbols";

/*
 * The mockup's LIVE MARKET FEED shows a sparkline per row. There is no
 * historical-price endpoint behind /api/market/{ticker}/price — it returns a
 * single spot quote — so a sparkline would have to be invented. The column is
 * dropped rather than faked; 24h change carries the same directional signal
 * and is real.
 */
export default function MarketFeed({
  onSelect,
  className,
}: {
  onSelect?: (symbol: string) => void;
  className?: string;
}) {
  const feed = usePrices(WATCHLIST);
  const rows = feed.data ?? [];

  return (
    <Panel
      title="Live market feed"
      meta={
        feed.lastUpdated ? `updated ${clockOf(feed.lastUpdated)}` : undefined
      }
      loading={feed.loading && rows.every((row) => row.price === null)}
      error={feed.error}
      className={className}
      bodyClassName="p-0"
    >
      <table className="w-full border-collapse text-[11px]">
        <thead>
          <tr className="text-left text-muted">
            <th className="px-3 py-1.5 font-normal">Asset</th>
            <th className="px-3 py-1.5 text-right font-normal">Price</th>
            <th className="px-3 py-1.5 text-right font-normal">24h</th>
            <th className="hidden px-3 py-1.5 text-right font-normal sm:table-cell">
              Volume
            </th>
          </tr>
        </thead>

        <tbody>
          {rows.map((row) => {
            const pair = tickerToPair(row.ticker);

            return (
              <tr
                key={row.ticker}
                onClick={onSelect ? () => onSelect(pair) : undefined}
                className={`border-t border-line ${
                  onSelect ? "cursor-pointer hover:bg-panel-2" : ""
                }`}
              >
                <th
                  scope="row"
                  className="px-3 py-1.5 text-left font-mono font-normal text-ink"
                >
                  {row.ticker}
                </th>

                {row.price ? (
                  <>
                    <td className="px-3 py-1.5 text-right font-mono text-ink">
                      {formatPrice(row.price.price)}
                    </td>
                    <td
                      className={`px-3 py-1.5 text-right font-mono ${signClass(
                        row.price.change_24h,
                      )}`}
                    >
                      {formatPercent(row.price.change_24h)}
                    </td>
                    <td className="hidden px-3 py-1.5 text-right font-mono text-muted sm:table-cell">
                      {formatCompact(row.price.volume_24h)}
                    </td>
                  </>
                ) : (
                  <td
                    colSpan={3}
                    className="px-3 py-1.5 text-right text-[10px] text-danger"
                  >
                    {/* A per-coin failure stays on its own row. */}
                    {row.error ?? "loading…"}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </Panel>
  );
}
