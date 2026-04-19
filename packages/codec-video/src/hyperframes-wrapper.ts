import { spawn } from "node:child_process";
import { mkdir, writeFile, stat } from "node:fs/promises";
import { dirname, extname, join } from "node:path";
import type { RenderCtx, RenderResult } from "@wittgenstein/schemas";
import type { VideoComposition } from "./schema.js";

export async function renderWithHyperFrames(
  composition: VideoComposition,
  ctx: RenderCtx,
): Promise<RenderResult> {
  const startedAt = Date.now();
  const html = buildHyperFramesHtml(composition, ctx);
  const wantsMp4 = extname(ctx.outPath).toLowerCase() === ".mp4";
  const encodeMp4 = process.env.WITTGENSTEIN_HYPERFRAMES_RENDER === "1";

  if (wantsMp4 && encodeMp4) {
    const indexPath = join(ctx.runDir, "index.html");
    await mkdir(ctx.runDir, { recursive: true });
    await mkdir(dirname(ctx.outPath), { recursive: true });
    await writeFile(indexPath, html, "utf8");

    ctx.logger.info("hyperframes: running local MP4 encode (npx hyperframes render)", {
      cwd: ctx.runDir,
      output: ctx.outPath,
    });

    await runHyperframesRenderToMp4({
      cwd: ctx.runDir,
      outputMp4: ctx.outPath,
      fps: composition.fps,
    });

    const bytes = (await stat(ctx.outPath)).size;

    return {
      artifactPath: ctx.outPath,
      mimeType: "video/mp4",
      bytes,
      metadata: {
        codec: "video",
        route: "hyperframes-mp4",
        llmTokens: { input: 0, output: 0 },
        costUsd: 0,
        durationMs: Date.now() - startedAt,
        seed: ctx.seed,
      },
    };
  }

  const artifactPath = resolveHyperFramesArtifactPath(ctx.outPath);

  await mkdir(dirname(artifactPath), { recursive: true });
  await writeFile(artifactPath, html, "utf8");

  const bytes = (await stat(artifactPath)).size;

  return {
    artifactPath,
    mimeType: "text/html; charset=utf-8",
    bytes,
    metadata: {
      codec: "video",
      route: "hyperframes-html",
      llmTokens: { input: 0, output: 0 },
      costUsd: 0,
      durationMs: Date.now() - startedAt,
      seed: ctx.seed,
    },
  };
}

async function runHyperframesRenderToMp4(params: {
  cwd: string;
  outputMp4: string;
  fps: number;
}): Promise<void> {
  const fps = snapHyperframesFps(params.fps);
  const timeoutMs = Number.parseInt(process.env.WITTGENSTEIN_HYPERFRAMES_RENDER_TIMEOUT_MS ?? "600000", 10);
  const args = [
    "-y",
    "hyperframes",
    "render",
    "--output",
    params.outputMp4,
    "--fps",
    String(fps),
    "--quality",
    process.env.WITTGENSTEIN_HYPERFRAMES_QUALITY?.trim() || "standard",
    "--quiet",
  ];

  await spawnProcess(
    "npx",
    args,
    {
      cwd: params.cwd,
      env: {
        ...process.env,
        HYPERFRAMES_NO_TELEMETRY: process.env.HYPERFRAMES_NO_TELEMETRY ?? "1",
        HYPERFRAMES_NO_UPDATE_CHECK: process.env.HYPERFRAMES_NO_UPDATE_CHECK ?? "1",
      },
    },
    timeoutMs,
  );

  try {
    await stat(params.outputMp4);
  } catch {
    throw new Error(
      "hyperframes render exited but output MP4 was not found. Install HyperFrames + FFmpeg + Chrome, run `npx hyperframes doctor`, or unset WITTGENSTEIN_HYPERFRAMES_RENDER to emit HTML only.",
    );
  }
}

function snapHyperframesFps(fps: number): 24 | 30 | 60 {
  if (!Number.isFinite(fps) || fps <= 0) {
    return 30;
  }
  if (fps <= 27) {
    return 24;
  }
  if (fps <= 45) {
    return 30;
  }
  return 60;
}

