# Wittgenstein

A production-grade modality harness for text-first LLMs.

> Wittgenstein treats the LLM as planner and the repo as runtime OS. The model emits structured IR; codecs turn that IR into files; every run leaves a forensic trail in `artifacts/runs/*`.

## Status

Scaffold phase. Shared contracts, runtime spine, CLI, docs, site app, CI wiring, and reproducibility plumbing are present. Codec bodies are intentionally stubbed with `NotImplementedError`.

## Quick start

```bash
pnpm install
pnpm typecheck
pnpm --filter @wittgenstein/cli exec wittgenstein --help
pnpm --filter @wittgenstein/cli exec wittgenstein image "test prompt" --dry-run
```

## Project map

- [`AGENTS.md`](AGENTS.md) — agent-facing repo map and working rules (primary, short).
- [`packages/agent-contact-text/README.md`](packages/agent-contact-text/README.md) — extended agent primers (00–03) + architecture overview for coding agents.
- [`docs/architecture.md`](docs/architecture.md) — the five-layer foundation mapping.
- [`docs/codec-protocol.md`](docs/codec-protocol.md) — the `WittgensteinCodec` contract.
- [`docs/reproducibility.md`](docs/reproducibility.md) — the manifest spine and seed rules.
- [`docs/team-split.md`](docs/team-split.md) — ownership boundaries and Day 1 split.

## CLI shape

```bash
wittgenstein init
wittgenstein image  "prompt" --out out.png
wittgenstein audio  "prompt" --out out.mp3
wittgenstein video  "prompt" --out out.mp4
wittgenstein sensor "prompt" --out out.json
wittgenstein doctor
```

## Workspace layout

- `packages/schemas` — shared zod schemas and codec contracts
- `packages/core` — harness runtime, config, manifest, retry, telemetry
- `packages/codec-image` — sole image path: JSON scene -> latent codes -> frozen decoder -> PNG
- `packages/codec-audio` — speech, soundscape, and music route stubs
- `packages/codec-video` — HyperFrames wrapper stub
- `packages/codec-sensor` — procedural signal stub
- `packages/cli` — `wittgenstein` CLI
- `packages/agent-contact-text` — extended agent primers (00–03); see [`packages/agent-contact-text/README.md`](packages/agent-contact-text/README.md)
- `apps/site` — official site scaffold
- `docs/` — system of record for architecture and product constraints
- `artifacts/runs` — runtime traces and manifest outputs

## Locked constraints

- Node 20+, TypeScript, pnpm workspaces.
- Image has exactly one pipeline: `LLM -> JSON scene spec -> adapter -> frozen decoder -> PNG`.
- No SVG, HTML, Canvas, or raster fallback for image.
- Decoder is allowed; generator is not. Frozen pretrained decoders are in-bounds.
- Every CLI run writes a run manifest, even on failure.

## License

Apache 2.0 — see [`LICENSE`](LICENSE).
