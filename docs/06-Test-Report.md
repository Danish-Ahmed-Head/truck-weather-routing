# 06 Test Report and Defect Log

Basis: ISO/IEC/IEEE 29119-3. Version 1.0, 2026-10-20. Environment: see [05](05-Test-Plan.md) section 2.

## 1. Automated results (run 2026-10-20, after all fixes)

| Check | Command | Result |
|---|---|---|
| Unit and integration | `manage.py test -v 2` | **25 run, 25 passed, 0 failed** (about 0.1 s) |
| Python lint | `ruff check` | All checks passed |
| Django system check | `manage.py check` | No issues |
| Python dependency audit | `pip-audit -r requirements.txt` | No known vulnerabilities |
| TypeScript | `tsc --noEmit` | Clean |
| Frontend build | `npm run build` | Success |
| npm dependency audit | `npm audit` | 0 vulnerabilities |
| Deploy check | `check --deploy` (secret set, HTTPS on) | 3 warnings, accepted (doc 09 S-05, S-06) |

## 2. Test cases by suite

test_risk: 8 passed. test_planner: 11 passed. test_views: 6 passed. Names are listed in [05](05-Test-Plan.md) section 5.

## 3. Manual system tests

| ID | Test | Result |
|---|---|---|
| M1 | Search Denver to Omaha on the upgraded stack (React 19, Vite 8) | Pass: 3 routes, Route A recommended, 12 checkpoint rows, one heat canvas |
| M2 | Slider changes heat colours | Pass before and after the dependency upgrade. After: 0 yellow pixels at hour 5, 58 at hour 23, 0 blue (the hours with risk were read from the API: 23, 42, 43) |
| M3 | Phone width 375 px, empty state | Pass: no horizontal scroll, form usable. **Not tested** with results shown or with keyboard on the slider |
| M4 | Denver to Denver | Pass after fix: HTTP 400 "same place" |
| M5 | Los Angeles to New York live | Pass: 3 routes (2794, 2779, 3073 mi), 57-62 checkpoints, 12.1 s, 169 KB |
| M6 | Real weather at the time of testing was calm | Risk colours above Low were therefore seen only in the 1-checkpoint Moderate case. High/Severe/No Travel visuals are **not** seen on live data |

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
| D14 | Missing (null) weather hours count as calm | Review | Medium | **Open**, accepted shortcut, SRS A-07 |
| D15 | Open-Meteo quota counts every location requested | Analysis | Medium | Mitigated by 15-minute cache, not eliminated |

## 5. Added after the first report draft

NFR-03 gap closed: `test_upstream_failure_is_502_with_generic_message` added (suite now 25 tests).
Not yet covered: the React UI has no automated tests (doc 11).
