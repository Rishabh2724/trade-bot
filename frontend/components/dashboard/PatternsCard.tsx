import type { AnalysisResponse, StructureEvent } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { formatAgo } from "@/lib/time";

/*
 * The mockup's "Active Patterns: Head and Shoulders (Developing)" has no
 * backend equivalent — the engine detects market-structure breaks, not chart
 * patterns. What it does detect is real and more actionable: BOS (break of
 * structure, trend continuation) and CHoCH (change of character, potential
 * reversal), on two layers.
 */
export default function PatternsCard({ data }: { data: AnalysisResponse }) {
  const layers: { name: string; event: StructureEvent | null; trend: string }[] =
    [
      {
        name: "Swing",
        event: data.structure.swing.latest_event,
        trend: data.structure.swing.trend,
      },
      {
        name: "Internal",
        event: data.structure.internal.latest_event,
        trend: data.structure.internal.trend,
      },
    ];

  return (
    <section className="flex flex-col gap-2 border-t border-line pt-3">
      <span className="text-[10px] tracking-wider text-muted uppercase">
        Market structure
      </span>

      {layers.map((layer) => (
        <div key={layer.name} className="flex flex-col gap-0.5">
          <div className="flex items-baseline justify-between gap-2">
            <span className="text-[11px] text-muted">{layer.name}</span>

            {layer.event ? (
              <span
                className={`rounded-sm px-1.5 py-0.5 text-[10px] font-semibold tracking-wider ${
                  layer.event.direction === "bullish"
                    ? "bg-accent/15 text-accent"
                    : "bg-danger/15 text-danger"
                }`}
              >
                {layer.event.event} {layer.event.direction}
              </span>
            ) : (
              <span className="text-[10px] text-muted">no break yet</span>
            )}
          </div>

          {layer.event ? (
            <div className="flex items-baseline justify-between gap-2 font-mono text-[11px]">
              <span className="text-ink">
                @ {formatPrice(layer.event.level)}
              </span>
              <span className="text-muted">
                {formatAgo(layer.event.break_timestamp)}
              </span>
            </div>
          ) : (
            <span className="text-[11px] text-muted capitalize">
              {layer.trend}
            </span>
          )}
        </div>
      ))}
    </section>
  );
}
