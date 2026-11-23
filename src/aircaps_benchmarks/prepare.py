"""Rebuild only the pinned, published input IDs; verify every PCM hash."""

import hashlib
import io
import json
import math
import os
import time
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from .io import REPO, manifest


def decode(blob):
    audio, sr = sf.read(io.BytesIO(blob), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        audio = resample_poly(
            audio, 16000 // math.gcd(sr, 16000), sr // math.gcd(sr, 16000)
        )
    return (np.clip(audio, -1, 0.999969) * 32768).astype("<i2").tobytes()


def prepare(track, audio_dir, cache_dir, root=REPO):
    root = Path(root)
    audio_dir = Path(audio_dir)
    cache_dir = Path(cache_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    meta = manifest(track, root)
    pending = {
        k: r
        for k, r in meta.items()
        if not (audio_dir / (r["sha256"] + ".pcm")).exists()
    }
    start = time.monotonic()
    last = start
    done = len(meta) - len(pending)

    def save(key, pcm):
        nonlocal done, last
        row = pending.pop(key)
        if hashlib.sha256(pcm).hexdigest() != row["sha256"]:
            raise ValueError(f"PCM hash differs from recorded input: {key}")
        (audio_dir / (row["sha256"] + ".pcm")).write_bytes(pcm)
        done += 1
        now = time.monotonic()
        if now - last >= 55:
            rate = (done - (len(meta) - initial)) / max(now - start, 0.001)
            remaining = len(meta) - done
            print(
                f"PREPARE {done}/{len(meta)} {rate:.2f}/s ETA {remaining / max(rate, 0.001):.0f}s",
                flush=True,
            )
            last = now

    initial = len(pending)
    print(f"PREPARE {track} {done}/{len(meta)} cached", flush=True)
    if track == "historical/asr" and pending:
        from .historical_inputs import inputs

        sources = json.load((root / "datasets/sources.json").open())
        for key, pcm in inputs(dict(pending), sources, cache_dir, decode):
            save(key, pcm)
    if pending:
        from huggingface_hub import HfApi, hf_hub_download
        import pyarrow.parquet as pq

        sources = json.load((root / "datasets/sources.json").open())
        source = sources["smart_turn" if track == "turns/smart_turn" else "livekit"]
        repo = source["repository"]
        revision = source["revision"]
        api = HfApi(token=os.getenv("HF_TOKEN"))
        info = api.dataset_info(repo, revision=revision)
        shards = [
            x.rfilename for x in info.siblings if x.rfilename.endswith(".parquet")
        ]
        prefix = "smart-turn/" if track == "turns/smart_turn" else "livekit/"
        for i, name in enumerate(shards, 1):
            if not pending:
                break
            path = hf_hub_download(
                repo,
                name,
                repo_type="dataset",
                revision=revision,
                cache_dir=str(cache_dir / "huggingface"),
                token=os.getenv("HF_TOKEN"),
                etag_timeout=30,
            )
            for batch in pq.ParquetFile(path).iter_batches(batch_size=16):
                for row in batch.to_pylist():
                    key = prefix + row["id"]
                    if key in pending:
                        save(key, decode(row["audio"]["bytes"]))
            print(
                f"PREPARE SHARD {i}/{len(shards)}; inputs {done}/{len(meta)}",
                flush=True,
            )
    if pending:
        raise ValueError(f"Pinned source missing {len(pending)} input IDs")
    # Cached inputs are verified too, so a stale cache cannot silently change data.
    for r in meta.values():
        path = audio_dir / (r["sha256"] + ".pcm")
        if hashlib.sha256(path.read_bytes()).hexdigest() != r["sha256"]:
            raise ValueError(f"Corrupt cached PCM: {r['id']}")
    print(
        f"DONE PREPARE {done}/{len(meta)} elapsed {time.monotonic() - start:.1f}s",
        flush=True,
    )


def rebuild_vad_bounds(audio_dir, root=REPO):
    import webrtcvad

    meta = manifest("turns/smart_turn", root)
    out = {}
    for i, (key, row) in enumerate(meta.items(), 1):
        pcm = (Path(audio_dir) / (row["sha256"] + ".pcm")).read_bytes()
        vad = webrtcvad.Vad(2)
        voiced = [
            a / 32000 + 0.02
            for a in range(0, len(pcm) - 639, 640)
            if vad.is_speech(pcm[a : a + 640], 16000)
        ]
        out[key] = voiced[-1] if voiced else None
        if i % 500 == 0:
            print(f"VAD {i}/{len(meta)}", flush=True)
    expected = json.load((Path(root) / "datasets/smart-turn-vad-bounds.json").open())
    if out != expected:
        raise ValueError("Rebuilt VAD boundaries differ from released boundaries")
    print(f"DONE VAD {len(meta)}/{len(meta)}; boundaries verified", flush=True)
