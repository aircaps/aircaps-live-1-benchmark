"""One model at a time, causal playback, bounded retries, minute progress."""

import asyncio
import fcntl
import gzip
import json
import time
from pathlib import Path
import aiohttp
from . import adapters
from .io import REPO, manifest, records, clean, write_json


async def run(track, model, audio_dir, output_dir, concurrency=4, root=REPO):
    root = Path(root)
    native = track.startswith("turns/")
    meta = manifest(track, root)
    supported = {p + "_" + m: (p, m, c) for p, m, c in adapters.MODELS}
    if model not in supported:
        raise ValueError("Model is not in this benchmark registry")
    provider, model_id, _ = supported[model]
    if native and provider not in ("aircaps", "assemblyai", "deepgram"):
        raise ValueError("Model has no recorded turn-taking comparison")
    if native and model_id == "nova-3":
        raise ValueError("Nova 3 is an ASR-only model in this release")
    maximum = min(
        adapters.LIMITS[provider],
        {"aircaps": 4, "elevenlabs": 22, "assemblyai": 12, "deepgram": 35, "mai": 4}[
            provider
        ],
    )
    if not 1 <= concurrency <= maximum:
        raise ValueError(f"Concurrency must be between 1 and {maximum}")
    target = Path(output_dir) / "results" / track
    target.mkdir(parents=True, exist_ok=True)
    if target.resolve().is_relative_to((root / "results").resolve()):
        raise ValueError(
            "Use a separate output directory; released results are immutable"
        )
    lock = None
    if provider == "aircaps":
        lock = (root / ".aircaps-streams.lock").open("a")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if native and provider == "aircaps":
        cfg = json.load((root / "configs/turn_taking.json").open())[
            "livekit" if track.endswith("livekit") else "smart_turn"
        ]["aircaps"]
        if "end_of_turn_mode" in cfg and len(cfg) != 2:
            raise ValueError(
                "Do not combine a mode preset with explicit endpoint knobs"
            )
        adapters.ENDPOINT_CONFIG = {k: v for k, v in cfg.items() if k != "end_of_turn"}
    else:
        adapters.ENDPOINT_CONFIG = {}
    (target / "records").mkdir(exist_ok=True)
    (target / "events").mkdir(exist_ok=True)
    result_path = target / "records" / (model + ".jsonl.gz")
    event_path = target / "events" / (model + ".jsonl.gz")
    states = records(result_path) if result_path.exists() else {}
    cached = {
        k
        for k, r in states.items()
        if not r.get("error") and not r.get("pacing_invalid")
    }
    pending = [
        dict(r, path=str(Path(audio_dir) / (r["sha256"] + ".pcm")))
        for k, r in meta.items()
        if k not in cached
    ]
    pending.sort(key=lambda r: r["duration"], reverse=True)
    queue = asyncio.Queue()
    for r in pending:
        queue.put_nowait(r)
    total = len(meta)
    done = total - len(pending)
    initial = done
    start = time.monotonic()
    errors = 0
    next_start = 0.0
    admission_lock = asyncio.Lock()
    write_json(
        target / "run-config.json",
        dict(
            track=track,
            model=model_id,
            provider=provider,
            concurrency=concurrency,
            native=native,
            aircaps_parameters=adapters.ENDPOINT_CONFIG
            if provider == "aircaps" and native
            else None,
            tail_s=2 if native else 0,
        ),
    )
    print(
        f"START {track} {model} {done}/{total}; concurrency {concurrency}", flush=True
    )

    async def progress():
        while True:
            await asyncio.sleep(55)
            elapsed = time.monotonic() - start
            rate = (done - initial) / max(elapsed, 0.001)
            print(
                f"PROGRESS {done}/{total}; {rate:.3f} clips/s; ETA {(total - done) / max(rate, 0.001):.0f}s; errors {errors}",
                flush=True,
            )

    reporter = asyncio.create_task(progress())
    try:
        async with aiohttp.ClientSession() as session:
            with (
                gzip.open(result_path, "at", compresslevel=3) as out,
                gzip.open(event_path, "at", compresslevel=3) as ev,
            ):

                async def worker():
                    nonlocal done, errors, next_start
                    try:
                        while not queue.empty():
                            row = queue.get_nowait()
                            for attempt in range(3):
                                if provider in adapters.STARTS:
                                    async with admission_lock:
                                        await asyncio.sleep(
                                            max(0, next_start - time.monotonic())
                                        )
                                        next_start = (
                                            time.monotonic() + adapters.STARTS[provider]
                                        )
                                r, e = await adapters.transcribe(
                                    session, provider, model_id, row, native
                                )
                                if not r["error"] and not r["pacing_invalid"]:
                                    break
                                errors += 1
                                print(
                                    f"WARNING {row['id']}: {r['error'] or 'pacing invalid'}",
                                    flush=True,
                                )
                                if attempt < 2:
                                    await asyncio.sleep(2**attempt)
                            r["attempts"] = attempt + 1
                            if provider == "aircaps" and native:
                                starts = [
                                    m["payload"]
                                    for _, m in e["events"]
                                    if m.get("type") == "client_start_payload"
                                ]
                                if len(starts) != 1 or "end_of_turn_mode" in starts[0]:
                                    raise RuntimeError(
                                        "AirCaps request evidence missing or mode was set"
                                    )
                                r["configuration"] = dict(adapters.ENDPOINT_CONFIG)
                            out.write(json.dumps(clean(r), ensure_ascii=False) + "\n")
                            out.flush()
                            ev.write(json.dumps(clean(e), ensure_ascii=False) + "\n")
                            ev.flush()
                            done += 1
                    finally:
                        task = asyncio.current_task()
                        if getattr(task, "mai_ws", None):
                            await task.mai_ws.close()

                await asyncio.gather(*(worker() for _ in range(concurrency)))
    finally:
        reporter.cancel()
        await asyncio.gather(reporter, return_exceptions=True)
        if lock:
            lock.close()
    print(
        f"DONE {done}/{total}; errors {errors}; elapsed {time.monotonic() - start:.1f}s",
        flush=True,
    )
