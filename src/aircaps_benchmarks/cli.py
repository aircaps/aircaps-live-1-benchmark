"""Explicit replay and offline reproduction commands; no automatic API calls."""

import argparse
import asyncio
from pathlib import Path
from .io import REPO, MANIFESTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("score", help="Recompute released results offline")
    p.add_argument("--track", choices=[*MANIFESTS, "all"], default="all")
    p.add_argument("--rebuild-predictions", action="store_true")
    p.add_argument("--results-dir", type=Path)
    p = sub.add_parser(
        "prepare", help="Download pinned input audio into explicit storage"
    )
    p.add_argument("--track", choices=MANIFESTS, required=True)
    p.add_argument("--audio-dir", type=Path, required=True)
    p.add_argument("--cache-dir", type=Path, required=True)
    p = sub.add_parser(
        "vad-bounds", help="Verify published Smart Turn speech boundaries"
    )
    p.add_argument("--audio-dir", type=Path, required=True)
    p = sub.add_parser("run", help="Replay one model; requires your API key")
    p.add_argument("--track", choices=MANIFESTS, required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--audio-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--concurrency", type=int, default=4)
    p = sub.add_parser(
        "report", help="Generate tables from recomputed public summaries"
    )
    args = parser.parse_args()
    if args.command == "score":
        from .scoring import score_track

        for track in MANIFESTS if args.track == "all" else [args.track]:
            score_track(track, args.root, args.rebuild_predictions, args.results_dir)
    elif args.command == "prepare":
        from .prepare import prepare

        prepare(args.track, args.audio_dir, args.cache_dir, args.root)
    elif args.command == "vad-bounds":
        from .prepare import rebuild_vad_bounds

        rebuild_vad_bounds(args.audio_dir, args.root)
    elif args.command == "run":
        from dotenv import load_dotenv

        load_dotenv(args.root / ".env")
        from .replay import run

        asyncio.run(
            run(
                args.track,
                args.model,
                args.audio_dir,
                args.output_dir,
                args.concurrency,
                args.root,
            )
        )
    elif args.command == "report":
        from .reporting import report

        report(args.root)


if __name__ == "__main__":
    main()
