import { UNKNOWN } from "./risk";
import type { Route } from "./types";

export interface HeatSample {
  lat: number;
  lon: number;
  /** Position between checkpoint `i` and `i + 1` (0..1), used to blend the hourly risk. */
  i: number;
  t: number;
  route: Route;
}

export const HEAT_STEP_MILES = 3;

/** Points densely spaced along each route's checkpoints so the heatmap reads as a continuous corridor. */
export function buildSamples(routes: Route[]): HeatSample[] {
  const out: HeatSample[] = [];
  for (const route of routes) {
    const cps = route.checkpoints;
    for (let i = 0; i < cps.length - 1; i++) {
      const steps = Math.max(1, Math.ceil((cps[i + 1].mile - cps[i].mile) / HEAT_STEP_MILES));
      for (let s = 0; s < steps; s++) {
        const t = s / steps;
        out.push({
          lat: cps[i].lat + (cps[i + 1].lat - cps[i].lat) * t,
          lon: cps[i].lon + (cps[i + 1].lon - cps[i].lon) * t,
          i,
          t,
          route,
        });
      }
    }
    const last = cps[cps.length - 1];
    out.push({ lat: last.lat, lon: last.lon, i: cps.length - 2, t: 1, route });
  }
  return out;
}

/** Risk level of each sample at `hour` after departure; UNKNOWN when either neighbouring checkpoint has no data. */
export function sampleLevels(samples: HeatSample[], hour: number): number[] {
  return samples.map(({ i, t, route }) => {
    const a = route.checkpoints[Math.max(0, i)].forecast[hour];
    const b = route.checkpoints[Math.min(route.checkpoints.length - 1, i + 1)].forecast[hour];
    return a === UNKNOWN || b === UNKNOWN ? UNKNOWN : a + (b - a) * t;
  });
}
