# 05 Test Plan

Basis: ISO/IEC/IEEE 29119-3 (test documentation). Version 1.0, 2026-10-20.

## 1. Scope and approach

| Level | What | How | Where |
|---|---|---|---|
| Static | Style, bugs, types, deploy settings | `ruff`, `tsc --noEmit`, `manage.py check --deploy` | CLI |
| Unit | Risk rules, ETA, checkpoints, ranking; frontend colour and heat logic | Django `SimpleTestCase` and Vitest, no network | `routing/tests/test_risk.py`, `test_planner.py` |
| Integration | HTTP endpoint with fake geocoder and fake network functions | Django test client | `routing/tests/test_views.py` |
| System (manual) | Real APIs end to end, map, slider | Browser pane, scripted JS checks | Doc 06 section 3 |
| Non-functional | Dependency audit, performance timing, deploy checks | `pip-audit`, `npm audit`, timing scripts | Docs 09, 10 |

Not covered by automation: rendering of React components and the Leaflet map (only the pure logic in `risk.ts` and `heat.ts` is unit-tested).

## 2. Environment

Windows 11, Python 3.12 venv, Node 24.15, Chromium-based in-app browser. Real network for system tests; none for unit and integration tests.

## 3. Entry and exit criteria

Entry: code compiles and lints. Exit: all automated tests pass, no open High or Medium defect, every FR has a verification result in doc 07.

## 4. Test design technique

Boundary value analysis on every risk threshold (just under, on, just over). Equivalence classes for load rules. Error guessing for input validation and degenerate trips.

## 5. Test cases (automated)

| Test | Verifies |
|---|---|
| `WindBands.test_bands` | FR-06 wind boundaries 24.9, 25, 34.9, 35, 45, 54.9, 55 |
| `RainAndSnowBands.test_rain`, `test_snow` | FR-06 rain and snow boundaries incl. strict No Travel |
| `RainAndSnowBands.test_worst_condition_wins` | FR-06 max of three conditions |
| `LoadRules` (4 tests) | FR-07 all three load rules, never lowering a level |
| `Recommendation.test_prefers_calm_route_even_when_slower` | FR-08 |
| `Recommendation.test_same_weather_picks_fastest` | FR-08 time tie-break |
| `Recommendation.test_load_changes_the_risk_of_the_same_weather` | FR-07 through the planner |
| `Recommendation.test_fills_to_three_routes_with_waypoint_alternatives` | FR-03 |
| `Recommendation.test_duplicate_alternatives_are_dropped` | FR-03 |
| `Checkpoints.test_interval_choice` | FR-04 |
| `Checkpoints.test_checkpoints_span_whole_route` | FR-04 |
| `Checkpoints.test_segment_miles_sum_to_route_length` | FR-04, FR-08 mileage |
| `Checkpoints.test_etas_increase_and_end_at_arrival` | FR-05, FR-10 strip length |
| `Checkpoints.test_weather_is_sampled_at_eta_not_departure` | FR-05 |
| `RequestValidation.test_rejects_bad_input` | FR-11 |
| `MissingForecast` (3 tests) | FR-12: unknown not calm, gaps rank lower, known data has no unknown miles |
| `risk.test.ts`, `heat.test.ts` (12 Vitest tests) | Colour blending, formatting, heat-corridor sampling and unknown propagation (FR-10, FR-12) |
| `RoutesEndpoint` (6 tests) | FR-01, FR-11, NFR-03, NFR-04: success, same place, bad JSON/fields, GET 405, rate limit 429, upstream failure 502 |

## 6. Manual system tests

M1 search Denver to Omaha: 3 routes, recommended badge, checkpoint table. M2 slider moves and heat colours change.
M3 phone width (375 px) and tablet (768 px) have no horizontal scroll, with results shown. M4 same-place error. M5 long route (Los Angeles to New York).

## 7. Defect handling

Every finding goes into the defect log in doc 06 with severity and status; fixes re-enter the loop in doc 01 section 3.