function spawnProcess(
  command: string,
  args: readonly string[],
  options: { cwd: string; env: NodeJS.ProcessEnv },
  timeoutMs: number,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd,
      env: options.env,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout?.setEncoding("utf8");
    child.stderr?.setEncoding("utf8");
    child.stdout?.on("data", (chunk: string) => {
      stdout += chunk;
    });
    child.stderr?.on("data", (chunk: string) => {
      stderr += chunk;
    });

    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      reject(
        new Error(
          `hyperframes render timed out after ${timeoutMs}ms (set WITTGENSTEIN_HYPERFRAMES_RENDER_TIMEOUT_MS).`,
        ),
      );
    }, timeoutMs);

    child.on("error", (error) => {
      clearTimeout(timer);
      reject(
        new Error(
          `Failed to spawn hyperframes render (${command} ${args.join(" ")}). Is Node/npm available on PATH?`,
          { cause: error },
        ),
      );
    });

    child.on("close", (code) => {
      clearTimeout(timer);
      if (code === 0) {
        resolve();
        return;
      }
      reject(
        new Error(
          `hyperframes render exited with code ${code}: ${stderr.slice(-8000) || stdout.slice(-8000)}`,
        ),
      );
    });
  });
}

function resolveHyperFramesArtifactPath(outPath: string): string {
  const ext = extname(outPath);
  if (ext.toLowerCase() === ".html" || ext.toLowerCase() === ".htm") {
    return outPath;
  }

  // The harness default for video is still `output.mp4`, but this codec stage emits a
  // HyperFrames-style HTML composition (render-to-mp4 happens via HyperFrames CLI).
  if (ext.toLowerCase() === ".mp4") {
    return `${outPath.slice(0, -".mp4".length)}.hyperframes.html`;
  }

  return `${outPath}.hyperframes.html`;
}

