import type { PlanRequest, PlanResponse } from "./types";

export async function planRoutes(req: PlanRequest, signal?: AbortSignal): Promise<PlanResponse> {
  const res = await fetch("/api/routes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error ?? `Request failed (${res.status})`);
  return body as PlanResponse;
}
