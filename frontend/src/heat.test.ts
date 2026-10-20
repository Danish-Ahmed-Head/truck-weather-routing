import { describe, expect, it } from "vitest";
import { buildSamples, sampleLevels } from "./heat";
import type { Checkpoint, Route } from "./types";

const cp = (mile: number, forecast: number[]): Checkpoint => ({
  mile,
  lat: 40,
  lon: -100 + mile / 100,
  eta: "2026-10-21T12:00:00+00:00",
  level: 0,
  label: "Low",
  drivers: [],
  wind_mph: 5,
  rain_in_hr: 0,
  snow_in_hr: 0,
  forecast_beyond_range: false,
  unknown: false,
  forecast,
});

const route = (checkpoints: Checkpoint[]) => ({ id: "A", checkpoints }) as unknown as Route;

describe("buildSamples", () => {
  it("places a sample about every 3 miles along each checkpoint gap, plus the end", () => {
    const samples = buildSamples([route([cp(0, [0]), cp(10, [0]), cp(20, [0])])]);
    expect(samples).toHaveLength(4 + 4 + 1); // ceil(10 / 3) = 4 per gap
    expect(samples[0].lon).toBeCloseTo(-100);
    expect(samples[samples.length - 1].lon).toBeCloseTo(-99.8);
  });

  it("keeps routes separate", () => {
    const a = route([cp(0, [0]), cp(10, [0])]);
    const b = route([cp(0, [0]), cp(10, [0])]);
    const samples = buildSamples([a, b]);
    expect(samples.filter((s) => s.route === a)).toHaveLength(5);
    expect(samples.filter((s) => s.route === b)).toHaveLength(5);
  });
});

describe("sampleLevels", () => {
  const samples = buildSamples([route([cp(0, [0, 2]), cp(10, [2, 2]), cp(20, [-1, 2])])]);

  it("blends the level between neighbouring checkpoints", () => {
    const levels = sampleLevels(samples, 0);
    expect(levels[0]).toBe(0); // at checkpoint 0
    expect(levels[2]).toBeCloseTo(1); // halfway between level 0 and level 2 (steps = 4)
  });

  it("marks samples unknown when either neighbouring checkpoint has no data at that hour", () => {
    const levels = sampleLevels(samples, 0);
    expect(levels.slice(4, -1).every((l) => l === -1)).toBe(true);
    expect(levels[samples.length - 1]).toBe(-1);
  });

  it("reads the requested hour", () => {
    expect(sampleLevels(samples, 1).every((l) => l === 2)).toBe(true);
  });
});
