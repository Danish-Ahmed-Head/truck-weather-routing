import json
from datetime import UTC, datetime, timedelta

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import geo, planner, services

MAX_LOAD_LB = 150000
MAX_DAYS_AHEAD = 12  # Open-Meteo forecasts 16 days; leave room for multi-day trips
MIN_TRIP_MILES = 1.0
# Each request fans out to three public APIs, so cap how often one client can trigger that.
RATE_LIMIT, RATE_WINDOW = 30, 600  # requests per client per window (seconds)


class BadRequest(Exception):
    pass


def default_deps():
    return {
        "fetch_routes": services.fetch_routes,
        "fetch_route_via": services.fetch_route_via,
        "fetch_weather": services.fetch_weather,
    }


def parse_request(body, now=None):
    now = now or datetime.now(UTC)
    origin = str(body.get("origin", "")).strip()
    destination = str(body.get("destination", "")).strip()
    if not origin or not destination:
        raise BadRequest("Origin and destination are required.")

    try:
        departure = datetime.fromisoformat(str(body.get("departure", "")))
    except ValueError:
        raise BadRequest("Departure must be an ISO date/time.") from None
    if departure.tzinfo is None:
        departure = departure.replace(tzinfo=UTC)
    departure = departure.astimezone(UTC)
    if departure < now - timedelta(hours=24) or departure > now + timedelta(days=MAX_DAYS_AHEAD):
        raise BadRequest(f"Departure must be within the forecast window (yesterday to {MAX_DAYS_AHEAD} days ahead).")

    try:
        load_lb = float(body.get("load_lb"))
    except (TypeError, ValueError):
        raise BadRequest("Load weight must be a number (lb).") from None
    if not 0 <= load_lb <= MAX_LOAD_LB:
        raise BadRequest(f"Load weight must be between 0 and {MAX_LOAD_LB:,} lb.")

    interval = body.get("interval", "auto")
    interval = int(interval) if str(interval) in ("10", "25", "50") else "auto"
    return origin, destination, departure, load_lb, interval


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


def rate_limited(request):
    # shortcut: keyed on REMOTE_ADDR and per process; behind a proxy all clients share one key, upgrade to a shared store.
    key = "rl:" + request.META.get("REMOTE_ADDR", "?")
    cache.add(key, 0, RATE_WINDOW)
    return cache.incr(key) > RATE_LIMIT


@csrf_exempt
@require_POST
def routes(request):
    if rate_limited(request):
        return JsonResponse({"error": "Too many requests. Please wait a few minutes."}, status=429)
    try:
        body = json.loads(request.body or b"{}")
        origin_text, dest_text, departure, load_lb, interval = parse_request(body)
        origin = services.geocode(origin_text)
        destination = services.geocode(dest_text)
        if geo.haversine_mi((origin["lat"], origin["lon"]), (destination["lat"], destination["lon"])) < MIN_TRIP_MILES:
            raise BadRequest("Origin and destination are the same place.")
        result = planner.plan(
            (origin["lat"], origin["lon"]),
            (destination["lat"], destination["lon"]),
            departure,
            load_lb,
            interval,
            default_deps(),
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Request body must be JSON."}, status=400)
    except (BadRequest, services.LocationNotFound) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except services.UpstreamError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({
        "origin": origin,
        "destination": destination,
        "departure": departure.isoformat(),
        "load_lb": load_lb,
        "routes": result,
    })
