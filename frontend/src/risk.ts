export const LEVEL_LABELS = ["Low", "Moderate", "High", "Severe", "No Travel"];
export const LEVEL_COLORS = ["#2e9e5b", "#e0b400", "#f07f1d", "#d62828", "#5b1a6e"];
/** Forecast strip value and colour for an hour with no weather data. */
export const UNKNOWN = -1;
export const UNKNOWN_COLOR = "#9aa0a6";

const LEVEL_RGB = LEVEL_COLORS.map((hex) => {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
});

/** Blend between level colours so a fractional level (between two checkpoints) gets a smooth hue. */
export function levelColor(level: number): string {
  if (level < 0) return UNKNOWN_COLOR;
  const lo = Math.min(4, Math.floor(level));
  const hi = Math.min(4, lo + 1);
  const t = level - lo;
  const c = LEVEL_RGB[lo].map((v, k) => Math.round(v + (LEVEL_RGB[hi][k] - v) * t));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

export const checkpointColor = (c: { level: number; unknown: boolean }) => (c.unknown ? UNKNOWN_COLOR : LEVEL_COLORS[c.level]);

/** Label colour that stays readable on a level's fill: white is too faint on the lighter greens, yellows and greys. */
export const LEVEL_TEXT = ["#14231a", "#2b2300", "#2e1700", "#fff", "#fff"];
export const UNKNOWN_TEXT = "#1b1f24";
export const checkpointText = (c: { level: number; unknown: boolean }) => (c.unknown ? UNKNOWN_TEXT : LEVEL_TEXT[c.level]);

export const fmtNum = (v: number | null) => (v === null ? "-" : String(v));

export const ROUTE_COLORS: Record<string, string> = { A: "#1f6feb", B: "#8250df", C: "#0a8f8f", D: "#bc4c00" };

export const routeColor = (id: string) => ROUTE_COLORS[id] ?? "#555";

export function fmtTime(iso: string, withDate = true): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: withDate ? "short" : undefined,
    hour: "numeric",
    minute: "2-digit",
    month: withDate ? "short" : undefined,
    day: withDate ? "numeric" : undefined,
  });
}

export function fmtDuration(hours: number): string {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  return m === 60 ? `${h + 1}h 00m` : `${h}h ${String(m).padStart(2, "0")}m`;
}
