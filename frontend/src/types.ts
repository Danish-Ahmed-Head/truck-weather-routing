export interface Checkpoint {
  mile: number;
  lat: number;
  lon: number;
  eta: string;
  level: number;
  label: string;
  drivers: string[];
  wind_mph: number | null;
  rain_in_hr: number | null;
  snow_in_hr: number | null;
  forecast_beyond_range: boolean;
  /** True when the forecast has no data for this checkpoint's hour (level is then 0 and not counted as risk). */
  unknown: boolean;
  /** Risk level at this spot for each hour 0..48 after departure; -1 where the forecast has no data. */
  forecast: number[];
}

export interface RouteStats {
  no_travel_miles: number;
  severe_miles: number;
  high_miles: number;
  moderate_miles: number;
  low_miles: number;
  unknown_miles: number;
  avg_risk: number;
  max_level: number;
}

export interface Route {
  id: string;
  name: string;
  rank: number;
  recommended: boolean;
  reason?: string;
  distance_mi: number;
  duration_h: number;
  arrival: string;
  summary: string;
  interval_mi: number;
  stats: RouteStats;
  checkpoints: Checkpoint[];
  geometry: [number, number][];
}

export interface PlanResponse {
  origin: { name: string; lat: number; lon: number };
  destination: { name: string; lat: number; lon: number };
  departure: string;
  load_lb: number;
  routes: Route[];
}

export interface PlanRequest {
  origin: string;
  destination: string;
  departure: string;
  load_lb: number;
  interval: "auto" | 10 | 25 | 50;
}
