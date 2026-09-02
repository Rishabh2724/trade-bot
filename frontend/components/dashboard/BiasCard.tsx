import { biasClass, formatPercent, formatPrice } from "@/lib/format";
import type { AnalysisResponse } from "@/lib/api";

import ScoreMeter from "./ScoreMeter";

export default function BiasCard({ data }: { data: AnalysisResponse }) {
  const { confluence, market, trend, indicators } = data;

  // EMA 50 vs 200 is the classic regime read and both are already on the wire.
  const emaSpread =
    indicators.ema_200 !== 0
      ? ((indicators.ema_50 - indicators.ema_200) / indicators.ema_200) * 100
      : null;

  return (
    <section className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[10px] tracking-wider text-muted uppercase">
          Current market bias
        </span>
        <span className="font-mono text-sm text-ink">
          {formatPrice(market.current_price)}
        </span>
      </div>

      <span
        className={`text-lg leading-none font-bold capitalize ${biasClass(
          confluence.bias,
        )}`}
      >
        {confluence.bias}
      </span>

      <ScoreMeter
        score={confluence.score}
        bias={confluence.bias}
        strength={confluence.strength}
      />

      <dl className="mt-1 grid grid-cols-2 gap-x-3 gap-y-1 border-t border-line pt-2 text-[11px]">
        <dt className="text-muted">Trend</dt>
        <dd className={`text-right capitalize ${biasClass(trend)}`}>{trend}</dd>

        <dt className="text-muted">EMA 50 / 200</dt>
        <dd
          className={`text-right font-mono ${
            emaSpread == null
              ? "text-muted"
              : emaSpread > 0
                ? "text-accent"
                : "text-danger"
          }`}
        >
          {formatPercent(emaSpread)}
        </dd>
      </dl>

      {confluence.conflicting_factors.length > 0 ? (
        <p className="text-[11px] leading-relaxed text-amber-400">
          {confluence.conflicting_factors.length} conflicting factor
          {confluence.conflicting_factors.length === 1 ? "" : "s"}:{" "}
          {confluence.conflicting_factors.join("; ")}
        </p>
      ) : null}
    </section>
  );
}
