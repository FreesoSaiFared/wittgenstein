import { z } from "zod";
import type { Result, VideoRequest } from "@wittgenstein/schemas";
import { VideoRequestSchema } from "@wittgenstein/schemas";

export const VideoCompositionSchema = z
  .object({
    durationSec: z.number().positive().default(6),
    fps: z.number().positive().default(24),
    scenes: z
      .array(
        z.object({
          name: z.string(),
          description: z.string(),
          durationSec: z.number().positive(),
        }),
      )
      .default([]),
    /** When non-empty, each entry is a full `<svg>…</svg>` shown as one timed slide (HyperFrames HTML). */
    inlineSvgs: z.array(z.string().min(1)).max(32).optional().default([]),
  })
  .superRefine((val, ctx) => {
    if (!val.inlineSvgs || val.inlineSvgs.length === 0) {
      return;
    }
    for (let i = 0; i < val.inlineSvgs.length; i += 1) {
      const s = val.inlineSvgs[i]!;
      const t = s.trimStart().toLowerCase();
      if (!t.startsWith("<svg") || !s.includes("</svg>")) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `inlineSvgs[${i}] must be a full SVG document (<svg …>…</svg>).`,
          path: ["inlineSvgs", i],
        });
      }
    }
  });

export type VideoComposition = z.infer<typeof VideoCompositionSchema>;

export function videoSchemaPreamble(req: VideoRequest): string {
  return [
    "Emit a JSON video composition spec.",
    "Prefer scene-level structure and timing cues.",
    `Requested duration: ${req.durationSec ?? "unspecified"} seconds.`,
    "Optional: include `inlineSvgs` as an array of full SVG documents (strings) for a timed slideshow (one slide per SVG, use `scenes[].durationSec` aligned by index for timing).",
  ].join("\n");
}

export function parseVideoComposition(raw: string): Result<VideoComposition> {
  try {
    const json = JSON.parse(raw) as unknown;
    const parsed = VideoCompositionSchema.safeParse(json);

    if (!parsed.success) {
      return {
        ok: false,
        error: {
          code: "VIDEO_SCHEMA_INVALID",
          message: "Video composition failed validation.",
          details: {
            issues: parsed.error.issues,
          },
        },
      };
    }

    return {
      ok: true,
      value: parsed.data,
    };
  } catch (error) {
    return {
      ok: false,
      error: {
        code: "VIDEO_SCHEMA_PARSE_FAILED",
        message: "Video composition was not valid JSON.",
        cause: error,
      },
    };
  }
}

export { VideoRequestSchema };
