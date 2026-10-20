"""Weather risk classification for a single checkpoint.

Thresholds come from the assessment brief. Boundary choices (the brief's ranges overlap
at their edges, e.g. rain "0.10-0.25" and "0.25-0.50"):

* wind: lower bound inclusive (>=25 Moderate, >=35 High, >=45 Severe, >=55 No Travel)
* rain / snow: lower bound inclusive for Moderate, High and Severe; No Travel is strictly
  above the top of the Severe band (rain > 1.00 in/hr, snow > 3.0 in/hr), as written.
"""

LOW, MODERATE, HIGH, SEVERE, NO_TRAVEL = range(5)
LEVEL_LABELS = ["Low", "Moderate", "High", "Severe", "No Travel"]

# (moderate, high, severe, no_travel, no_travel_is_strict)
WIND = (25.0, 35.0, 45.0, 55.0, False)
RAIN = (0.10, 0.25, 0.50, 1.00, True)
SNOW = (0.5, 1.0, 2.0, 3.0, True)


def _classify(value, thresholds):
    moderate, high, severe, no_travel, strict = thresholds
    if (value > no_travel) if strict else (value >= no_travel):
        return NO_TRAVEL
    if value >= severe:
        return SEVERE
    if value >= high:
        return HIGH
    if value >= moderate:
        return MODERATE
    return LOW


def assess(wind_mph, rain_in_hr, snow_in_hr, load_lb):
    """Return {"level": int, "label": str, "drivers": [str]} for one checkpoint."""
    wind_level = _classify(wind_mph, WIND)
    rain_level = _classify(rain_in_hr, RAIN)
    snow_level = _classify(snow_in_hr, SNOW)
    level = max(wind_level, rain_level, snow_level)
    drivers = [
        f"{name} {LEVEL_LABELS[lv]}"
        for name, lv in (("wind", wind_level), ("rain", rain_level), ("snow", snow_level))
        if lv == level and lv > LOW
    ]

    # Load rules. Wind >= 55 is already No Travel for any load via the wind band above.
    if 45 <= wind_mph < 55 and load_lb > 30000:
        level = NO_TRAVEL
        drivers.append("wind 45-54 mph with load over 30,000 lb")
    elif 35 <= wind_mph < 45 and load_lb > 40000 and level < SEVERE:
        level = SEVERE
        drivers.append("wind 35-44 mph with load over 40,000 lb")

    return {"level": level, "label": LEVEL_LABELS[level], "drivers": drivers}
