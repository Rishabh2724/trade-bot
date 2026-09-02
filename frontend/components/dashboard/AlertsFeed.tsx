import Panel from "@/components/ui/Panel";
import type { AnalysisResponse } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { formatAgo, timestampKey } from "@/lib/time";

interface Alert {
  key: string;
  label: string;
  detail: string;
  timestamp: string | null;
  tone: "bullish" | "bearish" | "neutral";
}

/*
 * The mockup's "BTC BOS Detected" / "Liquidity Cluster Formed @ 71,500" are
 * both real backend events, so this panel is a direct merge of the two
 * sources: structure breaks (swing + internal) and equal-high/equal-low
 * liquidity clusters, newest first.
 *
 * A cluster carries no formation time of its own, so its most recent touch
 * stands in. Clusters with no points at all sort last rather than being
 * dropped.
 */
function collect(data: AnalysisResponse): Alert[] {
  const alerts: Alert[] = [];

  const layers = [
    { name: "swing", events: data.structure.swing.events },
    { name: "internal", events: data.structure.internal.events },
  ];

  for (const layer of layers) {
    for (const event of layer.events) {
      alerts.push({
        key: `${layer.name}-${event.event}-${event.break_index}-${event.level}`,
        label: `${event.event} ${event.direction}`,
        detail: `${layer.name} @ ${formatPrice(event.level)}`,
        timestamp: event.break_timestamp,
        tone: event.direction,
      });
    }
  }

  const clusters = [
    { kind: "Equal highs", rows: data.liquidity.equal_highs, tone: "bearish" },
    { kind: "Equal lows", rows: data.liquidity.equal_lows, tone: "bullish" },
  ] as const;

  for (const group of clusters) {
    for (const cluster of group.rows) {
      const latest = cluster.points?.[cluster.points.length - 1] ?? null;

      alerts.push({
        key: `${group.kind}-${cluster.price}-${cluster.touches}`,
        label: `${group.kind} cluster`,
        detail: `${formatPrice(cluster.price)} · ${cluster.touches} touches`,
        timestamp: latest?.timestamp ?? null,
        tone: group.tone,
      });
    }
  }

  return alerts.sort(
    (a, b) => timestampKey(b.timestamp) - timestampKey(a.timestamp),
  );
}

export default function AlertsFeed({
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
  const alerts = data ? collect(data).slice(0, 12) : [];

  return (
    <Panel
      title="Recent alerts"
      meta={data ? `${alerts.length}` : undefined}
      loading={loading}
      error={error}
      stale={stale}
      isEmpty={data !== null && alerts.length === 0}
      empty="No structure breaks or liquidity clusters in this window."
      className={className}
      bodyClassName="p-0"
    >
      <ul className="divide-y divide-line">
        {alerts.map((alert) => (
          <li
            key={alert.key}
            className="flex items-baseline gap-2 px-3 py-1.5 text-[11px]"
          >
            <span
              aria-hidden
              className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                alert.tone === "bullish"
                  ? "bg-accent"
                  : alert.tone === "bearish"
                    ? "bg-danger"
                    : "bg-muted"
              }`}
            />
            <span className="min-w-0 flex-1 truncate">
              <span className="text-ink">{alert.label}</span>
              <span className="ml-1.5 font-mono text-muted">
                {alert.detail}
              </span>
            </span>
            <span className="shrink-0 font-mono text-[10px] text-muted">
              {formatAgo(alert.timestamp)}
            </span>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
