from django.test import SimpleTestCase

from routing.risk import HIGH, LOW, MODERATE, NO_TRAVEL, SEVERE, assess


def level(wind=0, rain=0, snow=0, load=10000):
    return assess(wind, rain, snow, load)["level"]


class WindBands(SimpleTestCase):
    def test_bands(self):
        self.assertEqual(level(wind=24.9), LOW)
        self.assertEqual(level(wind=25), MODERATE)
        self.assertEqual(level(wind=34.9), MODERATE)
        self.assertEqual(level(wind=35), HIGH)
        self.assertEqual(level(wind=45), SEVERE)
        self.assertEqual(level(wind=54.9, load=0), SEVERE)
        self.assertEqual(level(wind=55, load=0), NO_TRAVEL)


class RainAndSnowBands(SimpleTestCase):
    def test_rain(self):
        self.assertEqual(level(rain=0.09), LOW)
        self.assertEqual(level(rain=0.10), MODERATE)
        self.assertEqual(level(rain=0.25), HIGH)
        self.assertEqual(level(rain=0.50), SEVERE)
        self.assertEqual(level(rain=1.00), SEVERE)
        self.assertEqual(level(rain=1.01), NO_TRAVEL)

    def test_snow(self):
        self.assertEqual(level(snow=0.49), LOW)
        self.assertEqual(level(snow=0.5), MODERATE)
        self.assertEqual(level(snow=1.0), HIGH)
        self.assertEqual(level(snow=2.0), SEVERE)
        self.assertEqual(level(snow=3.0), SEVERE)
        self.assertEqual(level(snow=3.01), NO_TRAVEL)

    def test_worst_condition_wins(self):
        self.assertEqual(level(wind=26, rain=0.6, snow=0.1), SEVERE)


class LoadRules(SimpleTestCase):
    def test_heavy_load_in_severe_wind_is_no_travel(self):
        self.assertEqual(level(wind=50, load=30000), SEVERE)
        self.assertEqual(level(wind=50, load=30001), NO_TRAVEL)
        self.assertEqual(level(wind=45, load=35000), NO_TRAVEL)

    def test_very_heavy_load_in_high_wind_is_severe(self):
        self.assertEqual(level(wind=40, load=40000), HIGH)
        self.assertEqual(level(wind=40, load=40001), SEVERE)

    def test_load_rule_never_lowers_a_level(self):
        self.assertEqual(level(wind=40, rain=2.0, load=45000), NO_TRAVEL)

    def test_no_travel_wind_applies_to_any_load(self):
        self.assertEqual(level(wind=60, load=0), NO_TRAVEL)
