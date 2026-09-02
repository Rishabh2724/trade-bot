import { formatNumber } from "@/lib/format";

interface Props {
  /** indicators.rsi_14, a real 0-100 value. */
  rsi: number;
  /** rsi_condition from the backend — its thresholds, not ours. */
  condition: "overbought" | "oversold" | "neutral";
}

/*
 * Replaces the mockup's unlabelled needle gauge. RSI-14 is a genuine 0-100
 * reading, so it maps onto a bar honestly — unlike the mockup's "Bet" needle,
 * which had no data source at all.
 *
 * The 30/70 marks are drawn where the backend's own thresholds sit
 * (backend/app/analysis/market_analysis.py), so the bar and the label can
 * never disagree.
 */
export default function RsiGauge({ rsi, condition }: Props) {
  const clamped = Math.max(0, Math.min(rsi, 100));

  const tone =
    condition === "overbought"
      ? "bg-danger"
      : condition === "oversold"
        ? "bg-accent"
        : "bg-muted";

  const label =
    condition === "overbought"
      ? "text-danger"
      : condition === "oversold"
        ? "text-accent"
        : "text-muted";

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between">
        <span className="text-[10px] tracking-wider text-muted uppercase">
          RSI-14
        </span>
        <span className="font-mono text-xs text-ink">
          {formatNumber(rsi, 1)}
        </span>
      </div>

      <div
        role="meter"
        aria-valuenow={Math.round(clamped)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`RSI 14 at ${formatNumber(rsi, 1)}, ${condition}`}
        className="relative h-1.5 overflow-hidden rounded-full bg-panel-2"
      >
        <span
          className={`absolute inset-y-0 left-0 rounded-full ${tone}`}
          style={{ width: `${clamped}%` }}
        />
        {/* Oversold / overbought boundaries. */}
        <span className="absolute inset-y-0 left-[30%] w-px bg-bg/70" />
        <span className="absolute inset-y-0 left-[70%] w-px bg-bg/70" />
      </div>

      <span className={`text-[10px] capitalize ${label}`}>{condition}</span>
    </div>
  );
}
