# 09 Security Audit

Outline: IEEE 1028 audit structure; checklist: OWASP Top 10 themes. Date 2026-10-20. Auditor: Danish Ahmed (self-audit, not independent).
Method: code reading, `pip-audit`, `npm audit`, `manage.py check --deploy`, header inspection with `curl -I`. No penetration test was run.

## 1. System facts

Public, unauthenticated, stateless JSON API (`POST /api/routes`, `GET /api/health`) plus static SPA. No database, no cookies,
no user accounts, no stored personal data. User-entered places and the load weight are processed in memory; place names
are sent to Nominatim, route coordinates to OSRM, checkpoint coordinates to Open-Meteo (privacy note for any public site).

## 2. Findings

| ID | Area | Finding | Risk | Status |
|---|---|---|---|---|
| S-01 | XSS | Third-party place names were inserted as HTML in map tooltips | Medium | Fixed: text node used |
| S-02 | Abuse | Endpoint fans out to three public APIs with no limit | Medium | Mitigated: 30 requests per 10 min per client address, per process. Behind a proxy all clients may share one address (shortcut noted in code); use a shared store or proxy-level limit for real traffic |
| S-03 | Information leak | Raw exception text shown to users | Low | Fixed: logged server-side, generic message |
| S-04 | Headers | No `X-Frame-Options` | Low | Fixed: DENY (verified by `curl -I`) |
| S-05 | CSRF | `@csrf_exempt` and no CSRF middleware | Low | Accepted: no cookies or session, so nothing for CSRF to abuse. `check --deploy` W003 remains |
| S-06 | Transport | HSTS include-subdomains and preload not set | Low | **Open, owner decision**: depends on the domain. `DJANGO_FORCE_HTTPS=1` enables redirect, 1-year HSTS and proxy header |
| S-07 | CSP | No Content-Security-Policy | Low | **Open**: would need allowing `tile.openstreetmap.org` images and Leaflet inline styles |
| S-08 | AuthN/AuthZ | None | Info | Accepted: public tool by design (assumption, owner to confirm) |
| S-09 | Secrets | `DJANGO_SECRET_KEY` required unless `DJANGO_DEBUG=1`; no secret in repo; `.env*` git-ignored | - | Pass (inspection) |
| S-10 | SSRF | Upstream URLs come only from environment variables, never from request data | - | Pass |
| S-11 | Input validation | Body must be JSON; load 0-150,000; departure window; interval whitelisted; NaN and infinity rejected | - | Pass (tests) |
| S-12 | Dependencies | Python 0 known vulnerabilities, npm 0 | - | Pass at 2026-10-20; re-run before release |
| S-13 | Supply chain | Exact pins plus lockfile for npm; pip pins exact, no hash pinning | Low | Accepted |
| S-14 | Debug | `DJANGO_DEBUG` defaults off | - | Pass |
| S-15 | Container | Image ran as root | Low | Fixed: runs as user `app` (UID 1000, verified). Image not scanned for CVEs |
| S-16 | Third-party terms | Public OSRM, Nominatim and Open-Meteo have usage limits and (Open-Meteo free tier) non-commercial terms | Medium for production | **Open**: from knowledge, not re-read today; verify before any commercial use |

## 3. Accepted risks need owner sign-off

S-05, S-08, S-13. Open items for the owner: S-06, S-07, S-15, S-16.
