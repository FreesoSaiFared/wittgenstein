# Distribution

Wittgenstein is designed to be installable and skill-friendly, not just a local experiment.

## Delivery Surface

- `@wittgenstein/cli` exposes `wittgenstein`
- `scripts/install.sh` is the future `curl | sh` seam
- `AGENTS.md` is the short agent primer; `packages/agent-contact-text/` holds extended narrative primers (00–03) for coding agents
- output conventions are stable under `artifacts/runs/*`

## CLI Contract

```bash
wittgenstein init
wittgenstein image  "prompt" --out out.png
wittgenstein audio  "prompt" --out out.wav
wittgenstein video  "prompt" --out out.mp4
wittgenstein sensor "prompt" --out out.json
wittgenstein doctor
```

## Skill-Ready Expectations

- clear command surface
- deterministic artifact locations
- docs that explain the contracts, not just the aspiration