function buildHyperFramesHtml(composition: VideoComposition, ctx: RenderCtx): string {
  const width = 1920;
  const height = 1080;
  const compositionId = sanitizeId(`wittgenstein-${ctx.runId}`);
  const inlineSvgs =
    composition.inlineSvgs && composition.inlineSvgs.length > 0 ? composition.inlineSvgs : null;

  let totalDurationSec = 0.25;
  let clipTimelineCss = "";
  let bodyInner: string[] = [];

  if (inlineSvgs) {
    const durations = resolveSlideDurations(composition, inlineSvgs.length);
    let t = 0;
    const svgClips = inlineSvgs.map((svg, index) => {
      const durationSec = durations[index] ?? 3;
      const start = t;
      t += durationSec;
      const label = composition.scenes[index]?.name ?? `slide-${index + 1}`;
      return { svg, index, start, durationSec, label };
    });
    totalDurationSec = Math.max(t, 0.25);
    clipTimelineCss = buildClipTimelineCss(
      svgClips.map((c) => ({ index: c.index, start: c.start, durationSec: c.durationSec })),
      totalDurationSec,
    );

    bodyInner = svgClips.map(({ svg, index, start, durationSec, label }) => {
      const trackIndex = index % 8;
      return [
        `<div`,
        `  class="hf-clip hf-clip--${index}"`,
        `  style="z-index:${10 + index}"`,
        `  data-start="${start}"`,
        `  data-duration="${durationSec}"`,
        `  data-track-index="${trackIndex}"`,
        `>`,
        `  <div class="hf-svg-slide" role="img" aria-label="${escapeHtml(label)}">`,
        stripXmlDeclaration(svg),
        `  </div>`,
        `</div>`,
      ].join("\n");
    });

    return [
      "<!doctype html>",
      `<html lang="en">`,
      `<head>`,
      `<meta charset="utf-8" />`,
      `<meta name="viewport" content="width=device-width, initial-scale=1" />`,
      `<title>${escapeHtml(compositionId)}</title>`,
      `<style>`,
      `:root { color-scheme: dark; }`,
      `html, body { height: 100%; margin: 0; background: #000000; }`,
      `#stage { position: relative; width: ${width}px; height: ${height}px; margin: 0 auto; background: #000000; overflow: hidden; }`,
      `.hf-clip { position: absolute; inset: 0; display: grid; place-items: center; padding: 48px; box-sizing: border-box; opacity: 0; }`,
      `.hf-svg-slide { width: 100%; height: 100%; display: grid; place-items: center; box-sizing: border-box; }`,
      `.hf-svg-slide > svg { width: auto; height: auto; max-width: 1720px; max-height: 940px; display: block; }`,
      clipTimelineCss,
      `</style>`,
      `</head>`,
      `<body>`,
      `<div`,
      `  id="stage"`,
      `  data-composition-id="${escapeHtml(compositionId)}"`,
      `  data-start="0"`,
      `  data-width="${width}"`,
      `  data-height="${height}"`,
      `  data-duration="${totalDurationSec}"`,
      `>`,
      ...bodyInner,
      `</div>`,
      `</body>`,
      `</html>`,
      "",
    ].join("\n");
  }

  const scenes =
    composition.scenes.length > 0
      ? composition.scenes
      : [
          {
            name: "scene-1",
            description: composition.scenes.length === 0 ? "Auto scene (no scenes provided)." : "",
            durationSec: composition.durationSec,
          },
        ];

  totalDurationSec = Math.max(
    composition.durationSec,
    scenes.reduce((sum, s) => sum + s.durationSec, 0),
    0.25,
  );

  let t = 0;
  const clips = scenes.map((scene, index) => {
    const start = t;
    t += scene.durationSec;
    return { scene, index, start };
  });

  clipTimelineCss = buildClipTimelineCss(
    clips.map((c) => ({ index: c.index, start: c.start, durationSec: c.scene.durationSec })),
    totalDurationSec,
  );

  bodyInner = clips.map(({ scene, index, start }) => {
    const trackIndex = index % 8;
    const tone = sceneTone(index);
    return [
      `<div`,
      `  class="hf-clip hf-clip--${index}"`,
      `  style="z-index:${10 + index}; --hf-tone-a:${tone.a}; --hf-tone-b:${tone.b};"`,
      `  data-start="${start}"`,
      `  data-duration="${scene.durationSec}"`,
      `  data-track-index="${trackIndex}"`,
      `>`,
      `  <div class="hf-card" style="background: linear-gradient(145deg, rgba(10,14,28,0.82), rgba(10,14,28,0.62)), radial-gradient(900px 420px at 20% 0%, var(--hf-tone-a), transparent 55%), radial-gradient(700px 500px at 90% 80%, var(--hf-tone-b), transparent 55%);"`,
      `    <div class="hf-emoji" aria-hidden="true">🐧</div>`,
      `    <p class="hf-kicker">${escapeHtml(scene.name)}</p>`,
      `    <h1 class="hf-title">${escapeHtml(scene.name)}</h1>`,
      `    <p class="hf-body">${escapeHtml(scene.description)}</p>`,
      `    <div class="hf-meta">fps=${escapeHtml(String(composition.fps))} · seed=${escapeHtml(String(ctx.seed))}</div>`,
      `  </div>`,
      `</div>`,
    ].join("\n");
  });

  return [
    "<!doctype html>",
    `<html lang="en">`,
    `<head>`,
    `<meta charset="utf-8" />`,
    `<meta name="viewport" content="width=device-width, initial-scale=1" />`,
    `<title>${escapeHtml(compositionId)}</title>`,
    `<style>`,
    `:root { color-scheme: dark; }`,
    `html, body { height: 100%; margin: 0; background: #070a12; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; }`,
    `#stage { position: relative; width: ${width}px; height: ${height}px; margin: 0 auto; background: radial-gradient(1200px 800px at 30% 20%, #1b2a55, #070a12 55%), linear-gradient(180deg, #0b1020, #070a12); overflow: hidden; }`,
    `.hf-clip { position: absolute; inset: 0; display: grid; place-items: center; padding: 96px; box-sizing: border-box; opacity: 0; }`,
    `.hf-card { width: min(1400px, 92vw); border: 1px solid rgba(255,255,255,0.12); border-radius: 28px; padding: 56px 64px; background: rgba(10, 14, 28, 0.72); backdrop-filter: blur(10px); box-shadow: 0 30px 120px rgba(0,0,0,0.45); }`,
    `.hf-emoji { margin: 0 0 20px; font-size: clamp(96px, 14vw, 168px); line-height: 1; filter: drop-shadow(0 14px 36px rgba(0,0,0,0.45)); user-select: none; }`,
    `.hf-kicker { letter-spacing: 0.14em; text-transform: uppercase; font-size: 14px; color: rgba(255,255,255,0.55); margin: 0 0 18px; }`,
    `.hf-title { margin: 0 0 22px; font-size: 64px; line-height: 1.05; font-weight: 650; color: rgba(255,255,255,0.95); }`,
    `.hf-body { margin: 0; font-size: 34px; line-height: 1.35; color: rgba(255,255,255,0.78); white-space: pre-wrap; }`,
    `.hf-meta { margin-top: 34px; font-size: 18px; color: rgba(255,255,255,0.45); }`,
    clipTimelineCss,
    `</style>`,
    `</head>`,
    `<body>`,
    `<div`,
    `  id="stage"`,
    `  data-composition-id="${escapeHtml(compositionId)}"`,
    `  data-start="0"`,
    `  data-width="${width}"`,
    `  data-height="${height}"`,
    `  data-duration="${totalDurationSec}"`,
    `>`,
    ...bodyInner,
    `</div>`,
    `</body>`,
    `</html>`,
    "",
  ].join("\n");
}

