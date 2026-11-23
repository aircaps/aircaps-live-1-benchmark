"""Recover original cached ASR traces, never rerun or synthesize provider output.

Accepts original full/cached record files plus the cached event archive and an
explicit JSON list of missing IDs. Record identity and event replay must both
match before a trace is emitted. This is archival repair, not EOU tuning.
"""

import argparse
import gzip
import json
import math
import re
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aircaps_benchmarks.adapters import Adapter
from aircaps_benchmarks.io import records, clean, write_json

MATCH_FIELDS = (
    "id",
    "cohort",
    "provider",
    "model",
    "native",
    "text",
    "error",
    "pacing_invalid",
    "audio_duration",
    "ttfs_ms",
    "ttft_ms",
    "final_before_endpoint",
    "turns",
    "completed_utc",
    "wer",
    "substitutions",
    "deletions",
    "insertions",
    "reference_words",
)


def readable_members(path, chunk_size=16384):
    data = Path(path).read_bytes()
    covered = 0
    for found in re.finditer(b"\x1f\x8b\x08", data):
        start = found.start()
        if start < covered:
            continue
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        pending = b""
        for offset in range(start, len(data), chunk_size):
            chunk = data[offset : offset + chunk_size]
            before = decoder.copy()
            failed = False
            try:
                part = decoder.decompress(chunk)
            except zlib.error:
                # A failed call can discard valid output produced earlier in the
                # same compressed chunk. Recover that output from original bytes.
                decoder = before
                parts = []
                for byte in chunk:
                    try:
                        parts.append(decoder.decompress(bytes([byte])))
                    except zlib.error:
                        break
                part = b"".join(parts)
                failed = True
                print(f"WARNING unreadable gzip member at byte {start}", flush=True)
            pending += part
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                try:
                    yield json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            if failed:
                break
            if decoder.eof:
                covered = offset + len(chunk) - len(decoder.unused_data)
                break
        if pending.strip():
            try:
                row = json.loads(pending)
                if isinstance(row, dict) and "id" in row:
                    yield row
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass


def verify_trace(result, event):
    if result.get("native"):
        raise ValueError("This recovery verifier is for forced-final ASR records")
    adapter = Adapter(result["provider"], result["model"], False)
    original = time.perf_counter
    try:
        for at, message in event["events"]:
            time.perf_counter = lambda value=at: value
            adapter.message(message)
    finally:
        time.perf_counter = original
    observed = dict(
        text=adapter.text,
        ttfs_ms=max(0, (adapter.last_final - event["t0"]) * 1000)
        if adapter.last_final and event["t0"]
        else None,
        ttft_ms=(adapter.first - event["start"]) * 1000
        if adapter.first and event["start"]
        else None,
    )
    for key, value in observed.items():
        expected = result[key]
        if isinstance(value, (float, int)) and expected is not None:
            if not math.isclose(value, expected, rel_tol=0, abs_tol=1e-7):
                return False
        elif value != expected:
            return False
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--full-records", type=Path, required=True)
    p.add_argument("--cached-records", type=Path, required=True)
    p.add_argument("--cached-events", type=Path, required=True)
    p.add_argument("--missing-ids", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--bytewise", action="store_true")
    a = p.parse_args()
    full = records(a.full_records)
    cached = records(a.cached_records)
    logs = {
        r["id"]: r
        for r in readable_members(a.cached_events, 1 if a.bytewise else 16384)
    }
    wanted = json.load(a.missing_ids.open())
    restored = []
    unmatched = []
    if a.output.exists():
        raise ValueError("Write to a new recovery file, not an existing archive")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(a.output, "wt", compresslevel=5) as out:
        for key in wanted:
            if (
                key in full
                and key in cached
                and key in logs
                and all(full[key].get(k) == cached[key].get(k) for k in MATCH_FIELDS)
                and verify_trace(full[key], logs[key])
            ):
                out.write(json.dumps(clean(logs[key]), ensure_ascii=False) + "\n")
                restored.append(key)
            else:
                unmatched.append(key)
    write_json(
        a.output.with_suffix(".recovery.json"),
        dict(
            matched_fields=MATCH_FIELDS,
            restored_ids=restored,
            unmatched_ids=unmatched,
            new_api_calls=0,
        ),
    )
    print(
        f"DONE RECOVERY {len(restored)}/{len(wanted)} exact original traces; unmatched {len(unmatched)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
