# 11 Production Readiness Review

Basis: ISO/IEC/IEEE 12207 transition process (outline). Date 2026-10-20. Verdict at the end.

| Area | Check | Result |
|---|---|---|
| Build | Frontend build, typecheck, lint | Pass |
| Tests | 28 backend tests pass | Pass |
| Tests | Frontend automated tests | Pass for pure logic (12 Vitest); component and map rendering not covered |
| Tests | Test of upstream failure (502 path) | Pass at HTTP layer |
| Config | All settings from env; secret key required in production | Pass |
| Config | `.env` ignored by git | Pass |
| Security | Dependency audits, headers, input validation | Pass (doc 09) |
| Security | HSTS options, CSP | Open (owner/domain decisions); container is non-root |
| Observability | Console logging, `/api/health` | Pass |
| Observability | Metrics, error tracking, alerts | Not present |
| Packaging | Dockerfile (Node 24 build, Python 3.12, Gunicorn 2 workers x 8 threads, non-root, honours `$PORT`) | Pass: built and run locally, health, index and a live search OK |
| Packaging | Gunicorn on Linux | Pass (ran inside the container) |
| Deploy | Hosting target | PythonAnywhere free chosen; guide in doc 13; not deployed |
| Deploy | CI pipeline | Written (GitHub Actions: backend, frontend, docker build), **never run**; first run happens on push |
| Data | No database, nothing to back up or migrate | N/A |
| Accessibility | Labels on inputs, slider has aria-label; keyboard operation of slider and map not tested; colour is the only risk cue on map dots (popups and table also give text) | Partial |
| Responsive | 375 px empty state OK; with results not tested | Partial |
| Docs | README, SRS, SDD, test and audit docs | Pass |
| Known defects | D14 null weather | Fixed |
| Third-party | Public API limits and terms | Open (doc 09 S-16, doc 10) |

## Verdict

**Ready for a controlled demo and submission after the owner's decisions; not production-grade for public traffic.**
Blocking items for production: component tests, an image CVE scan,
self-hosted or paid routing/weather. Blocking items for the assessment: owner decisions Q1-Q3 in doc 02.
