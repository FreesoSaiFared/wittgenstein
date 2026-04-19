import { describe, expect, it } from "vitest";
import { imageCodec } from "../src/index.js";

describe("@wittgenstein/codec-image", () => {
  it("exposes the locked image codec skeleton", () => {
    expect(imageCodec.name).toBe("image");
    expect(imageCodec.modality).toBe("image");
    expect(imageCodec.parse("{}").ok).toBe(true);
  });
});
