"""Verify fresh prepared PCM files against the original client's manifest."""

import argparse
import hashlib
import json
from pathlib import Path


def verify(audio_dir, manifest):
    audio_dir = Path(audio_dir)
    rows = json.loads(Path(manifest).read_text())["files"]
    for n, row in enumerate(rows, 1):
        path = audio_dir / Path(row["file"]).name
        if not path.is_file():
            raise ValueError(f"Missing prepared input {row['sample_id']}")
        if path.stat().st_size != row["bytes"]:
            raise ValueError(f"Prepared input byte count differs: {row['sample_id']}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["pcm_sha256"]:
            raise ValueError(f"Prepared input SHA-256 differs: {row['sample_id']}")
        if n % 100 == 0:
            print(f"VERIFIED INPUTS {n}/{len(rows)}", flush=True)
    print(
        f"DONE: {len(rows)}/{len(rows)} prepared inputs match the original streamed files",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "results/pipecat_stt/input_manifest.json",
    )
    args = parser.parse_args()
    verify(args.audio_dir, args.manifest)
