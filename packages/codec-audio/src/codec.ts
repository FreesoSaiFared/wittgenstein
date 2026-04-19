import type { AudioRequest, WittgensteinCodec, RenderCtx, RenderResult } from "@wittgenstein/schemas";
import { Modality } from "@wittgenstein/schemas";
import {
  AudioPlanSchema,
  AudioRequestSchema,
  audioSchemaPreamble,
  parseAudioPlan,
  type AudioPlan,
} from "./schema.js";
import { renderSpeechRoute } from "./routes/speech/index.js";
import { renderSoundscapeRoute } from "./routes/soundscape/index.js";
import { renderMusicRoute } from "./routes/music/index.js";

export const audioCodec: WittgensteinCodec<AudioRequest, AudioPlan> = {
  name: "audio",
  modality: Modality.Audio,
  schemaPreamble: audioSchemaPreamble,
  requestSchema: AudioRequestSchema,
  outputSchema: AudioPlanSchema,
  parse: parseAudioPlan,
  async render(parsed: AudioPlan, ctx: RenderCtx): Promise<RenderResult> {
    try {
      if (parsed.route === "speech") {
        return await renderSpeechRoute(parsed, ctx);
      }

      if (parsed.route === "soundscape") {
        return await renderSoundscapeRoute(parsed, ctx);
      }

      return await renderMusicRoute(parsed, ctx);
    } catch (error) {
      throw createNotImplementedError("codec: audio", error);
    }
  },
};

function createNotImplementedError(scope: string, cause?: unknown): Error & { code: string } {
  return Object.assign(new Error(`NotImplementedError(${scope})`, { cause }), {
    name: "NotImplementedError",
    code: "NOT_IMPLEMENTED",
  });
}
