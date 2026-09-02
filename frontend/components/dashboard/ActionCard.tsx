import type { AnalysisResponse } from "@/lib/api";
import { formatNumber, formatPrice } from "@/lib/format";

/*
 * The mockup's "Suggested Action: BUY SIGNAL" maps to setup.setup, which the
 * deterministic engine emits as LONG / SHORT / NO_SETUP with entry, stop,
 * targets and R:R attached.
 *
 * NO_SETUP is shown as prominently as a signal. A dashboard that only ever
 * looks confident trains the user to expect a trade on every glance.
 */
export default function ActionCard({ data }: { data: AnalysisResponse }) {
  const { setup } = data;

  const isLong = setup.setup === "LONG";
  const isShort = setup.setup === "SHORT";

  const tone = isLong
    ? "border-accent/40 bg-accent/10 text-accent"
    : isShort
      ? "border-danger/40 bg-danger/10 text-danger"
      : "border-line bg-panel-2 text-muted";

  const [entryLow, entryHigh] = setup.entry_zone ?? [];

  return (
    <section className="flex flex-col gap-2 border-t border-line pt-3">
      <span className="text-[10px] tracking-wider text-muted uppercase">
        Suggested action
      </span>

      <div
        className={`flex items-baseline justify-between gap-2 rounded-md border px-2 py-1.5 ${tone}`}
      >
        <span className="text-sm font-bold tracking-wide">
          {setup.setup === "NO_SETUP" ? "NO SETUP" : setup.setup}
        </span>
        <span className="font-mono text-[10px]">
          {setup.score}/5 · {setup.confidence}
        </span>
      </div>

      {setup.setup === "NO_SETUP" ? (
        <p className="text-[11px] leading-relaxed text-muted">
          {setup.reasons[0] ?? "Not enough confluence for a setup."}
        </p>
      ) : (
        <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 font-mono text-[11px]">
          <dt className="text-muted">Entry</dt>
          <dd className="text-right text-ink">
            {entryLow != null
              ? `${formatPrice(entryLow)}–${formatPrice(entryHigh)}`
              : "—"}
          </dd>

          <dt className="text-muted">Stop</dt>
          <dd className="text-right text-danger">
            {formatPrice(setup.stop_loss)}
          </dd>

          <dt className="text-muted">
            Target{setup.targets.length === 1 ? "" : "s"}
          </dt>
          <dd className="text-right text-accent">
            {setup.targets.length > 0
              ? setup.targets.map((target) => formatPrice(target)).join(" / ")
              : "—"}
          </dd>

          <dt className="text-muted">R:R</dt>
          <dd className="text-right text-ink">
            {setup.risk_reward != null
              ? `${formatNumber(setup.risk_reward, 2)}:1`
              : "—"}
          </dd>
        </dl>
      )}

      {setup.invalidated_if ? (
        <p className="text-[11px] leading-relaxed text-muted">
          <span className="text-amber-400">Invalid if</span>{" "}
          {setup.invalidated_if}
        </p>
      ) : null}

      {setup.conflicts.length > 0 ? (
        <p className="text-[11px] leading-relaxed text-amber-400">
          {setup.conflicts.join("; ")}
        </p>
      ) : null}

      {/*
        The engine is deterministic, not predictive. Saying so next to an
        entry/stop/target block is the difference between research and advice.
      */}
      <p className="text-[10px] leading-relaxed text-muted/70">
        Deterministic rule output, not financial advice.
      </p>
    </section>
  );
}
