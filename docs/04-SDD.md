# 04 Software Design Description

Basis: IEEE 1016 (design viewpoints). Version 1.0, 2026-10-20.

## 1. Context viewpoint

Browser (React SPA) calls one Django JSON endpoint. Django calls three public services. No database.

| External service | Used for | Called from |
|---|---|---|
| Nominatim (OpenStreetMap) | Geocoding place names | `services.geocode`, cached 24 h |
| OSRM public server | Routes and alternatives | `services.fetch_routes`, `fetch_route_via` |
| Open-Meteo | Hourly wind, rain, showers, snowfall | `services.fetch_weather`, cached 15 min per location |
| OpenStreetMap tile server | Map tiles | Browser directly |

## 2. Composition viewpoint (modules)

| Module | Responsibility | Requirements |
|---|---|---|
| `backend/routing/risk.py` | Pure risk classification and load rules | FR-06, FR-07 |
| `backend/routing/geo.py` | Haversine distance, polyline interpolation, thinning | FR-04 |
| `backend/routing/services.py` | The three API clients, unit conversion, caching, error type | FR-02, FR-03, FR-05 |
| `backend/routing/planner.py` | Route set, checkpoints, ETA, stats, ranking, reason | FR-03 to FR-08 |
| `backend/routing/views.py` | HTTP endpoint, validation, rate limit, error mapping | FR-01, FR-11 |
| `backend/config/settings.py` | Env-driven settings, hardening | NFR-04, NFR-05 |
| `frontend/src/App.tsx` | Form, route cards, checkpoint table, slider | FR-01, FR-09, FR-10 |
| `frontend/src/MapView.tsx` | Leaflet map: lines, dots, popups, heat corridor | FR-09, FR-10 |
| `frontend/src/risk.ts`, `types.ts`, `api.ts` | Colours and labels, API types, fetch wrapper | - |

Dependency rule: `risk.py` and `geo.py` import nothing from the project. `planner.py` receives its network functions
as an injected dict, so tests run without network.

## 3. Interface viewpoint

`POST /api/routes` request: `{origin, destination, departure (ISO), load_lb, interval: "auto"|10|25|50}`.
Response: `{origin, destination, departure, load_lb, routes[]}`. Each route: `id, name, rank, recommended, reason?,
distance_mi, duration_h, arrival, summary, interval_mi, stats{no_travel_miles, severe_miles, high_miles,
moderate_miles, low_miles, avg_risk, max_level}, checkpoints[], geometry[[lat,lon]]` (at most 1500 points).
Checkpoint: `mile, lat, lon, eta, level, label, drivers[], wind_mph, rain_in_hr, snow_in_hr, forecast_beyond_range,
forecast[49]` (risk level 0-4 for hours 0..48 after departure).
Errors: 400 invalid input or unknown place, 405 wrong method, 429 rate limit, 502 upstream failure.
`GET /api/health` returns `{"status":"ok"}`.

## 4. Interaction viewpoint (one search)

1. Validate body, rate-limit check. 2. Geocode origin and destination; reject if under 1 mile apart.
3. OSRM alternatives; keep those that are distinct; fill to 3 by routing through offset waypoints.
4. Compute checkpoint locations for every route; one deduplicated batched weather call (40 locations per call).
5. For each route: ETA per checkpoint, weather at nearest hour, risk, 49-hour strip, stats.
6. Rank, write the recommendation reason, return JSON. Front end draws lines, dots, heat corridor.

## 5. Algorithm viewpoint

**Risk.** Level = max(wind level, rain level, snow level), then load rules can only raise it (doc 03 A-01).
**Checkpoints.** Miles 0, k x interval, ..., total. Each checkpoint owns the road halfway to each neighbour; this gives
miles per level and the mile-weighted average risk.
**ETA.** departure + route duration x (checkpoint mile / total miles).
**Ranking key.** (No Travel miles/5, Severe miles/5, High miles/5, avg risk/0.1, duration), each rounded, lowest first.
**Distinct route.** A candidate is dropped if at least 85% of 25 sample points lie within 1 mile of an existing route.
**Heat corridor.** Samples every 3 miles between checkpoints; segment colour is the level at the chosen hour,
interpolated between neighbouring checkpoints; drawn in its own canvas pane with a CSS blur. Slider restyles segments only.

## 6. Design decisions and rejected options

| Decision | Rejected | Reason |
|---|---|---|
| Corridor of coloured, blurred segments | `leaflet.heat` plugin | Plugin sums overlapping points, so dense sampling turned Low risk orange (defect D03) |
| No database | Postgres | Nothing needs to persist; fewer parts to run |
| Injected network functions | Mocking `requests` | Simpler tests, no patching |
| Single-origin deploy (Django serves built SPA) | Separate frontend host | One service, no CORS |
| `requests` + public APIs | Paid APIs | No keys needed for the assessment |

## 7. Resources and limits

Weather payload per location is about 384 hours x 4 variables. Public API quotas apply (doc 10).

## 8. UI layout (updated 2026-10-21)

- Desktop: a 420 px sidebar (form panel, then results panel) beside the map. Phone and tablet (800 px and narrower): one column in the order form, map, results, so the map is not buried under the route list. Below 480 px the Departure and Load fields stack.
- Route card: distance, drive time and arrival as labelled figures, a risk bar, one line of Severe+/High/average-risk miles and a pill for the worst level. Pill and chip text colours come from `LEVEL_TEXT` in `risk.ts` so labels stay readable on yellow, orange and grey.
- While a search runs the form shows a status line, because a new trip can take 15 to 20 seconds; before the first search an empty-state hint explains what to do.
- `MapView` fits all routes with 150 px of bottom padding so the floating heat panel never covers the route.
- The server sends `Referrer-Policy: strict-origin-when-cross-origin` (Django's default `same-origin` made OpenStreetMap block the map tiles, defect D17).
