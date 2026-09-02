import type { ReactNode } from "react";

interface PanelProps {
  title: string;
  /** Small right-aligned annotation, e.g. a count or a timestamp. */
  meta?: ReactNode;
  loading?: boolean;
  /** Shown instead of children — only when there is nothing to show. */
  error?: string | null;
  /** Shown alongside children — the data is real but the refetch failed. */
  stale?: string | null;
  /** Rendered when there is no error and no content to show. */
  empty?: string;
  isEmpty?: boolean;
  className?: string;
  bodyClassName?: string;
  children?: ReactNode;
}

/**
 * Titled panel frame. Owns loading / error / stale / empty so one failing
 * panel shows its own message instead of blanking the dashboard.
 */
export default function Panel({
  title,
  meta,
  loading = false,
  error = null,
  stale = null,
  empty = "No data.",
  isEmpty = false,
  className = "",
  bodyClassName = "",
  children,
}: PanelProps) {
  return (
    // min-h-0 is lg-only on purpose. It lets a panel shrink inside the fixed
    // desktop grid rows, but below lg the rows are auto-sized: a zero minimum
    // there means the track can be squeezed to nothing by the other panels'
    // min-heights, which is exactly how this panel collapsed to 2px.
    <section
      className={`flex flex-col rounded-panel border border-line bg-panel lg:min-h-0 ${className}`}
    >
      <header className="flex shrink-0 items-baseline justify-between gap-2 border-b border-line px-3 py-2">
        <h2 className="text-[11px] font-semibold tracking-[0.12em] text-muted uppercase">
          {title}
        </h2>

        <span className="flex items-baseline gap-2">
          {stale ? (
            // Never silently show old numbers as if they were current.
            <span
              title={stale}
              className="rounded-sm bg-amber-500/15 px-1.5 py-0.5 text-[9px] font-semibold tracking-wider text-amber-400 uppercase"
            >
              stale
            </span>
          ) : null}
          {meta ? (
            <span className="font-mono text-[10px] text-muted">{meta}</span>
          ) : null}
        </span>
      </header>

      {/*
        The body only fills and scrolls at lg, where the grid rows are a fixed
        height. Below lg it must size to its own content and let the page
        scroll. `flex-1` is `flex-basis: 0%`, so together with `min-h-0` the
        body contributes zero intrinsic height — in an auto grid row that
        collapsed the tallest panel to 2px.
      */}
      <div className={`p-3 lg:min-h-0 lg:flex-1 lg:overflow-auto ${bodyClassName}`}>
        {error ? (
          <p className="text-xs leading-relaxed text-danger">{error}</p>
        ) : loading ? (
          <Skeleton />
        ) : isEmpty ? (
          <p className="text-xs text-muted">{empty}</p>
        ) : (
          children
        )}
      </div>
    </section>
  );
}

function Skeleton() {
  return (
    <div className="flex flex-col gap-2" aria-hidden>
      {[70, 90, 50].map((width, index) => (
        <div
          key={index}
          className="h-3 animate-pulse rounded bg-panel-2"
          style={{ width: `${width}%` }}
        />
      ))}
    </div>
  );
}
