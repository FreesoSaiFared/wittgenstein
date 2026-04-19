import { resolve } from "node:path";
import type {
  WittgensteinRequest,
  RenderCtx,
  RenderResult,
  RunManifest,
} from "@wittgenstein/schemas";
import { loadWittgensteinConfig } from "./config.js";
import { BudgetTracker } from "./budget.js";
import { collectRuntimeFingerprint, hashFile } from "./manifest.js";
import { routeRequest } from "./router.js";
import { CodecRegistry } from "./registry.js";
import { createRunId, resolveSeed } from "./seed.js";
import { RunTelemetry } from "./telemetry.js";
import { serializeError, ValidationError } from "./errors.js";
import { injectSchemaPreamble } from "../schema/preamble.js";
import type { LlmAdapter, LlmGenerationResult } from "../llm/adapter.js";
import { OpenAICompatibleLlmAdapter } from "../llm/openai-compatible.js";
import { AnthropicLlmAdapter } from "../llm/anthropic.js";
import { registerAudioCodec } from "../codecs/audio.js";
import { registerImageCodec } from "../codecs/image.js";
import { registerVideoCodec } from "../codecs/video.js";
import { registerSensorCodec } from "../codecs/sensor.js";
import { registerSvgCodec } from "../codecs/svg.js";
import { registerAsciipngCodec } from "../codecs/asciipng.js";
import { generateSvgFromEngine } from "./svg-generation.js";
import { buildSvgLocalGeneration } from "./svg-local.js";
import { buildVideoCompositionFromInlineSvgs } from "./video-inline-svgs.js";
import { generateAsciipngFromMinimax } from "./asciipng-minimax.js";

export interface HarnessRunOptions {
  command: string;
  args: string[];
  cwd?: string;
  dryRun?: boolean;
  outPath?: string;
  configPath?: string;
}

export interface HarnessOutcome {
  manifest: RunManifest;
  result: RenderResult | null;
  runDir: string;
  error: ReturnType<typeof serializeError> | null;
}

export interface WittgensteinOptions {
  registry?: CodecRegistry;
  llmAdapter?: LlmAdapter | null;
}

export class Wittgenstein {
  public constructor(
    private readonly config: Awaited<ReturnType<typeof loadWittgensteinConfig>>,
    private readonly registry: CodecRegistry,
    private readonly llmAdapter: LlmAdapter | null,
  ) {}

  public static async bootstrap(
    options: WittgensteinOptions & { cwd?: string; configPath?: string } = {},
  ): Promise<Wittgenstein> {
    const config = await loadWittgensteinConfig({
      ...(options.cwd ? { cwd: options.cwd } : {}),
      ...(options.configPath ? { configPath: options.configPath } : {}),
    });
    const registry = options.registry ?? createDefaultRegistry();
    const llmAdapter = options.llmAdapter ?? createLlmAdapter(config.llm);
    return new Wittgenstein(config, registry, llmAdapter);
  }

