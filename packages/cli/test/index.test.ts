import { describe, expect, it } from "vitest";
import { createProgram } from "../src/index.js";

describe("@wittgenstein/cli", () => {
  it("registers the locked command surface", () => {
    const commandNames = createProgram()
      .commands.map((command) => command.name())
      .sort();

    expect(commandNames).toEqual([
      "animate-html",
      "asciipng",
      "audio",
      "doctor",
      "image",
      "init",
      "sensor",
      "svg",
      "video",
    ]);
  });
});
