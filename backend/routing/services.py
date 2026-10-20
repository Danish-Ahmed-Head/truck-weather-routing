"""Thin clients for the third-party APIs (OSRM routing, Nominatim geocoding, Open-Meteo weather)."""
import hashlib
import logging
import re
from datetime import UTC, datetime, timedelta

import requests
from django.conf import settings
from django.core.cache import cache

METERS_PER_MILE = 1609.344
TIMEOUT = 30
MM_PER_INCH = 25.4
CM_PER_INCH = 2.54
CHUNK = 40
WEATHER_TTL = 15 * 60  # seconds; the public Open-Meteo quota counts every location requested
logger = logging.getLogger(__name__)


class UpstreamError(Exception):
    """A third-party service failed or returned nothing usable."""


class LocationNotFound(Exception):
    pass


def _get(url, params, what):
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": settings.HTTP_USER_AGENT}, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("%s request failed: %s", what, exc)
        raise UpstreamError(f"{what} service is unavailable. Please try again shortly.") from exc


_LATLON = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")


def geocode(query):
    """Return {"name", "lat", "lon"} for a free-text place or a 'lat, lon' string."""
    query = (query or "").strip()
    if not query:
        raise LocationNotFound("Location is empty.")
    match = _LATLON.match(query)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        if abs(lat) <= 90 and abs(lon) <= 180:
            return {"name": f"{lat:.4f}, {lon:.4f}", "lat": lat, "lon": lon}

    key = "geocode:" + hashlib.sha1(query.lower().encode()).hexdigest()
    hit = cache.get(key)
    if hit:
        return hit
    data = _get(f"{settings.NOMINATIM_URL}/search", {"q": query, "format": "jsonv2", "limit": 1}, "Geocoding")
    if not data:
        raise LocationNotFound(f"Could not find a location for '{query}'.")
    result = {"name": data[0]["display_name"], "lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
    cache.set(key, result, 60 * 60 * 24)
    return result


def _osrm(coords, alternatives):
    path = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coords)
    return _get(
        f"{settings.OSRM_URL}/route/v1/driving/{path}",
        {"alternatives": "3" if alternatives else "false", "overview": "full", "geometries": "geojson", "steps": "true"},
        "Routing",
    )


def _parse_osrm_route(raw):
    # Name the route after the roads it spends the most distance on.
    by_road = {}
    for leg in raw.get("legs", []):
        for step in leg.get("steps", []):
            label = step.get("ref") or step.get("name")
            if label:
                label = label.split(";")[0]
                by_road[label] = by_road.get(label, 0.0) + step["distance"]
    top = sorted(by_road, key=by_road.get, reverse=True)[:3]
    return {
        "distance_mi": raw["distance"] / METERS_PER_MILE,
        "duration_h": raw["duration"] / 3600 * settings.TRUCK_TIME_FACTOR,
        "points": [(lat, lon) for lon, lat in raw["geometry"]["coordinates"]],
        "summary": "via " + ", ".join(top) if top else "via local roads",
    }


def fetch_routes(origin, destination):
    """Candidate routes from OSRM (the main route plus whatever alternatives it offers)."""
    data = _osrm([origin, destination], alternatives=True)
    if data.get("code") != "Ok" or not data.get("routes"):
        raise UpstreamError("No drivable route was found between those locations.")
    return [_parse_osrm_route(r) for r in data["routes"]]


def fetch_route_via(origin, via, destination):
    """One route forced through a waypoint; used to manufacture alternatives when OSRM offers too few."""
    try:
        data = _osrm([origin, via, destination], alternatives=False)
    except UpstreamError:
        return None
    if data.get("code") != "Ok" or not data.get("routes"):
        return None
    return _parse_osrm_route(data["routes"][0])


def round_key(lat, lon):
    return (round(lat, 2), round(lon, 2))


def fetch_weather(coords):
    """Hourly forecast per rounded (lat, lon).

    Returns {key: {"start": datetime(UTC), "wind": [mph], "rain": [in/hr], "snow": [in/hr]}}.
    Open-Meteo hourly rain+showers are mm over the previous hour (so mm/hr) and snowfall is cm of
    snow depth over the previous hour, which matches the brief's "in/hr" snow thresholds.
    """
    keys = sorted({round_key(lat, lon) for lat, lon in coords})
    out = {}
    missing = []
    for key in keys:
        hit = cache.get(_wx_cache_key(key))
        if hit:
            out[key] = hit
        else:
            missing.append(key)
    for i in range(0, len(missing), CHUNK):
        chunk = missing[i : i + CHUNK]
        data = _get(
            settings.OPEN_METEO_URL,
            {
                "latitude": ",".join(str(k[0]) for k in chunk),
                "longitude": ",".join(str(k[1]) for k in chunk),
                "hourly": "wind_speed_10m,rain,showers,snowfall",
                "wind_speed_unit": "mph",
                "timezone": "GMT",
                "past_days": 1,
                "forecast_days": 16,
            },
            "Weather",
        )
        if isinstance(data, dict):
            data = [data]
        if len(data) != len(chunk):
            raise UpstreamError("Weather service returned an unexpected response.")
        for key, loc in zip(chunk, data):
            hourly = loc["hourly"]
            # A null hour (None) means the forecast has no data there; the planner reports it as unknown.
            out[key] = {
                "start": datetime.fromisoformat(hourly["time"][0]).replace(tzinfo=UTC),
                "wind": hourly["wind_speed_10m"],
                "rain": [None if r is None or s is None else (r + s) / MM_PER_INCH
                         for r, s in zip(hourly["rain"], hourly["showers"])],
                "snow": [None if c is None else c / CM_PER_INCH for c in hourly["snowfall"]],
            }
            cache.set(_wx_cache_key(key), out[key], WEATHER_TTL)
    return out


def _wx_cache_key(key):
    return f"wx:{key[0]}:{key[1]}"


def hour_index(series, when):
    """Index of the hourly slot nearest `when`, clamped to the data. Second value flags clamping."""
    raw = round((when - series["start"]) / timedelta(hours=1))
    last = len(series["wind"]) - 1
    return max(0, min(last, raw)), (raw < 0 or raw > last)
