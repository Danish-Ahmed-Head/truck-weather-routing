# 06 Test Report and Defect Log

Basis: ISO/IEC/IEEE 29119-3. Version 1.1, updated 2026-10-22. Environment: see [05](05-Test-Plan.md) section 2.

## 1. Automated results (run 2026-10-20, after all fixes)

| Check | Command | Result |
|---|---|---|
| Unit and integration (backend) | `manage.py test -v 2` | **29 run, 29 passed, 0 failed** (about 0.1 s; re-run 2026-10-22) |
| Frontend unit | `npm test` (Vitest 5.0.5) | **12 run, 12 passed** |
| Python lint | `ruff check` | All checks passed |
| Django system check | `manage.py check` | No issues |
| Python dependency audit | `pip-audit -r requirements.txt` | No known vulnerabilities |
| TypeScript | `tsc --noEmit` | Clean |
| Frontend build | `npm run build` | Success |
| npm dependency audit | `npm audit` | 0 vulnerabilities |
| Deploy check | `check --deploy` (secret set, HTTPS on) | 3 warnings, accepted (doc 09 S-05, S-06) |

## 2. Test cases by suite

test_risk: 8 passed. test_planner: 14 passed. test_views: 6 passed. Vitest: risk.test 7, heat.test 5. Names are listed in [05](05-Test-Plan.md) section 5.

## 3. Manual system tests

| ID | Test | Result |
|---|---|---|
| M1 | Search Denver to Omaha on the upgraded stack (React 19, Vite 8) | Pass: 3 routes, Route A recommended, 12 checkpoint rows, one heat canvas |
| M2 | Slider changes heat colours | Pass before and after the dependency upgrade. After: 0 yellow pixels at hour 5, 58 at hour 23, 0 blue (the hours with risk were read from the API: 23, 42, 43) |
| M3 | Phone width 375 px, empty state | Pass: no horizontal scroll, form usable. Results shown at 375 px and 768 px: see M9. Slider by keyboard: see M10 |
| M4 | Denver to Denver | Pass after fix: HTTP 400 "same place" |
| M5 | Los Angeles to New York live | Pass: 3 routes (2794, 2779, 3073 mi), 57-62 checkpoints, 12.1 s, 169 KB |
| M7 | Unknown-data UI: grey dots, "No data" chips, route warning, grey risk-bar segment | Pass using one patched API response (real nulls occur only at the far end of the forecast range) |
| M6 | Real weather at the time of testing was calm | Risk colours above Low were therefore seen only in the 1-checkpoint Moderate case. High/Severe/No Travel visuals are **not** seen on live data |
| M8 | Map tiles on the deployed site, real browser, 2026-10-21 | **Fail, then fixed**: every tile was OpenStreetMap's 403 "Access blocked" image (D17). After the fix, 28 of 28 tiles loaded on desktop, 8 of 8 at 375 px, 12 of 12 at 768 px |
| M9 | Phone (375 px) and tablet (768 px) with results, local and live, 2026-10-21 | Pass: no horizontal scroll and no overflowing control, order form, map, results, tiles load. Checkpoint table scrolls sideways inside its own box on a phone |
| M10 | Live site end to end after each deploy, 2026-10-21 | Pass: health OK, Salt Lake City to Great Falls (45,000 lb, every 10 mi) returned 3 routes with 63 checkpoints on the selected route, card switch works, Play/Pause moved the slider, slider by arrow keys, bad place gives HTTP 400, no console errors. A real High checkpoint was seen on live forecast data (local server with live forecast data, 16:00 departure: rain 0.28 in/hr at mile 180 on the fastest route) |

## 4. Defect log

Severity: High breaks a requirement, Medium wrong or unsafe in some cases, Low cosmetic or hygiene.