  public async run(
    request: WittgensteinRequest,
    options: HarnessRunOptions,
  ): Promise<HarnessOutcome> {
    const cwd = resolve(options.cwd ?? process.cwd());
    const codec = routeRequest(request, this.registry);
    const runId = createRunId();
    const runDir = resolve(cwd, this.config.runtime.artifactsDir, "runs", runId);
    const telemetry = new RunTelemetry({ runId, runDir });
    const fingerprint = await collectRuntimeFingerprint(cwd);
    const budget = new BudgetTracker(this.config.runtime.budget);
    const seed = resolveSeed(request.seed, this.config.runtime.defaultSeed);
    const promptExpanded = injectSchemaPreamble(
      request.prompt,
      codec.schemaPreamble(request),
    );
    const startedAt = new Date();

    await telemetry.ensureRunDir();
    await telemetry.writeText("llm-input.txt", promptExpanded);

    const manifest: RunManifest = {
      runId,
      ...fingerprint,
      command: options.command,
      args: options.args,
      seed,
      codec: codec.name,
      tier: null,
      route: "route" in request ? request.route : undefined,
      llmProvider: this.config.llm.provider,
      llmModel: this.config.llm.model,
      llmTokens: {
        input: 0,
        output: 0,
      },
      costUsd: 0,
      promptRaw: request.prompt,
      promptExpanded,
      llmOutputRaw: null,
      llmOutputParsed: null,
      artifactPath: null,
      artifactSha256: null,
      startedAt: startedAt.toISOString(),
      durationMs: 0,
      ok: false,
      error: null,
    };

    let result: RenderResult | null = null;
    let error: ReturnType<typeof serializeError> | null = null;

    try {
      const generation =
        request.modality === "asciipng" && request.source === "minimax" && !options.dryRun
          ? await generateAsciipngFromMinimax(request, promptExpanded, seed, this.config.llm)
          : request.modality === "asciipng"
            ? buildAsciiPngGeneration(request)
            : request.modality === "video" && Array.isArray(request.inlineSvgs) && request.inlineSvgs.length > 0
              ? buildVideoCompositionFromInlineSvgs(request)
              : request.modality === "svg" && request.source === "local"
                ? buildSvgLocalGeneration(request)
                : options.dryRun
                  ? createDryRunGeneration(request)
                  : request.modality === "svg"
                    ? await generateSvgFromEngine(promptExpanded, seed, this.config.svg)
                    : await this.generateStructured(promptExpanded, seed);

      if (request.modality === "svg") {
        const raw = generation.raw;
        if (raw && typeof raw === "object" && "svgLocal" in raw && (raw as { svgLocal?: boolean }).svgLocal === true) {
          manifest.llmProvider = "svg-local";
          manifest.llmModel = "geometry-from-prompt";
        } else {
          manifest.llmProvider = "svg-engine";
          manifest.llmModel = this.config.svg.inferenceUrl;
        }
      }

      if (request.modality === "asciipng" && request.source === "minimax") {
        manifest.llmProvider = "minimax";
        manifest.llmModel =
          request.minimaxModel?.trim() ||
          process.env.WITTGENSTEIN_MINIMAX_MODEL?.trim() ||
          "abab6.5s-chat-h";
      } else if (request.modality === "asciipng") {
        manifest.llmProvider = "local-asciipng";
        manifest.llmModel = "pseudo-ascii-raster";
      }

      if (request.modality === "video") {
        const raw = generation.raw;
        if (
          raw &&
          typeof raw === "object" &&
          "videoInlineSvgs" in raw &&
          (raw as { videoInlineSvgs?: boolean }).videoInlineSvgs === true
        ) {
          manifest.llmProvider = "inline-svgs";
          manifest.llmModel = "filesystem";
        }
      }

      budget.consume(
        generation.tokens.input + generation.tokens.output,
        generation.costUsd,
      );

      manifest.llmOutputRaw = generation.text;
      manifest.llmTokens = generation.tokens;
      manifest.costUsd = generation.costUsd;
      await telemetry.writeText("llm-output.txt", generation.text);

      const parsed = codec.parse(generation.text);
      if (!parsed.ok) {
        throw new ValidationError("Codec output could not be parsed", {
          details: {
            codec: codec.name,
            error: parsed.error,
          },
        });
      }

      manifest.llmOutputParsed = parsed.value;

      const renderCtx: RenderCtx = {
        runId,
        runDir,
        seed,
        outPath: resolve(
          options.outPath ?? defaultOutputPathFor(request.modality, cwd, runId),
        ),
        logger: createRunLogger(runId),
      };

      result = await codec.render(parsed.value, renderCtx);
      manifest.artifactPath = result.artifactPath;
      manifest.artifactSha256 = await hashFile(result.artifactPath);
      manifest.ok = true;
      manifest.durationMs = Date.now() - startedAt.getTime();
      manifest.llmTokens = result.metadata.llmTokens;
      manifest.costUsd = result.metadata.costUsd;
    } catch (caughtError) {
      error = serializeError(caughtError);
      manifest.error = error;
      manifest.durationMs = Date.now() - startedAt.getTime();
      manifest.ok = false;
    }

    await telemetry.writeJson("manifest.json", manifest);

    return {
      manifest,
      result,
      runDir,
      error,
    };
  }

