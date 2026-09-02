import Panel from "@/components/ui/Panel";
import type { AnalysisResponse } from "@/lib/api";
import { formatPrice } from "@/lib/format";

import RsiGauge from "./RsiGauge";

/*
 * The mockup's right-hand DATA column. Its four widgets were a donut gauge, an
 * unlabelled needle, three rows (ETH / S&P 500 / GOLD) and a bar chart.
 *
 * What replaces them, and why:
 *   donut 80%   -> dropped; the same score is already 5 pips in the left panel
 *   needle      -> RSI-14, a real 0-100 reading
 *   SPX / GOLD  -> dropped; the backend is crypto-only (COIN_IDS), so equities
 *                  and metals have no source. The watchlist below the chart
 *                  covers the crypto rows.
 *   bar chart   -> confluence bullish_score vs bearish_score, which is a
 *                  genuine two-sided tally
 */
export default function DataPanel({
  data,
  loading,
  error,
  stale,
  className,
}: {
  data: AnalysisResponse | null;
  loading: boolean;
  error: string | null;
  stale: string | null;
  className?: string;
}) {
  return (
    <Panel
      title="Data"
      loading={loading}
      error={error}
      stale={stale}
      className={className}
    >
      {data ? (
        <div className="flex flex-col gap-4">
          <RsiGauge
            rsi={data.indicators.rsi_14}
            condition={data.rsi_condition}
          />

          <FactorBars
            bullish={data.confluence.bullish_score}
            bearish={data.confluence.bearish_score}
          />

          <div className="flex flex-col gap-1.5 border-t border-line pt-3">
            <span className="text-[10px] tracking-wider text-muted uppercase">
              Moving averages
            </span>

            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 font-mono text-[11px]">
              {(
                [
                  ["SMA 20", data.indicators.sma_20],
                  ["SMA 50", data.indicators.sma_50],
                  ["EMA 20", data.indicators.ema_20],
                  ["EMA 50", data.indicators.ema_50],
                  ["EMA 200", data.indicators.ema_200],
                ] as const
              ).map(([label, value]) => (
                <div key={label} className="col-span-2 flex justify-between">
                  <dt className="text-muted">{label}</dt>
                  <dd
                    className={
                      value > data.market.current_price
                        ? "text-danger"
                        : "text-accent"
                    }
                    // Above price is resistance, below is support.
                    title={
                      value > data.market.current_price
                        ? "above price"
                        : "below price"
                    }
                  >
                    {formatPrice(value)}
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          <Factors
            title="Bullish factors"
            items={data.confluence.bullish_factors}
            tone="text-accent"
          />
          <Factors
            title="Bearish factors"
            items={data.confluence.bearish_factors}
            tone="text-danger"
          />
        </div>
      ) : null}
    </Panel>
  );
}

function FactorBars({
  bullish,
  bearish,
}: {
  bullish: number;
  bearish: number;
}) {
  // Scale to the larger side so a 1-vs-0 tally does not render as a full bar
  // against an empty one at the same visual weight as 5-vs-0.
  const peak = Math.max(bullish, bearish, 1);

  const rows = [
    { label: "Bullish", value: bullish, tone: "bg-accent" },
    { label: "Bearish", value: bearish, tone: "bg-danger" },
  ];

  return (
    <div className="flex flex-col gap-1.5 border-t border-line pt-3">
      <span className="text-[10px] tracking-wider text-muted uppercase">
        Score breakdown
      </span>

      {rows.map((row) => (
        <div key={row.label} className="flex items-center gap-2">
          <span className="w-12 shrink-0 text-[10px] text-muted">
            {row.label}
          </span>
          <span className="h-2 min-w-0 flex-1 rounded-full bg-panel-2">
            <span
              className={`block h-full rounded-full ${row.tone}`}
              style={{ width: `${(row.value / peak) * 100}%` }}
            />
          </span>
          <span className="w-3 shrink-0 text-right font-mono text-[10px] text-ink">
            {row.value}
          </span>
        </div>
      ))}
    </div>
  );
}

function Factors({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: string;
}) {
  if (items.length === 0) return null;

  return (
    <div className="flex flex-col gap-1 border-t border-line pt-3">
      <span className="text-[10px] tracking-wider text-muted uppercase">
        {title}
      </span>
      <ul className="flex flex-col gap-0.5">
        {items.map((item) => (
          <li key={item} className={`text-[11px] leading-snug ${tone}`}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
