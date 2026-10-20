# 02 Project Management Plan

Basis: ISO/IEC/IEEE 16326:2019 (confirmed current). Version 1.0, 2026-10-20.

## 1. Purpose and scope

Deliver a React + Django web app that recommends the safest of three truck routes from weather, load weight and
travel time, per the "Weather-Aware Truck Routing" assessment brief. Deliverables required by the brief: GitHub
repository, hosted application, 5-10 minute Loom walkthrough. Additional deliverable requested by the owner:
this documentation set.

Out of scope: building a routing engine, user accounts, payments, truck-specific routing restrictions.

## 2. Constraints and deadline

- Brief: at most 4 days and 16 work hours. The email gives no calendar deadline; if the 4 days run from receipt
  (2026-10-19) they end about 2026-10-23. **Unconfirmed; owner to check.**
- Evaluation weights: 40% route/weather/risk/recommendation logic, 40% UI/map/heatmap, 15% code quality, 5% docs and walkthrough.

## 3. Work breakdown and status

Iteration 1 (initial build, no formal process) and Iteration 2 (process retrofit, review, fixes) are recorded.
Status: Done = built, tested, run, verified.

| ID | Task | Iter | Status |
|---|---|---|---|
| T01 | Risk classification rules and load rules | 1 | Done (8 tests) |
| T02 | External clients: geocode, route, weather | 1 | Done, live-checked |
| T03 | Checkpoint placement, ETA, weather at ETA | 1 | Done (5 tests) |
| T04 | Route ranking and recommendation reason | 1,2 | Done (reason wording fixed in loop) |
| T05 | Three-route guarantee (alternatives plus waypoint fill) | 1 | Done (2 tests) |
| T06 | API endpoint and input validation | 1,2 | Done (6 tests) |
| T07 | Map UI: routes, checkpoints, popups, route list | 1 | Done, browser-verified |
| T08 | Weather heatmap with 0-48 h slider | 1,2 | Done after redesign (see doc 06 D03) |
| T09 | Upgrade to latest stable stack | 2 | Done |
| T10 | Line-by-line review and defect fixes | 2 | Done, residual items in doc 08 |
| T11 | Security, scalability, performance audits | 2 | Done, see docs 09, 10 |
| T12 | Docs set (this set) | 2 | Done |
| T13 | Frontend automated tests | - | **Not done** (gap, doc 11) |
| T14 | CI pipeline | - | **Not done**, not requested |
| T15 | Docker image build verified | 2 | Done 2026-10-20: built with Docker 29.6.1, run with `PORT=9000` as non-root, gunicorn on Linux, 3 routes returned |
| T16 | GitHub repo, hosting, Loom, submission | - | **Not started, needs owner approval** |

## 4. Effort

Actual hours were not measured. The 16-hour limit applies to the owner's submission; the owner should judge
how this work counts against it.

## 5. Risks

| ID | Risk | Likelihood | Impact | Response |
|---|---|---|---|---|
| R1 | Public OSRM/Nominatim/Open-Meteo throttle or go down | Medium | High | Env-var URLs for own instances; error 502 with clear message; 15-min weather cache |
| R2 | Calm weather during demo hides the risk colours | High | Medium | Pick a date/place with weather, or demo via unit tests |
| R3 | Rule boundaries misread (ranges overlap in brief) | Medium | High | Choices written in SRS A-01; owner to confirm |
| R4 | Deadline passes before submission | Medium | High | Owner confirms the deadline with the assessor |
| R5 | Hosting not chosen | High | High | Owner decision needed (open question Q1) |

## 5b. Open questions for the owner (nothing here is assumed)

Q1 hosting target (Coolify on your Contabo server, other, or free tier). Q2 repo visibility (private with invite
or public) and which account. Q3 exact deadline. Q4 confirm rule-boundary choices (SRS A-01..A-06). Q5 whether to
add CI and frontend tests before submission. Q6 domain name, which decides HSTS settings.

## 6. Tools and versions (checked 2026-10-20 against PyPI, npm and endoflife.date)

| Component | Version used | Latest checked | Note |
|---|---|---|---|
| Python | 3.12.x (installed) | 3.14.8 | 3.14 not installed; 3.12 is supported to Oct 2028 and meets Django 6.1 |
| Django | 6.1.2 | 6.1.2 | 5.2 is the LTS line (to Apr 2028); 6.1 is non-LTS, supported to Dec 2027 |
| requests / whitenoise / gunicorn | 2.34.2 / 6.12.0 / 26.2.0 | same | |
| Node | 24.15.0 (installed) | 24.22.0 (24 LTS), 26 | patch behind; Docker uses node:24 |
| React / react-dom | 19.3.1 | 19.3.1 | |
| Vite / plugin-react | 8.3.4 / 6.1.2 | same | |
| TypeScript | 7.0.2 | 7.0.2 | |
| Leaflet | 1.9.4 | 1.9.4 | |
| ruff, pip-audit | installed in venv, dev only | - | not in requirements.txt |

## 7. Quality, configuration, communication

Quality: see [01](01-SDLC-Process-Description.md) loop and definition of done. Configuration: git, exact pins.
Communication: the owner is asked before any push, deploy, send or submit.