  private async generateStructured(
    promptExpanded: string,
    seed: number | null,
  ): Promise<LlmGenerationResult> {
    if (!this.llmAdapter) {
      throw new ValidationError(
        "No LLM adapter is configured for non-dry-run execution.",
      );
    }

    return this.llmAdapter.generate({
      model: this.config.llm.model,
      maxOutputTokens: this.config.llm.maxOutputTokens,
      temperature: this.config.llm.temperature,
      seed,
      responseFormat: "json",
      messages: [
        {
          role: "system",
          content: "Return JSON only. Do not wrap it in markdown.",
        },
        {
          role: "user",
          content: promptExpanded,
        },
      ],
    });
  }
}

export function createDefaultRegistry(): CodecRegistry {
  const registry = new CodecRegistry();
  registerImageCodec(registry);
  registerAudioCodec(registry);
  registerVideoCodec(registry);
  registerSensorCodec(registry);
  registerSvgCodec(registry);
  registerAsciipngCodec(registry);
  return registry;
}

function createLlmAdapter(
  llmConfig: Awaited<ReturnType<typeof loadWittgensteinConfig>>["llm"],
): LlmAdapter | null {
  if (llmConfig.provider === "anthropic") {
    return new AnthropicLlmAdapter(llmConfig);
  }

  return new OpenAICompatibleLlmAdapter(llmConfig);
}

function buildAsciiPngGeneration(request: WittgensteinRequest): LlmGenerationResult {
  if (request.modality !== "asciipng") {
    throw new ValidationError("buildAsciiPngGeneration called for non-asciipng request.");
  }
  const ir = {
    text: request.prompt.slice(0, 2000),
    columns: request.columns,
    rows: request.rows,
    cell: request.cell,
    glyphMode: "pseudo" as const,
  };
  return {
    text: JSON.stringify(ir),
    tokens: { input: 0, output: 0 },
    costUsd: 0,
    raw: { asciiPngLocal: true },
  };
}

function createDryRunGeneration(request: WittgensteinRequest): LlmGenerationResult {
  if (request.modality === "svg") {
    return {
      ...buildSvgLocalGeneration(request),
      raw: { dryRun: true, svgLocal: true },
    };
  }

  if (request.modality === "image") {
    const scene = {
      intent: "Photorealistic wildlife portrait suitable for print",
      subject: request.prompt,
      composition: {
        framing: "tight portrait on subject",
        camera: "telephoto compression, shallow depth of field",
        depthPlan: ["sharp subject", "soft bokeh", "clean background"],
      },
      lighting: { mood: "natural soft daylight", key: "diffused key, gentle fill" },
      style: {
        references: ["wildlife photography", "fine-art nature print"],
        palette: ["neutral grey", "natural fur tones", "cool water highlights"],
      },
      decoder: {
        family: "llamagen" as const,
        codebook: "stub-codebook",
        latentResolution: [32, 32] as [number, number],
      },
    };

    return {
      text: JSON.stringify(scene),
      tokens: {
        input: 0,
        output: 0,
      },
      costUsd: 0,
      raw: {
        dryRun: true,
      },
    };
  }

  return {
    text: "{}",
    tokens: {
      input: 0,
      output: 0,
    },
    costUsd: 0,
    raw: {
      dryRun: true,
    },
  };
}

function defaultOutputPathFor(modality: WittgensteinRequest["modality"], cwd: string, runId: string) {
  const extension =
    modality === "image" || modality === "asciipng"
      ? "png"
      : modality === "audio"
        ? "wav"
        : modality === "video"
          ? "mp4"
          : modality === "svg"
            ? "svg"
            : "json";

  return resolve(cwd, "artifacts", "runs", runId, `output.${extension}`);
}

function createRunLogger(runId: string): RenderCtx["logger"] {
  return {
    debug: (message, data) => {
      console.debug(`[wittgenstein:${runId}] ${message}`, data ?? "");
    },
    info: (message, data) => {
      console.info(`[wittgenstein:${runId}] ${message}`, data ?? "");
    },
    warn: (message, data) => {
      console.warn(`[wittgenstein:${runId}] ${message}`, data ?? "");
    },
    error: (message, data) => {
      console.error(`[wittgenstein:${runId}] ${message}`, data ?? "");
    },
  };
}
