"""Builds weather-risk-scored route options and picks the recommended one."""
import math
from datetime import timedelta

from . import geo, risk
from .services import hour_index, round_key

FORECAST_HOURS = 48
TARGET_ROUTES = 3
SIMILAR_ROUTE_OVERLAP = 0.85
DISPLAY_POINTS = 1500
MILE_BUCKET = 5  # miles within the same bucket count as a tie when ranking
RISK_BUCKET = 0.1


def pick_interval(total_miles, requested):
    """Checkpoint spacing in miles: the caller's 10/25/50, or by trip length when 'auto'."""
    if requested in (10, 25, 50):
        return requested
    if total_miles < 150:
        return 10
    if total_miles < 500:
        return 25
    return 50


def checkpoint_miles(total, interval):
    miles = [0.0]
    m = interval
    while m < total - interval / 2:
        miles.append(float(m))
        m += interval
    miles.append(total)
    return miles


def _segments(miles):
    """Miles of road each checkpoint is responsible for (split halfway to its neighbours)."""
    out = []
    for i, m in enumerate(miles):
        lo = (miles[i - 1] + m) / 2 if i > 0 else 0.0
        hi = (m + miles[i + 1]) / 2 if i < len(miles) - 1 else miles[-1]
        out.append(hi - lo)
    return out


def _overlap(candidate, existing):
    """Share of `candidate` that lies within ~1 mile of `existing` (both thinned polylines)."""
    cand = geo.thin(candidate, 25)
    near = sum(1 for p in cand if any(geo.haversine_mi(p, q) < 1.0 for q in existing))
    return near / len(cand)


def _distinct(route, kept):
    return all(
        _overlap(route["points"], geo.thin(k["points"], DISPLAY_POINTS)) < SIMILAR_ROUTE_OVERLAP for k in kept
    )


def _via_points(origin, destination):
    """Waypoints pushed sideways from the midpoint, used to coax out extra alternatives."""
    mid_lat, mid_lon = (origin[0] + destination[0]) / 2, (origin[1] + destination[1]) / 2
    scale = math.cos(math.radians(mid_lat)) or 1.0
    d_lat = destination[0] - origin[0]
    d_lon = (destination[1] - origin[1]) * scale  # degrees of lat-equivalent
    length = math.hypot(d_lat, d_lon) or 1.0
    perp_lat, perp_lon = -d_lon / length, d_lat / length
    for frac in (0.15, -0.15, 0.3, -0.3):
        yield (mid_lat + perp_lat * frac * length, mid_lon + perp_lon * frac * length / scale)


def gather_routes(origin, destination, fetch_routes, fetch_route_via):
    """Up to three distinct routes: OSRM alternatives first, then waypoint-forced ones."""
    kept = []
    for route in fetch_routes(origin, destination):
        if len(kept) < TARGET_ROUTES and _distinct(route, kept):
            kept.append(route)
    for via in _via_points(origin, destination):
        if len(kept) >= TARGET_ROUTES:
            break
        route = fetch_route_via(origin, via, destination)
        if route and _distinct(route, kept):
            kept.append(route)
    return kept


def _checkpoint_plan(route, requested_interval):
    cumulative = geo.cumulative_miles(route["points"])
    # Trust OSRM's distance over our haversine sum, and map back to the polyline with this scale.
    scale = route["distance_mi"] / cumulative[-1] if cumulative[-1] else 1.0
    interval = pick_interval(route["distance_mi"], requested_interval)
    miles = checkpoint_miles(route["distance_mi"], interval)
    locations = [geo.point_at(route["points"], cumulative, m / scale) for m in miles]
    return interval, miles, locations


