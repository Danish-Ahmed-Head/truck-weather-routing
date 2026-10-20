import { describe, expect, it } from "vitest";
import { UNKNOWN_COLOR, checkpointColor, fmtDuration, fmtNum, levelColor } from "./risk";

describe("levelColor", () => {
  it("returns the exact level colours at whole levels", () => {
    expect(levelColor(0)).toBe("rgb(46,158,91)");
    expect(levelColor(4)).toBe("rgb(91,26,110)");
  });

  it("blends halfway between neighbouring levels", () => {
    expect(levelColor(0.5)).toBe("rgb(135,169,46)"); // midpoint of Low green and Moderate yellow
  });

  it("does not overflow above the top level", () => {
    expect(levelColor(4.4)).toBe(levelColor(4));
  });

  it("uses grey for unknown", () => {
    expect(levelColor(-1)).toBe(UNKNOWN_COLOR);
  });
});

describe("checkpointColor", () => {
  it("is grey for a checkpoint with no data and the level colour otherwise", () => {
    expect(checkpointColor({ level: 0, unknown: true })).toBe(UNKNOWN_COLOR);
    expect(checkpointColor({ level: 3, unknown: false })).toBe("#d62828");
  });
});

describe("formatting", () => {
  it("formats durations and carries rounded minutes", () => {
    expect(fmtDuration(10.5)).toBe("10h 30m");
    expect(fmtDuration(0)).toBe("0h 00m");
    expect(fmtDuration(1.9999)).toBe("2h 00m");
  });

  it("shows a dash for missing numbers but keeps zero", () => {
    expect(fmtNum(null)).toBe("-");
    expect(fmtNum(0)).toBe("0");
    expect(fmtNum(12.5)).toBe("12.5");
  });
});
