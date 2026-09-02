/*
 * Confluence score display.
 *
 * The backend's confluence score is an integer 0-5 (five boolean-ish factors),
 * so it is rendered as five discrete pips, not the smooth arc gauge in the
 * mockup. An arc implies precision the engine does not have — it can only ever
 * land on 0, 20, 40, 60, 80 or 100 percent, and showing "80%" invites reading
 * it as a probability. "4/5" says what it actually is.
 */

interface Props {
  score: number;
  max?: number;
  bias: string;
  strength: string;
}

export default function ScoreMeter({ score, max = 5, bias, strength }: Props) {
  const filled = Math.max(0, Math.min(Math.round(score), max));

  const tone =
    bias === "bullish"
      ? "bg-accent"
      : bias === "bearish"
        ? "bg-danger"
        : "bg-muted";

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between">
        <span className="text-[10px] tracking-wider text-muted uppercase">
          Confluence
        </span>
        <span className="font-mono text-xs text-ink">
          {filled}/{max}
        </span>
      </div>

      <div
        role="meter"
        aria-valuenow={filled}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={`Confluence score ${filled} of ${max}`}
        className="flex gap-1"
      >
        {Array.from({ length: max }, (_, index) => (
          <span
            key={index}
            className={`h-1.5 flex-1 rounded-full ${
              index < filled ? tone : "bg-panel-2"
            }`}
          />
        ))}
      </div>

      <span className="text-[10px] text-muted capitalize">
        {strength} {bias}
      </span>
    </div>
  );
}
