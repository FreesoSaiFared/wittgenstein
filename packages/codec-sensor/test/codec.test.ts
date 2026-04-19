import { describe, expect, it } from "vitest";
import { sensorCodec } from "../src/index.js";

describe("@wittgenstein/codec-sensor", () => {
  it("exports the sensor codec contract", () => {
    expect(sensorCodec.name).toBe("sensor");
    expect(sensorCodec.parse("{}").ok).toBe(true);
  });
});