| ID | Defect | Found by | Sev | Status |
|---|---|---|---|---|
| D01 | Recommendation reason compared only with the runner-up, so it hid that another route was Severe | Test failure | Low | Fixed |
| D02 | Same origin and destination returned a fake 0-mile route | Measurement run | Medium | Fixed, test added |
| D03 | `leaflet.heat` saturated: Low-risk corridor drew orange and red | Browser | High | Fixed (redesign, doc 04 section 6) |
| D04 | New heat segments flashed Leaflet blue for one frame | Code review | Low | Fixed |
| D05 | A new canvas renderer per search was never removed (leak) | Code review | Medium | Fixed |
| D06 | Place names from Nominatim inserted into tooltips as HTML | Code review | Medium | Fixed |
| D07 | TypeScript 7 rejected untyped CSS imports | Upgrade build | Low | Fixed (`vite-env.d.ts`) |
| D08 | Geocode cache key had spaces (cache warning) | Live run | Low | Fixed (hashed key) |
| D09 | Closure over loop variable in weather parsing | ruff B023 | Low | Fixed |
| D10 | `X-Frame-Options` skipped because WhiteNoise answered first | Header check | Low | Fixed (middleware order) |
| D11 | Three old servers kept port 8000, so one round of checks hit stale code; `pkill` does not work in this shell | Verification | Process | Fixed by killing by PID; final checks ran on a fresh server |
| D12 | Tile URL used `{s}` subdomains, discouraged by OSM tile policy | Review | Low | Fixed |
| D13 | Raw upstream exception text shown to users | Review | Low | Fixed (logged, generic message) |
| D14 | Missing (null) weather hours counted as calm | Review | Medium | Fixed 2026-10-20: shown as unknown (FR-12), 3 backend tests |
| D16 | `manage.py` had a shebang but was not marked executable in git; `ruff` on Linux (CI) rejected it. Not visible on Windows | CI | Low | Fixed: mode 100755 |
| D15 | Open-Meteo quota counts every location requested | Analysis | Medium | Mitigated by 15-minute cache, not eliminated |
| D17 | Deployed site showed OpenStreetMap "Access blocked" (403) instead of map tiles: Django's default `Referrer-Policy: same-origin` sent no Referer to the tile server | Real browser on the live site (M8) | High | Fixed 2026-10-21 (`SECURE_REFERRER_POLICY`, test `SecurityHeaders`), commit 72b6d45 |
| D18 | After the UI restyle the phone form was clipped at the right edge (16 px inputs too wide for two columns) | Browser at 375 px | Medium | Fixed before commit: fields stack below 480 px, inputs can shrink |
| D19 | Floating heat panel covered the end of the route (Salt Lake City hidden) | Browser | Medium | Fixed: map fits routes with bottom padding |
| D20 | Full-width input rule also stretched the heat panel checkbox so its label wrapped | Live site after deploy | Low | Fixed in f13fea0 (live for a few minutes before the redeploy) |

## 5. Added after the first report draft

NFR-03 gap closed: `test_upstream_failure_is_502_with_generic_message` added.
Iteration 3: D14 fixed (backend, UI, 3 tests); Vitest added (12 tests); CI workflow added; its runs are listed below.
CI (GitHub Actions, Ubuntu, Python 3.12, Node 24): run 1 failed in the backend job on D16; run 2 passed all three jobs (backend: ruff, 28 tests, pip-audit; frontend: 12 tests, build, npm audit; docker: image build). This is the first Linux run of the lint and tests.
Later CI runs (2026-10-21): commits 72b6d45, 340103f and f13fea0 all passed backend (29 tests), frontend (12 tests, build) and docker.
Iteration 4 (2026-10-21): D17 found by looking at the deployed site; fixed with 1 test. UI cleanup (doc 04 section 8) with D18 to D20 found and fixed. Server updated by git pull plus a frontend rebuild on the host (doc 13 section 3).
Not covered: component rendering and the Leaflet map have no automated tests; they were checked by hand (M8 to M10). Risk pill colours for Moderate and High text were chosen by contrast calculation and not seen on screen in the final build.
