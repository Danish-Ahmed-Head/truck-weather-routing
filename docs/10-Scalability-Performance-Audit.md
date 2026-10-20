# 10 Scalability and Performance Audit

Outline: IEEE 1028 audit structure. Date 2026-10-20. Measured on a Windows 11 laptop against the live public APIs and with the planner alone.

## 1. Measurements

| Measure | Value | How |
|---|---|---|
| Denver to Omaha, end to end (first run, cold) | 9.5 s | Django test client, live APIs |
| Los Angeles to New York, end to end | 12.1 s, 169 KB, 3 routes, 57-62 checkpoints | same |
| Planner CPU alone, 3 routes x 30,000 points | 267 ms, 169 KB | synthetic benchmark with fake weather |
| Frontend bundle | 379.5 kB JS (115.6 kB gzip), 18.3 kB CSS | `vite build` |
| Test suite | 25 tests in about 0.1 s | `manage.py test` |
| Slider redraw time | **Not measured** numerically; design restyles existing segments (about 930 per 2,800 mi route set) without creating layers | - |

Conclusion: server CPU is not the bottleneck. Wall time is dominated by the public APIs (geocode x2, OSRM, up to 4
extra OSRM calls, Open-Meteo in chunks of 40 locations).

## 2. Scalability analysis

| Topic | Finding | Rating |
|---|---|---|
| State | Stateless; no database. Can run several instances | Good |
| Caches | In-process (per worker). Warm-up is repeated per worker; no sharing | Acceptable now |
| Concurrency | Gunicorn 2 workers x 8 threads = 16 requests in flight. If each holds a thread about 10 s, capacity is about 1.6 requests per second. **Estimate, not load-tested** | Low |
| Upstream quota | Open-Meteo counts each location. A 2,800-mile search sends up to about 180 locations. Free-tier daily limits (from knowledge, not verified today) would allow only dozens of long searches per day without the cache | Main limit |
| Upstream etiquette | Nominatim allows about 1 request per second; public OSRM is a demo server | Risk for real traffic |
| Request timeouts | Each upstream call times out at 30 s; Gunicorn timeout is 120 s. A worst case chain of calls can exceed that | Open |
| Payload | 169 KB for the longest route, no compression configured | Fine; enable gzip at the proxy |
| Memory | Weather cached as Python lists of 384 floats x 3 per location; 1,000 locations is a few tens of MB | Fine |

## 3. Recommendations (not implemented, need owner priority)

1. Self-host OSRM and Nominatim, or use paid tiers, before real traffic. 2. Add a shared cache (Redis) for weather and geocodes.
3. Put a total time budget on one request and fail fast. 4. Run a load test with recorded upstream responses.
5. Measure slider redraw in a real browser profile on a mid-range laptop. 6. Compress responses at the proxy.

## 4. Verdict

Adequate for an assessment demo and light use. Not sized for public production traffic without items 1-3.
