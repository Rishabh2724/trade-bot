import type { AnalysisResponse, FvgZone } from "@/lib/api";
import { formatPercent, formatPrice } from "@/lib/format";

/*
 * "Key SMC zones" — unmitigated fair-value gaps plus the nearest liquidity
 * on each side.
 *
 * Distance is computed here, not read from the payload. FvgZone.position /
 * distance / distance_percent are only ever populated by get_relevant_fvgs()
 * in backend/app/analysis/patterns.py, which nothing calls — the pipeline uses
 * get_active_fvgs(). Those three fields arrive null on every zone, so the
 * arithmetic has to happen client-side against market.current_price.
 */

interface Derived {
  zone: FvgZone;
  distancePercent: number | null;
  position: "above" | "below" | "inside" | null;
}

function derive(zone: FvgZone, price: number): Derived {
  if (!Number.isFinite(price) || price <= 0) {
    return { zone, distancePercent: null, position: null };
  }

  const midpoint = (zone.lower + zone.upper) / 2;

  return {
    zone,
    distancePercent: ((midpoint - price) / price) * 100,
    position:
      price > zone.upper ? "below" : price < zone.lower ? "above" : "inside",
  };
}

export default function ZonesCard({ data }: { data: AnalysisResponse }) {
  const price = data.market.current_price;

  // Nearest first — that is the one price can reach next.
  const zones = data.fvg.zones
    .map((zone) => derive(zone, price))
    .sort(
      (a, b) =>
        Math.abs(a.distancePercent ?? Infinity) -
        Math.abs(b.distancePercent ?? Infinity),
    )
    .slice(0, 4);

  const buySide = data.confluence.nearest_buy_side_liquidity;
  const sellSide = data.confluence.nearest_sell_side_liquidity;

  return (
    <section className="flex flex-col gap-2 border-t border-line pt-3">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[10px] tracking-wider text-muted uppercase">
          Key SMC zones
        </span>
        <span className="font-mono text-[10px] text-muted">
          {data.fvg.active_count} active
        </span>
      </div>

      {zones.length === 0 ? (
        <p className="text-[11px] text-muted">No unmitigated FVGs.</p>
      ) : (
        <ul className="flex flex-col gap-1">
          {zones.map(({ zone, distancePercent, position }, index) => (
            <li
              key={`${zone.formation_index ?? index}-${zone.lower}`}
              className="flex items-baseline justify-between gap-2 font-mono text-[11px]"
            >
              <span
                className={
                  zone.type === "bullish" ? "text-accent" : "text-danger"
                }
              >
                {zone.type === "bullish" ? "Demand" : "Supply"}
              </span>

              <span className="text-ink">
                {formatPrice(zone.lower)}–{formatPrice(zone.upper)}
              </span>

              <span
                className={
                  position === "inside" ? "text-amber-400" : "text-muted"
                }
              >
                {position === "inside"
                  ? "in zone"
                  : formatPercent(distancePercent, 1)}
              </span>
            </li>
          ))}
        </ul>
      )}

      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 border-t border-line pt-2 font-mono text-[11px]">
        <dt className="text-muted">Buy-side liq.</dt>
        <dd className="text-right text-accent">
          {buySide ? formatPrice(buySide.price) : "—"}
          {buySide ? (
            <span className="ml-1 text-muted">×{buySide.touches}</span>
          ) : null}
        </dd>

        <dt className="text-muted">Sell-side liq.</dt>
        <dd className="text-right text-danger">
          {sellSide ? formatPrice(sellSide.price) : "—"}
          {sellSide ? (
            <span className="ml-1 text-muted">×{sellSide.touches}</span>
          ) : null}
        </dd>
      </dl>
    </section>
  );
}
