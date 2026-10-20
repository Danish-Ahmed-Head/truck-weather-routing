export const LEVEL_LABELS = ["Low", "Moderate", "High", "Severe", "No Travel"];
export const LEVEL_COLORS = ["#2e9e5b", "#e0b400", "#f07f1d", "#d62828", "#5b1a6e"];
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
