import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase

from routing import services, views

from .test_planner import deps, route

FAKE_PLACES = {"Denver": {"name": "Denver", "lat": 40.0, "lon": -100.0}, "Omaha": {"name": "Omaha", "lat": 40.0, "lon": -97.0}}


def post(client, **overrides):
    body = {
        "origin": "Denver",
        "destination": "Omaha",
        "departure": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
        "load_lb": 30000,
        **overrides,
    }
    return client.post("/api/routes", json.dumps(body), content_type="application/json")


@patch("routing.services.geocode", side_effect=lambda q: FAKE_PLACES[q])
class RoutesEndpoint(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_returns_ranked_routes(self, _geocode):
        fake = deps([route(40.0, 3.0, "main")], lambda lat: 5)
        with patch.object(views, "default_deps", return_value=fake):
            resp = post(self.client)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["origin"]["name"], "Denver")
        self.assertTrue(body["routes"][0]["recommended"])

    def test_same_place_is_rejected(self, _geocode):
        resp = post(self.client, destination="Denver")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("same place", resp.json()["error"])

    def test_bad_json_and_bad_fields_are_400(self, _geocode):
        self.assertEqual(self.client.post("/api/routes", "{", content_type="application/json").status_code, 400)
        self.assertEqual(post(self.client, load_lb="abc").status_code, 400)

    def test_get_is_not_allowed(self, _geocode):
        self.assertEqual(self.client.get("/api/routes").status_code, 405)

    def test_rate_limit_returns_429(self, _geocode):
        with patch.object(views, "RATE_LIMIT", 2):
            codes = [post(self.client, load_lb="abc").status_code for _ in range(3)]
        self.assertEqual(codes, [400, 400, 429])

    def test_upstream_failure_is_502_with_generic_message(self, _geocode):
        with patch.object(views.planner, "plan", side_effect=services.UpstreamError("Routing service is unavailable.")):
            resp = post(self.client)
        self.assertEqual(resp.status_code, 502)
        self.assertIn("unavailable", resp.json()["error"])


class SecurityHeaders(SimpleTestCase):
    def test_referrer_policy_lets_map_tiles_load(self):
        # OpenStreetMap blocks tile requests that carry no Referer.
        resp = self.client.get("/api/health")
        self.assertEqual(resp["Referrer-Policy"], "strict-origin-when-cross-origin")