def build_route(route, departure, load_lb, requested_interval, weather):
    total = route["distance_mi"]
    interval, miles, locations = _checkpoint_plan(route, requested_interval)
    segments = _segments(miles)

    checkpoints = []
    miles_at_level = [0.0] * 5
    weighted = 0.0
    for m, seg, (lat, lon) in zip(miles, segments, locations):
        eta = departure + timedelta(hours=route["duration_h"] * (m / total if total else 0))
        series = weather[round_key(lat, lon)]
        idx, clamped = hour_index(series, eta)
        result = risk.assess(series["wind"][idx], series["rain"][idx], series["snow"][idx], load_lb)

        # Heatmap strip: risk at this spot for each hour 0..48 after departure (fixed clock, not ETA).
        start, _ = hour_index(series, departure)
        last = len(series["wind"]) - 1
        strip = []
        for h in range(FORECAST_HOURS + 1):
            j = min(last, start + h)
            strip.append(risk.assess(series["wind"][j], series["rain"][j], series["snow"][j], load_lb)["level"])

        miles_at_level[result["level"]] += seg
        weighted += result["level"] * seg
        checkpoints.append({
            "mile": round(m, 1),
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "eta": eta.isoformat(),
            "level": result["level"],
            "label": result["label"],
            "drivers": result["drivers"],
            "wind_mph": round(series["wind"][idx], 1),
            "rain_in_hr": round(series["rain"][idx], 2),
            "snow_in_hr": round(series["snow"][idx], 2),
            "forecast_beyond_range": clamped,
            "forecast": strip,
        })

    stats = {
        "no_travel_miles": round(miles_at_level[risk.NO_TRAVEL], 1),
        "severe_miles": round(miles_at_level[risk.SEVERE], 1),
        "high_miles": round(miles_at_level[risk.HIGH], 1),
        "moderate_miles": round(miles_at_level[risk.MODERATE], 1),
        "low_miles": round(miles_at_level[risk.LOW], 1),
        "avg_risk": round(weighted / total, 2) if total else 0.0,
        "max_level": max(c["level"] for c in checkpoints),
    }
    return {
        "distance_mi": round(total, 1),
        "duration_h": round(route["duration_h"], 2),
        "arrival": (departure + timedelta(hours=route["duration_h"])).isoformat(),
        "summary": route["summary"],
        "interval_mi": interval,
        "stats": stats,
        "checkpoints": checkpoints,
        "geometry": [[round(a, 5), round(b, 5)] for a, b in geo.thin(route["points"], DISPLAY_POINTS)],
    }


def rank_key(r):
    """No Travel miles, then Severe, then High miles, lowest average risk, shortest time.

    Mileage and risk are bucketed so a 1-mile difference does not outweigh a much faster route.
    """
    s = r["stats"]
    return (
        round(s["no_travel_miles"] / MILE_BUCKET),
        round(s["severe_miles"] / MILE_BUCKET),
        round(s["high_miles"] / MILE_BUCKET),
        round(s["avg_risk"] / RISK_BUCKET),
        r["duration_h"],
    )


def _reason(best, others):
    s = best["stats"]
    if not others:
        return "Only one distinct route was found."
    if s["no_travel_miles"] > 0 and all(o["stats"]["no_travel_miles"] > 0 for o in others):
        return "Every route crosses No Travel weather; this one has the least of it. Consider delaying departure."
    for field, label in (("no_travel_miles", "No Travel"), ("severe_miles", "Severe"), ("high_miles", "High")):
        worst = max(others, key=lambda o: o["stats"][field])
        if round(s[field] / MILE_BUCKET) < round(worst["stats"][field] / MILE_BUCKET):
            return (f"Fewest {label}-risk miles: {s[field]:g} vs up to {worst['stats'][field]:g} "
                    f"on {worst['name']}.")
    worst = max(others, key=lambda o: o["stats"]["avg_risk"])
    if round(s["avg_risk"] / RISK_BUCKET) < round(worst["stats"]["avg_risk"] / RISK_BUCKET):
        return f"Lowest average weather risk: {s['avg_risk']:g} vs up to {worst['stats']['avg_risk']:g}."
    return "Weather risk is equivalent across routes, so the shortest travel time wins."


def plan(origin, destination, departure, load_lb, interval, deps):
    """deps supplies fetch_routes, fetch_route_via and fetch_weather (injected so tests can fake them)."""
    routes = gather_routes(origin, destination, deps["fetch_routes"], deps["fetch_route_via"])
    coords = [loc for r in routes for loc in _checkpoint_plan(r, interval)[2]]
    weather = deps["fetch_weather"](coords)

    built = [build_route(r, departure, load_lb, interval, weather) for r in routes]
    for letter, r in zip("ABCDEF", built):
        r["id"] = letter
        r["name"] = f"Route {letter}"
    ranked = sorted(built, key=rank_key)
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
        r["recommended"] = i == 0
    ranked[0]["reason"] = _reason(ranked[0], ranked[1:])
    return built
