# Weather-Aware Truck Routing

React + Django app that helps a truck driver pick the safest of three routes using forecast weather
sampled at the truck's estimated arrival time at each checkpoint, the load weight and the travel time.

- **Backend:** Django 5 (no database), `backend/routing/`
- **Frontend:** React 18 + TypeScript + Vite + Leaflet, `frontend/`
- **Third-party APIs (all free, no API key):** OSRM (routing), Nominatim (geocoding), Open-Meteo (weather)

## Run locally

```bash
# backend
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Linux/macOS: .venv/bin/pip
DJANGO_DEBUG=1 .venv/Scripts/python manage.py runserver 127.0.0.1:8000

# frontend (second terminal) - dev server proxies /api to :8000
cd frontend
npm ci
npm run dev        # http://localhost:5173
```

Single-origin build (what production uses): `cd frontend && npm run build` writes to
`backend/frontend_dist/`, which Django/WhiteNoise then serves at `/` next to `/api/`.

```bash
cd backend && DJANGO_DEBUG=1 python manage.py test     # 25 tests, no network needed
cd frontend && npm run build                           # typechecks, then builds
```

Docker (verified locally): `docker build -t truck-routing . && docker run -p 8000:8000 -e DJANGO_SECRET_KEY=change-me -e DJANGO_ALLOWED_HOSTS=localhost truck-routing`. The container runs as a non-root user and listens on `$PORT` (default 8000).

### Environment variables

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Required unless `DJANGO_DEBUG=1` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts (default `localhost,127.0.0.1`) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Optional, comma-separated |
| `OSRM_URL`, `NOMINATIM_URL`, `OPEN_METEO_URL` | Point at your own instances if you outgrow the public ones |
| `TRUCK_TIME_FACTOR` | Multiplier on OSRM car durations (default `1.15`) |

## How it works

`POST /api/routes` with `{origin, destination, departure (ISO), load_lb, interval}` returns every route with
its checkpoints, risk stats and a recommendation.

1. **Routes.** OSRM returns the main route plus its alternatives. If fewer than three distinct routes come back
   (distinct = under 85% of the new route within 1 mile of an existing one), extra routes are forced through
   waypoints offset sideways from the midpoint.
2. **Checkpoints.** Spaced every 10, 25 or 50 miles. "Auto" picks 10 mi under 150 mi, 25 mi under 500 mi and
   50 mi beyond; the user can force any of the three.
3. **ETA.** Route duration (OSRM car time x `TRUCK_TIME_FACTOR`) is spread along the route by distance.
4. **Weather.** One batched Open-Meteo call returns hourly wind, rain and snowfall per checkpoint. Each checkpoint
   uses the hour nearest its own ETA, not the departure time.
5. **Risk.** `backend/routing/risk.py` applies the brief's thresholds and load rules (unit-tested at every boundary).
6. **Recommendation.** Routes are ranked by: No Travel miles, Severe miles, High miles, average risk, then duration.
   Each checkpoint stands for the stretch halfway to its neighbours, which gives miles per risk level.
7. **Heatmap.** Each checkpoint also carries its risk for hours 0-48 after departure. The slider recolours a
   blurred corridor along every route; it only restyles existing segments, so scrubbing does not rebuild layers.

## Assumptions and limits

- **Overlapping boundaries.** The brief's ranges touch at their edges (rain 0.10-0.25 vs 0.25-0.50). Lower bounds are
  inclusive; No Travel for rain and snow is strictly above 1.00 and 3.0, as written. Wind uses `>=` 55.
- **Units.** Rain is mm/hr converted to in/hr. Snow is Open-Meteo snowfall (cm of snow depth per hour) converted to
  in/hr, so it is snow depth, not liquid equivalent. Wind is sustained 10 m wind speed, not gusts.
- **Severe vs No Travel in ranking.** No Travel miles are compared first (a route you cannot drive loses), then Severe.
- **Tie tolerance.** Mileage is compared in 5-mile buckets and average risk in 0.1 steps, so a 1-mile difference does not
  beat a much faster route. Only exact ties fall through to travel time.
- **Truck pace.** OSRM only has a car profile, so durations are scaled by 1.15. It does not know about truck
  restrictions, weight limits or low bridges.
- **Forecast window.** Departure must be within the last 24 hours to 12 days ahead. If a trip runs past the
  16-day forecast, the last available hour is used and the checkpoint is flagged `forecast_beyond_range`.
- **Public APIs.** The public OSRM and Nominatim servers are for light use. Nominatim limits requests to about one per
  second and forbids autocomplete, so places are geocoded on submit. Locations also accept `lat, lon`.
- **No auth or database.** Geocoding results are cached in memory for a day.
