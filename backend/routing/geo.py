import math
from itertools import pairwise

EARTH_RADIUS_MI = 3958.8


def haversine_mi(a, b):
    """Great-circle distance in miles between two (lat, lon) points."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_MI * math.asin(math.sqrt(h))


def cumulative_miles(points):
    """Running distance (miles) at each point of a polyline of (lat, lon)."""
    out = [0.0]
    for prev, cur in pairwise(points):
        out.append(out[-1] + haversine_mi(prev, cur))
    return out


def point_at(points, cumulative, mile):
    """Interpolate the (lat, lon) located `mile` miles along the polyline."""
    if mile <= 0:
        return points[0]
    if mile >= cumulative[-1]:
        return points[-1]
    lo, hi = 0, len(cumulative) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if cumulative[mid] <= mile:
            lo = mid
        else:
            hi = mid
    span = cumulative[hi] - cumulative[lo]
    t = (mile - cumulative[lo]) / span if span else 0.0
    return (
        points[lo][0] + (points[hi][0] - points[lo][0]) * t,
        points[lo][1] + (points[hi][1] - points[lo][1]) * t,
    )


def thin(points, max_points):
    """Evenly thin a polyline for display, always keeping the last point."""
    if len(points) <= max_points:
        return points
    step = len(points) / max_points
    out = [points[int(i * step)] for i in range(max_points)]
    out[-1] = points[-1]
    return out
