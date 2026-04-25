"""CLI entry — python -m polyglot image|sensor|tts|dossier ..."""
from __future__ import annotations
import argparse
import json
import sys


def main() -> int:
    ap = argparse.ArgumentParser(prog="polyglot")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_img = sub.add_parser("image")
    p_img.add_argument("prompt")
    p_img.add_argument("--out", default="outputs/image.png")
    p_img.add_argument("--w", type=int, default=1024)
    p_img.add_argument("--h", type=int, default=1024)
    p_img.add_argument("--seed", type=int, default=0)
    p_img.add_argument("--no-llm", action="store_true", help="Skip LLM, use fallback painter directly")

    p_sen = sub.add_parser("sensor")
    p_sen.add_argument("prompt")
    p_sen.add_argument("--out", default="outputs/sensor.json")
    p_sen.add_argument("--duration", type=float, default=10.0)
    p_sen.add_argument("--fs", type=float, default=250.0)
    p_sen.add_argument("--dry-run", action="store_true", help="Use built-in spec, no LLM")

    p_tts = sub.add_parser("tts")
    p_tts.add_argument("prompt")
    p_tts.add_argument("--out", default="outputs/speech.m4a")
    p_tts.add_argument("--voice", default=None)
    p_tts.add_argument("--lang", default="en")
    p_tts.add_argument("--rate", type=int, default=180)
    p_tts.add_argument("--raw", action="store_true", help="Skip LLM script rewrite")
    p_tts.add_argument("--ambient", default="auto",
                       help="Ambient layer: auto|none|rain|wind|forest|city|electronic")
    p_tts.add_argument("--ambient-vol", type=float, default=None)

    p_dossier = sub.add_parser("dossier")
    p_dossier.add_argument("prompt")
    p_dossier.add_argument("--provider", default="local", choices=("local", "notebooklm"))
    p_dossier.add_argument("--sources", nargs="+", required=True)
    p_dossier.add_argument("--out", default="artifacts/context/executor-context.md")
    p_dossier.add_argument("--max-files", type=int, default=8)

    p_replay = sub.add_parser("dossier-replay")
    p_replay.add_argument("run_dir")
    p_replay.add_argument("--out", default=None)

    p_verify = sub.add_parser("verify-patch-authority")
    p_verify.add_argument("run_dir")
    p_verify.add_argument("--patch-ledger", default=None)
    p_verify.add_argument("--repo-root", default=None)

    args = ap.parse_args()

    import os
    if getattr(args, "out", None):
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    if args.cmd == "image":
        if args.no_llm:
            from .fallback_painter import paint_fallback
            paint_fallback(args.out, prompt=args.prompt, width=args.w, height=args.h, seed=args.seed)
            result = {"ok": True, "codec": "image:fallback-painter", "artifact_path": args.out}
        else:
            from .image import generate_image
            result = generate_image(args.prompt, args.out, width=args.w, height=args.h, seed=args.seed)
    elif args.cmd == "sensor":
        from .sensor import generate_sensor
        result = generate_sensor(args.prompt, args.out,
                                 default_duration_s=args.duration, default_fs=args.fs,
                                 dry_run=args.dry_run)
    elif args.cmd == "tts":
        from .tts import generate_speech
        result = generate_speech(args.prompt, args.out, voice=args.voice, lang=args.lang,
                                 rate_wpm=args.rate, use_llm_script=not args.raw,
                                 ambient=args.ambient,
                                 ambient_vol=args.ambient_vol)
    elif args.cmd == "dossier":
        from .dossier import generate_dossier
        result = generate_dossier(args.prompt, provider=args.provider, sources=args.sources,
                                  out_path=args.out, max_files=args.max_files)
    elif args.cmd == "dossier-replay":
        from .dossier import replay_dossier
        result = replay_dossier(args.run_dir, out_path=args.out)
    elif args.cmd == "verify-patch-authority":
        from .dossier import verify_patch_authority
        result = verify_patch_authority(run_dir=args.run_dir,
                                        patch_ledger_path=args.patch_ledger,
                                        repository_root=args.repo_root)
    else:
        ap.error(f"unknown cmd {args.cmd}")

    # Do not print full code blob by default
    r = {**result}
    if "code" in r:
        r["code_len"] = len(r["code"]); del r["code"]
    print(json.dumps(r, indent=2, default=str))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
