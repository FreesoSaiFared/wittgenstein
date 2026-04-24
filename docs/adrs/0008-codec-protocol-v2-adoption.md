# 0008 Codec Protocol v2 Adoption

## Status

Accepted (ratifies RFC-0001)

## Decision

Wittgenstein adopts Codec Protocol v2 as specified in RFC-0001. The `Codec<Req, Art>.produce(req, ctx): Promise<Art>` primitive replaces per-modality branching in `packages/core/src/runtime/harness.ts:123-172`. Strategy moves from request schema into codec-declared `Route` metadata, retiring `AudioRequest.route`, `SvgRequest.source`, `AsciipngRequest.source`, and `VideoRequest.inlineSvgs`. Every codec implements the full L3–L5 pipeline (`expand → adapt → decode → package`), even if L4 adapter or L5 packaging is a no-op — the seams exist uniformly. The codec authors its own `manifestRows(art)`; harness merges but does not override, retiring `harness.ts:139-172`. The `Handoff = Text | Latent | Hybrid` sum type (named by ADR-0010) is the canonical handoff shape between LLM and codec, with only `Text` inhabited at v0.2. Default pipeline is two LLM rounds: round 1 expansion to natural-language description, round 2 schema-constrained JSON (XGrammar / Outlines / Anthropic chain-of-thought-then-structured prior art).

## Consequence

Migration is phased sensor → audio → image → cleanup (RFC-0001 §Migration). Kill date for the pre-v2 surface is v0.3.0. Brief A's rename "VQ decoder" → "LFQ-family discrete-token decoder" lands in M5 alongside the harness cleanup, updating ADR-0005's vocabulary without weakening its content. Future scale-out past ~10 modalities is unblocked because adding a modality is now "implement `Codec` once," not "add a branch to the harness and four fields to the request schema." If after migration ≥2 modalities still need special-case harness carve-outs, or if the round-trip test cannot fit a new modality in ≤20 lines, RFC-0001's kill criteria fire and v3 opens.
