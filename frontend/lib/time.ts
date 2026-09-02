/*
 * The backend stringifies pandas Timestamps, which produces
 * "2026-09-02 11:30:00+00:00" — space-separated, not ISO-8601 with a "T".
 *
 * V8 happens to parse that, but it is not spec-guaranteed and other engines
 * return NaN. Everything that reads a backend timestamp goes through here.
 */
export function parseTimestamp(value: string | null | undefined): Date | null {
  if (!value) return null;

  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const date = new Date(normalized);

  return Number.isNaN(date.getTime()) ? null : date;
}

/** "14:32" in the viewer's locale, or "—" when the timestamp is unusable. */
export function formatClock(value: string | null | undefined): string {
  const date = parseTimestamp(value);
  if (!date) return "—";

  return date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    // 24h regardless of locale: candle timestamps are 24h, and "07:54 PM"
    // sitting next to "19:00" invites misreading one for the other.
    hour12: false,
  });
}

/** Compact "3m ago" / "2h ago" for feed rows. */export function formatAgo(value: string | null | undefined): string {
  const date = parseTimestamp(value);
  if (!date) return "—";

  const seconds = Math.round((Date.now() - date.getTime()) / 1000);

  if (seconds < 0) return "just now";
  if (seconds < 60) return `${seconds}s ago`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  return `${Math.floor(hours / 24)}d ago`;
}

/**
 * Sortable numeric key for a backend timestamp. Unparseable values sort last
 * rather than being silently dropped from a feed.
 */
export function timestampKey(value: string | null | undefined): number {
  return parseTimestamp(value)?.getTime() ?? -Infinity;
}

/** "14:32" for a Date we made ourselves, e.g. a hook's lastUpdated. */
export function clockOf(date: Date | null | undefined): string {
  if (!date) return "—";

  return date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}
