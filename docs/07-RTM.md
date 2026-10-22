# 07 Requirements Traceability Matrix

Basis: ISO/IEC/IEEE 29148. Version 1.0, 2026-10-20.

| Req | Design module | Code | Automated test | Manual / other | Status |
|---|---|---|---|---|---|
| FR-01 | views, App | `views.parse_request`, `App.tsx` form | `RequestValidation`, `RoutesEndpoint` | M1 | Verified |
| FR-02 | services | `services.geocode` | `RoutesEndpoint` (fake geocoder) | M1, M5 live | Verified live; no unit test of the real geocoder |
| FR-03 | planner, services | `gather_routes`, `fetch_routes`, `fetch_route_via` | `test_fills_to_three...`, `test_duplicate...` | M1, M5 | Verified |
| FR-04 | planner | `pick_interval`, `checkpoint_miles` | 3 `Checkpoints` tests | M1 | Verified |
| FR-05 | planner, services | `build_route`, `hour_index` | `test_weather_is_sampled_at_eta...` | - | Verified |
| FR-06 | risk | `risk.assess` | `WindBands`, `RainAndSnowBands` | - | Verified at every boundary |
| FR-07 | risk | `risk.assess` | `LoadRules`, `test_load_changes...` | - | Verified |
| FR-08 | planner | `rank_key`, `_reason` | `Recommendation` (3 tests) | M1 | Verified |
| FR-09 | App, MapView | route cards, popups, table | none | M1 | Demonstrated only |
| FR-10 | MapView, heat.ts | heat segments, slider | strip length in `test_etas...`, `heat.test.ts` (sampling, blend) | M2 | Logic unit-tested; rendering demonstrated only; High/Severe visuals not seen on live data |
| FR-11 | views | `parse_request`, error mapping | `RequestValidation`, `RoutesEndpoint` | M4 | Verified |
| FR-12 | planner, services, UI | `_assess_at`, `build_route`, `heat.sampleLevels`, grey states | `MissingForecast` (3), `heat.test.ts` | M7 | Verified |
| NFR-02 | MapView | restyle-only effect | none | Code inspection | Inspected |
| NFR-03 | services, views | `UpstreamError` to 502 | `test_upstream_failure_is_502...` | - | Verified at the HTTP layer; client code not unit-tested |
| NFR-04 | views | `rate_limited` | `test_rate_limit_returns_429` | - | Verified |
| NFR-05 | settings | env secret | none | `check --deploy` | Inspected |
| NFR-06 | - | - | - | pip-audit, npm audit | Verified |
| NFR-07 | styles | media query | none | M3, M9 (375 and 768 px with results), M10 (slider by arrow keys) | Verified for phone, tablet and keyboard slider; screen reader not tested |
| NFR-08 | docs | this set, README | - | - | Done |

Unverified or gaps: FR-09 and FR-10 have no automated tests; NFR-07 is partial.
