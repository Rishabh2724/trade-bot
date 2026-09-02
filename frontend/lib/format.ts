/*
 * Number formatting for panels.
 *
 * Every function takes null, because the backend reads CoinGecko fields with
 * .get() and several analysis fields are genuinely optional. A missing number
 * renders as an em dash — never as 0, which on a price panel reads as a real
 * quote.
 */

const DASH = "—";

/** Crypto spans ~$100k (BTC) to ~$0.0001, so precision has to scale. */
export function formatPrice(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return DASH;

  const decimals =
    Math.abs(value) >= 1000
      ? 2
      : Math.abs(value) >= 1
        ? 2
        : Math.abs(value) >= 0.01
          ? 4
          : 6;

  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/** Signed percent, e.g. "+2.41%". */
export function formatPercent(
  value: number | null | undefined,
  decimals = 2,
): string {
  if (value == null || !Number.isFinite(value)) return DASH;

  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}%`;
}

/** "$1.2B" — 24h volumes are too wide to print in full. */
export function formatCompact(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return DASH;

  return value.toLocaleString(undefined, {
    notation: "compact",
    maximumFractionDigits: 1,
  });
}

export function formatNumber(
  value: number | null | undefined,
  decimals = 2,
): string {
  if (value == null || !Number.isFinite(value)) return DASH;
  return value.toFixed(decimals);
}

/** Tailwind text colour for a signed change. */
export function signClass(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value) || value === 0) {
    return "text-muted";
  }
  return value > 0 ? "text-accent" : "text-danger";
}

/** Tailwind text colour for a directional bias. */
export function biasClass(bias: string | null | undefined): string {
  if (bias === "bullish") return "text-accent";
  if (bias === "bearish") return "text-danger";
  return "text-muted";
}

export { DASH };
