import type { WittgensteinCodec, RenderCtx, RenderResult, VideoRequest } from "@wittgenstein/schemas";
import { Modality } from "@wittgenstein/schemas";
import {
  VideoCompositionSchema,
  VideoRequestSchema,
  parseVideoComposition,
  type VideoComposition,
  videoSchemaPreamble,
} from "./schema.js";
import { renderWithHyperFrames } from "./hyperframes-wrapper.js";

export const videoCodec: WittgensteinCodec<VideoRequest, VideoComposition> = {
  name: "video",
  modality: Modality.Video,
  schemaPreamble: videoSchemaPreamble,
  requestSchema: VideoRequestSchema,
  outputSchema: VideoCompositionSchema,
  parse: parseVideoComposition,
  async render(parsed: VideoComposition, ctx: RenderCtx): Promise<RenderResult> {
    try {
      return await renderWithHyperFrames(parsed, ctx);
    } catch (error) {
      throw createNotImplementedError("codec: video", error);
    }
  },
};

function createNotImplementedError(scope: string, cause?: unknown): Error & { code: string } {
  return Object.assign(new Error(`NotImplementedError(${scope})`, { cause }), {
    name: "NotImplementedError",
    code: "NOT_IMPLEMENTED",
  });
}
