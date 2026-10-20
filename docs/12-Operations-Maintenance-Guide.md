# 12 Operations and Maintenance Guide

Basis: ISO/IEC/IEEE 12207 operation and maintenance processes (outline). Date 2026-10-20.

## 1. Run

Local: see the README. Production container: `docker build -t truck-routing .` then run with `DJANGO_SECRET_KEY`,
`DJANGO_ALLOWED_HOSTS`, optionally `DJANGO_FORCE_HTTPS=1` when behind TLS. The image listens on `$PORT` (default 8000). Built and run locally on 2026-10-20.
Health check: `GET /api/health` returns `{"status":"ok"}`.

## 2. Configuration

| Variable | Meaning |
|---|---|
| `DJANGO_SECRET_KEY` | Required in production |
| `DJANGO_DEBUG` | `1` for local development only |
| `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma separated |
| `DJANGO_FORCE_HTTPS` | `1` turns on redirect, 1-year HSTS and proxy header |
| `OSRM_URL`, `NOMINATIM_URL`, `OPEN_METEO_URL` | Point at own instances |
| `HTTP_USER_AGENT` | Sent to Nominatim and others; set a contact address for real use |
| `TRUCK_TIME_FACTOR` | Default 1.15 |
| `LOG_LEVEL` | Default INFO |

## 3. Runbook

| Symptom | Likely cause | Action |
|---|---|---|
| Users see "Routing/Weather/Geocoding service is unavailable" (502) | Public API down or throttling | Check the service status; read the warning in the log; switch the URL variable to another instance |
| 429 "Too many requests" | Rate limit | Wait 10 minutes or raise `RATE_LIMIT` in `views.py` |
| Requests take over 15 s | Slow upstream | Check logs; see doc 10 |
| Blank map tiles | Tile server blocked or offline | Check network access to `tile.openstreetmap.org` |
| Grey "No data" checkpoints | Open-Meteo returned null hours (seen at the far end of the 16-day range) | Choose a nearer departure; inspect the raw Open-Meteo response |
| Port 8000 already in use during development | Old server still running | `netstat -ano | grep :8000`, then `taskkill //PID <pid> //F` (do not rely on `pkill` on Windows) |

## 4. Maintenance

Dependency upgrade loop: check latest versions (`npm view`, PyPI, endoflife.date), bump one group, run
`manage.py test`, `ruff`, `tsc --noEmit`, `npm run build`, run the app, fix, repeat. Re-run `pip-audit` and `npm audit` before every release.
Next due review: Django 6.1 is supported to Dec 2027; Django 5.2 LTS to Apr 2028; Python 3.12 to Oct 2028; Node 24 to Apr 2028
(dates from endoflife.date, 2026-10-20).

## 5. Change log

| Date | Change |
|---|---|
| 2026-10-20 | Iteration 1: initial build (commit 022081f) |
| 2026-10-20 | Iteration 3: unknown-weather policy (FR-12), Vitest (12 tests), GitHub Actions workflow (green), PythonAnywhere guide (doc 13), public repo created |
| 2026-10-20 | Iteration 2: stack upgrade, review fixes D01-D13, tests 19 to 25, hardening, docs set (commits 8858aaf and later) |

## 6. Known limits

See SRS assumptions A-01 to A-09, doc 08 open findings, doc 10 recommendations.
