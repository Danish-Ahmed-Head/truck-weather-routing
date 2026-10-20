from datetime import UTC, datetime, timedelta

from django.test import SimpleTestCase

from routing import geo, planner, views

DEPARTURE = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)
ORIGIN, DEST = (40.0, -100.0), (40.0, -97.0)


def route(lat, hours, summary, n=60):
    """A straight east-west route at `lat` spanning the same longitudes as ORIGIN..DEST."""
    pts = [(lat, -100.0 + 3.0 * i / (n - 1)) for i in range(n)]
    return {"points": pts, "distance_mi": geo.cumulative_miles(pts)[-1], "duration_h": hours, "summary": summary}


def weather_by_lat(wind_for_lat):
    """Fake forecast: constant wind per latitude, no precipitation."""
    def fetch(coords):
        out = {}
        for lat, lon in coords:
            key = (round(lat, 2), round(lon, 2))
            out[key] = {
                "start": DEPARTURE - timedelta(hours=24),
                "wind": [wind_for_lat(key[0])] * 200,
                "rain": [0.0] * 200,
                "snow": [0.0] * 200,
            }
        return out
    return fetch


def deps(routes, wind_for_lat):
    return {
        "fetch_routes": lambda o, d: routes,
        "fetch_route_via": lambda o, v, d: None,
        "fetch_weather": weather_by_lat(wind_for_lat),
    }


def calm_north(lat):
    return 50 if lat < 40.5 else 5  # the lat-40 route is Severe throughout for an empty load


class Recommendation(SimpleTestCase):
    def test_prefers_calm_route_even_when_slower(self):
        routes = [route(40.0, 3.0, "via I-80"), route(41.0, 4.0, "via US-30"), route(42.0, 5.0, "via US-20")]
        result = planner.plan(ORIGIN, DEST, DEPARTURE, 10000, 10, deps(routes, calm_north))
        best = next(r for r in result if r["recommended"])
        self.assertEqual(best["id"], "B")  # calm and faster than C
        self.assertEqual(next(r for r in result if r["id"] == "A")["rank"], 3)
        self.assertIn("Severe", best["reason"])

    def test_same_weather_picks_fastest(self):
        routes = [route(40.0, 5.0, "slow"), route(41.0, 3.0, "fast"), route(42.0, 4.0, "mid")]
        result = planner.plan(ORIGIN, DEST, DEPARTURE, 10000, 10, deps(routes, lambda lat: 5))
        self.assertEqual(next(r for r in result if r["recommended"])["id"], "B")

    def test_load_changes_the_risk_of_the_same_weather(self):
        routes = [route(40.0, 3.0, "only")]
        light = planner.plan(ORIGIN, DEST, DEPARTURE, 20000, 10, deps(routes, lambda lat: 50))[0]
        heavy = planner.plan(ORIGIN, DEST, DEPARTURE, 35000, 10, deps(routes, lambda lat: 50))[0]
        self.assertEqual(light["stats"]["max_level"], 3)
        self.assertEqual(heavy["stats"]["max_level"], 4)
        self.assertGreater(heavy["stats"]["no_travel_miles"], 0)

    def test_fills_to_three_routes_with_waypoint_alternatives(self):
        extra = iter([route(41.0, 4.0, "via A"), route(42.0, 5.0, "via B"), route(43.0, 6.0, "via C")])
        d = deps([route(40.0, 3.0, "main")], lambda lat: 5)
        d["fetch_route_via"] = lambda o, v, dest: next(extra)
        self.assertEqual(len(planner.plan(ORIGIN, DEST, DEPARTURE, 10000, 10, d)), 3)

    def test_duplicate_alternatives_are_dropped(self):
        d = deps([route(40.0, 3.0, "main"), route(40.0, 3.1, "same road")], lambda lat: 5)
        self.assertEqual(len(planner.plan(ORIGIN, DEST, DEPARTURE, 10000, 10, d)), 1)


class Checkpoints(SimpleTestCase):
    def test_interval_choice(self):
        self.assertEqual(planner.pick_interval(100, "auto"), 10)
        self.assertEqual(planner.pick_interval(300, "auto"), 25)
        self.assertEqual(planner.pick_interval(900, "auto"), 50)
        self.assertEqual(planner.pick_interval(900, 25), 25)

    def test_checkpoints_span_whole_route(self):
        miles = planner.checkpoint_miles(103.0, 25)
        self.assertEqual(miles, [0.0, 25.0, 50.0, 75.0, 103.0])

    def test_segment_miles_sum_to_route_length(self):
        miles = planner.checkpoint_miles(137.0, 25)
        self.assertAlmostEqual(sum(planner._segments(miles)), 137.0)

    def test_etas_increase_and_end_at_arrival(self):
        result = planner.plan(ORIGIN, DEST, DEPARTURE, 10000, 25, deps([route(40.0, 4.0, "x")], lambda lat: 5))[0]
        etas = [c["eta"] for c in result["checkpoints"]]
        self.assertEqual(etas, sorted(etas))
        self.assertEqual(etas[0], DEPARTURE.isoformat())
        self.assertEqual(etas[-1], (DEPARTURE + timedelta(hours=4)).isoformat())
        self.assertEqual(len(result["checkpoints"][0]["forecast"]), 49)

    def test_weather_is_sampled_at_eta_not_departure(self):
        # Wind rises 10 mph every hour from departure; a later ETA must see stronger wind.
        def fetch(coords):
            return {
                (round(la, 2), round(lo, 2)): {
                    "start": DEPARTURE,
                    "wind": [10.0 * h for h in range(200)],
                    "rain": [0.0] * 200,
                    "snow": [0.0] * 200,
                }
                for la, lo in coords
            }
        d = deps([route(40.0, 4.0, "x")], lambda lat: 0)
        d["fetch_weather"] = fetch
        cps = planner.plan(ORIGIN, DEST, DEPARTURE, 0, 25, d)[0]["checkpoints"]
        self.assertEqual(cps[0]["wind_mph"], 0.0)
        self.assertEqual(cps[-1]["wind_mph"], 40.0)


class RequestValidation(SimpleTestCase):
    def test_rejects_bad_input(self):
        good = {"origin": "A", "destination": "B", "departure": DEPARTURE.isoformat(), "load_lb": 30000}
        views.parse_request(good, DEPARTURE)
        for patch in ({"origin": ""}, {"load_lb": "heavy"}, {"load_lb": -1},
                      {"departure": "nope"}, {"departure": (DEPARTURE + timedelta(days=30)).isoformat()}):
            with self.assertRaises(views.BadRequest):
                views.parse_request({**good, **patch}, DEPARTURE)
