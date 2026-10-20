# 03 Software Requirements Specification

Basis: ISO/IEC/IEEE 29148 (requirements engineering). Version 1.0, 2026-10-20. Source: the assessment brief.

## 1. Introduction

**Purpose.** Specify a web app that helps a truck driver choose the safest route by weather, load weight and travel time.
**Users.** One user type: a truck driver or dispatcher. **Operating environment.** Modern desktop browser; server runs Python 3.12 or newer.

## 2. Functional requirements

Verification methods: T = automated test, D = demonstration in the running app, I = inspection.

| ID | Requirement | Verify |
|---|---|---|
| FR-01 | The user enters origin, destination, departure date/time and load weight. | D, T |
| FR-02 | The system resolves place names (or "lat, lon") to coordinates. | D |
| FR-03 | The system generates 3 route options using a routing API. | T, D |
| FR-04 | The system samples weather at checkpoints every 10, 25 or 50 miles. | T |
| FR-05 | Weather at each checkpoint is taken for the truck's estimated arrival time there. | T |
| FR-06 | Each checkpoint is classified Low/Moderate/High/Severe/No Travel from wind, rain and snow thresholds. | T |
| FR-07 | Load rules apply: wind >=55 is No Travel for any load; 45-54 mph with load >30,000 lb is No Travel; 35-44 mph with load >40,000 lb is Severe. | T |
| FR-08 | The system recommends the best route by: fewest Severe miles, fewest High miles, lowest average risk, shortest travel time. | T |
| FR-09 | The map shows all routes, checkpoints, risk levels, ETAs and route summaries. | D |
| FR-10 | A weather heatmap along the trip corridor has a 0-48 hour forecast slider. | D |
| FR-11 | Invalid input (missing place, same place, bad load, date outside forecast window) gets a clear error. | T |
| FR-12 | An hour with no forecast data is shown as unknown (grey, "No data"), is never treated as calm, and a route with gaps ranks below an otherwise equal fully forecast route. | T, D |

### Threshold table (from the brief)

| Condition | Low | Moderate | High | Severe | No Travel |
|---|---|---|---|---|---|
| Wind | <25 mph | 25-34 | 35-44 | 45-54 | >=55 |
| Rain | <0.10 in/hr | 0.10-0.25 | 0.25-0.50 | 0.50-1.00 | >1.00 |
| Snow | <0.5 in/hr | 0.5-1.0 | 1.0-2.0 | 2.0-3.0 | >3.0 |

## 3. Non-functional requirements

| ID | Requirement | Verify |
|---|---|---|
| NFR-01 | Correctness and clarity take priority over extra features (brief). | I |
| NFR-02 | Slider changes redraw the heatmap without rebuilding layers. | I, D |
| NFR-03 | Third-party failures return a readable error, not a crash. | T |
| NFR-04 | The service limits request rate per client. | T |
| NFR-05 | No secret is stored in code; production requires `DJANGO_SECRET_KEY`. | I |
| NFR-06 | Dependencies have no known vulnerabilities at release. | pip-audit, npm audit |
| NFR-07 | The map and form work at phone width and the slider is keyboard operable. | D (partial, doc 11) |
| NFR-08 | Documentation: README, assumptions, this set. | I |

## 4. Constraints

C-01 Third-party APIs allowed (brief). C-02 Free public services need no API key. C-03 4 days / 16 hours (brief).

## 5. Assumptions and interpretations (owner to confirm; nothing here is silent)

| ID | Interpretation | Why it needed deciding |
|---|---|---|
| A-01 | Lower bound inclusive for Moderate/High/Severe; rain and snow No Travel strictly above 1.00 and 3.0 as written; wind No Travel at >=55. **Confirmed by the owner 2026-10-20 (higher band at a shared edge).** | Brief ranges overlap at edges (rain 0.25) |
| A-02 | "Every 10 / 25 / 50 miles" is a spacing the user may pick; "Auto" uses 10 mi under 150 mi, 25 mi under 500, 50 mi beyond. | Brief does not say how to choose |
| A-03 | Wind is sustained 10 m wind speed, not gusts. | Brief says "wind" only |
| A-04 | Snow is Open-Meteo snowfall (cm snow depth per hour) converted to inches. | Brief says "in/hr" without saying depth or water |
| A-05 | No Travel miles are compared before Severe miles when ranking; mileage compared in 5-mile buckets, risk in 0.1 steps. | Brief lists Severe first and "balancing" with time |
| A-06 | Truck duration is OSRM car duration x 1.15. | OSRM has no truck profile |
| A-07 | Missing (null) weather hours are unknown, not calm (FR-12). **Decided by the owner 2026-10-20.** Live check: every location returned 5 null hours at the end of the 16-day range. | Needs a policy |
| A-08 | Departure must be between 24 hours ago and 12 days ahead. | Forecast window is 16 days |
| A-09 | Heatmap hour 0 is the departure time; slider shows a fixed clock time for the whole corridor, not per-ETA. | Brief says "0-48 hour forecast slider" |

## 5b. Verification of understanding

The brief says "3 route options". If the routing API offers fewer distinct routes, extra routes are forced
through offset waypoints (design in doc 04). If even that yields fewer than 3, fewer are shown. This is stated
so the owner can disagree.
