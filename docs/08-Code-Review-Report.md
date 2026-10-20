# 08 Code Review Report

Structure follows IEEE 1028 review practice (IEEE 1028-2008 is inactive-reserved; used as an outline only). Date 2026-10-20.

## 1. Scope and method

Reviewed by reading every source line of `backend/routing/*.py`, `backend/config/settings.py`, `frontend/src/*.ts(x)` after
the first build, then running `ruff`, `tsc`, `django check --deploy` and the dependency audits. Reviewer and author: Danish Ahmed.
**This is a self-review, not an independent one.** A second engineer should review before submission.

## 2. Findings and disposition

| ID | File | Finding | Disposition |
|---|---|---|---|
| F-01 | `views.py` | Same-place trip accepted | Fixed (D02) |
| F-02 | `views.py` | No rate limit on an endpoint that calls three public APIs | Fixed; limit is per process and per `REMOTE_ADDR` (shortcut comment in code) |
| F-03 | `services.py` | Raw exception text returned | Fixed (D13) |
| F-04 | `services.py` | Weather fetched for every checkpoint every time | Fixed: 15-minute cache per location |
| F-05 | `services.py` | Closure over loop variable | Fixed (D09) |
| F-06 | `services.py` | Cache key with spaces | Fixed (D08) |
| F-07 | `settings.py` | No clickjacking header, no HTTPS options, no logging | Fixed; HTTPS options behind `DJANGO_FORCE_HTTPS=1` |
| F-08 | `planner.py` | Reason text misleading | Fixed (D01) |
| F-09 | `MapView.tsx` | Blue flash, renderer leak, HTML tooltip, tile URL | Fixed (D04, D05, D06, D12) |
| F-10 | `planner.py` | Checkpoint locations computed twice per route (plan and build) | Accepted: 267 ms CPU on 90,000 points, not worth the code |
| F-11 | `App.tsx` | State setter named `setInterval_` shadows a global by convention | Accepted, cosmetic |
| F-12 | `views.py` | `@csrf_exempt` | Accepted: stateless JSON API, no cookies or login (doc 09 S-05) |
| F-13 | all | Pyright reports unresolved Django imports and unused lambda parameters | Not defects: editor is not using the venv |
| F-14 | `services.py` | Missing weather hours become 0.0 (calm) | **Open**: unsafe default for a safety tool, SRS A-07. Needs an owner decision: treat as unknown and show a warning, or as worst case |
| F-15 | `planner.py` | `_via_points` builds offsets in flat degrees; poor at high latitudes or across the date line | Open, Low; fallback only |
| F-16 | `risk.py` | Uses sustained wind only (SRS A-03) | Open, owner to confirm |

## 3. Static analysis results

`ruff`: clean. `tsc --noEmit`: clean. `django check`: clean. Tests: 25 of 25.

## 4. Simplicity check

Removed during review: the `leaflet.heat` dependency and its type stub, the animation-frame batching in the heat
effect. Shortcuts left with comments in code: per-process rate limit (`views.rate_limited`), null weather as calm
(`services._column`).