function resolveSlideDurations(composition: VideoComposition, slideCount: number): number[] {
  const n = Math.max(1, slideCount);
  const scenes = composition.scenes;
  if (scenes.length === n) {
    return scenes.map((s) => s.durationSec);
  }
  if (composition.durationSec && composition.durationSec > 0) {
    const each = Math.max(0.25, composition.durationSec / n);
    return Array.from({ length: n }, () => each);
  }
  return Array.from({ length: n }, () => 3);
}

function stripXmlDeclaration(svg: string): string {
  return svg.replace(/^\uFEFF?<\?xml[^>]*>\s*/i, "").trim();
}

function sceneTone(index: number): { a: string; b: string } {
  const tones = [
    { a: "rgba(80, 160, 255, 0.35)", b: "rgba(255, 210, 120, 0.22)" },
    { a: "rgba(255, 140, 90, 0.28)", b: "rgba(120, 200, 255, 0.22)" },
    { a: "rgba(190, 120, 255, 0.26)", b: "rgba(120, 255, 200, 0.18)" },
  ] as const;
  return tones[index % tones.length]!;
}

function buildClipTimelineCss(
  clips: Array<{ index: number; start: number; durationSec: number }>,
  totalSec: number,
): string {
  const T = Math.max(totalSec, 0.0001);
  const blocks: string[] = [];

  for (const { index, start, durationSec } of clips) {
    const end = start + durationSec;
    const p0 = (start / T) * 100;
    const p1 = Math.min(100, (end / T) * 100);
    const name = `hf-clip-op-${index}`;
    const atStart = start <= 1e-6;
    const endsAtEnd = end >= T - 1e-6;
    const eps = 0.05;

    let keyframes: string;
    if (atStart && endsAtEnd) {
      keyframes = `@keyframes ${name} { 0%, 100% { opacity: 1; transform: scale(1); } }`;
    } else if (atStart) {
      keyframes = `@keyframes ${name} {
        0% { opacity: 1; transform: scale(1); }
        ${fmtPct(Math.max(0, p1 - eps))} { opacity: 1; transform: scale(1); }
        ${fmtPct(p1)} { opacity: 0; transform: scale(0.99); }
        100% { opacity: 0; transform: scale(0.99); }
      }`;
    } else if (endsAtEnd) {
      keyframes = `@keyframes ${name} {
        0% { opacity: 0; transform: scale(0.99); }
        ${fmtPct(Math.max(0, p0 - eps))} { opacity: 0; transform: scale(0.99); }
        ${fmtPct(p0)} { opacity: 1; transform: scale(1); }
        100% { opacity: 1; transform: scale(1); }
      }`;
    } else {
      keyframes = `@keyframes ${name} {
        0% { opacity: 0; transform: scale(0.99); }
        ${fmtPct(Math.max(0, p0 - eps))} { opacity: 0; transform: scale(0.99); }
        ${fmtPct(p0)} { opacity: 1; transform: scale(1); }
        ${fmtPct(Math.max(p0, p1 - eps))} { opacity: 1; transform: scale(1); }
        ${fmtPct(p1)} { opacity: 0; transform: scale(0.99); }
        100% { opacity: 0; transform: scale(0.99); }
      }`;
    }

    blocks.push(keyframes);
    blocks.push(
      `.hf-clip--${index} { animation: ${name} ${T}s linear both; will-change: opacity, transform; }`,
    );
  }

  return blocks.join("\n");
}

function fmtPct(value: number): string {
  const clamped = Math.max(0, Math.min(100, value));
  return `${clamped.toFixed(3)}%`;
}

function sanitizeId(input: string): string {
  return input.replace(/[^a-zA-Z0-9_-]+/g, "-").replace(/^-+|-+$/g, "") || "composition";
}

function escapeHtml(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
