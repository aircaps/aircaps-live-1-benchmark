"""Export recorded website evidence without running any provider or judge.

Run on the archive host. Source files are opened read-only. Output is limited
to the models displayed on the Live 1 page; all inputs underlying its pooled
score are retained, including errors and the paired acoustic conditions.
"""

import argparse
import gzip
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from recover_cached_asr_traces import readable_members

MODELS = (
    "aircaps_aircaps-live-1",
    "assemblyai_universal-3-5-pro",
    "assemblyai_universal-3-6-pro",
    "deepgram_flux-general-en",
    "deepgram_nova-3",
    "elevenlabs_scribe_v2_realtime",
    "elevenlabs_scribe_v3_live",
    "mai_mai-transcribe-2-streaming",
)
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


def clean(value):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            key = k.lower()
            if key in {
                "api_key",
                "authorization",
                "x-api-key",
                "xi-api-key",
                "token",
                "access_token",
                "refresh_token",
                "secret",
                "quota_ms",
                "used_ms",
                "provider_remaining_hours",
                "stage",
                "aws_access_key_id",
                "aws_secret_access_key",
                "aws_session_token",
                "client_secret",
            } or key.endswith("_api_key"):
                continue
            if k == "path" and isinstance(v, str):
                out[k] = "audio/" + value["sha256"] + ".pcm"
            elif (
                k == "endpoint_host"
                and isinstance(v, str)
                and (".azure." in v or "cognitiveservices" in v)
            ):
                out[k] = "<MAI_HOST>"
            else:
                out[k] = clean(v)
        return out
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"(?:aircaps_sk_|sk-ant-)[A-Za-z0-9_-]+", "<REDACTED>", value)
    return value


def load(path):
    with Path(path).open() as f:
        return {r["id"]: r for line in f if (r := json.loads(line))}


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", compresslevel=5) as f:
        for r in rows:
            f.write(
                json.dumps(clean(r), separators=(",", ":"), ensure_ascii=False) + "\n"
            )


def export(source, output, limit=None, livekit_results=None):
    start = time.monotonic()
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    # The archive reader is included in this repository; no private helper is needed.
    event_rows = readable_members
    meta = load(source / "manifest.jsonl")
    meta.update(load(source / "clinical-manifest.jsonl"))
    meta = {k: v for k, v in meta.items() if not v.get("turn_only")}
    if limit:
        meta = dict(list(sorted(meta.items()))[:limit])
    elif len(meta) != 9211:
        raise ValueError(f"Unexpected full-suite input count: {len(meta)}")
    manifest = output / "datasets/manifests/historical-asr.jsonl"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "".join(json.dumps(clean(v), ensure_ascii=False) + "\n" for v in meta.values())
    )
    print(
        f"START archive export: {len(meta)} inputs, {len(MODELS)} models; no API calls",
        flush=True,
    )

    def model(name):
        states = {
            k: v
            for k, v in load(source / "results" / (name + "_full.jsonl")).items()
            if k in meta
        }
        if set(states) != set(meta):
            raise ValueError(f"Missing result records for {name}")
        folder = output / "results/historical/asr"
        write_rows(folder / "records" / (name + ".jsonl.gz"), states.values())
        logs = {
            r["id"]: r
            for r in event_rows(source / "results" / (name + "_full-events.jsonl.gz"))
            if r["id"] in meta
        }
        missing = set(meta) - set(logs)
        recovered = []
        if missing:
            pilot = load(source / "results" / (name + "_pilot.jsonl"))
            for r in event_rows(source / "results" / (name + "_pilot-events.jsonl.gz")):
                ident = r["id"]
                if (
                    ident in missing
                    and ident in pilot
                    and all(
                        states[ident].get(k) == pilot[ident].get(k)
                        for k in MATCH_FIELDS
                    )
                ):
                    logs[ident] = r
                    recovered.append(ident)
        write_rows(folder / "events" / (name + ".jsonl.gz"), logs.values())
        return name, dict(
            records=len(states),
            events=len(logs),
            missing_ids=sorted(set(meta) - set(logs)),
            recovered_original_cached_ids=sorted(recovered),
        )

    coverage = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for n, future in enumerate(
            as_completed([pool.submit(model, name) for name in MODELS]), 1
        ):
            name, values = future.result()
            coverage[name] = values
            elapsed = time.monotonic() - start
            print(
                f"EXPORT {n}/{len(MODELS)} {name}: {values['records']} records/{values['events']} traces; elapsed {elapsed:.1f}s; ETA {(len(MODELS) - n) * elapsed / n:.1f}s",
                flush=True,
            )
            if values["missing_ids"]:
                print(
                    f"WARNING {name}: {len(values['missing_ids'])} missing original traces",
                    flush=True,
                )
    if not limit:
        # Export only the supplied selected endpoint configuration.
        if livekit_results is None:
            raise ValueError("Supply the selected LiveKit result directory")
        livekit_results = Path(livekit_results)
        native_meta = {
            k: v
            for k, v in load(source / "manifest.jsonl").items()
            if k.startswith("livekit/")
        }
        p = output / "datasets/manifests/livekit-turns.jsonl"
        p.write_text(
            "".join(
                json.dumps(clean(v), ensure_ascii=False) + "\n"
                for v in native_meta.values()
            )
        )
        name = MODELS[0]
        states = {
            k: v
            for k, v in load(livekit_results / "results.jsonl").items()
            if k in native_meta
        }
        folder = output / "results/turns/livekit"
        write_rows(folder / "records" / (name + ".jsonl.gz"), states.values())
        events = {
            r["id"]: r
            for event_path in sorted(livekit_results.glob("events-*.jsonl.gz"))
            for r in event_rows(event_path)
            if r["id"] in native_meta
        }
        write_rows(folder / "events" / (name + ".jsonl.gz"), events.values())
        coverage["livekit_latency"] = dict(
            records=len(states),
            events=len(events),
            missing_ids=sorted(set(native_meta) - set(events)),
        )
    summary = [
        r
        for r in json.loads((source / "summary.json").read_text())
        if r["run"] in {m + "_full" for m in MODELS}
    ]
    p = output / "results/historical/asr/original-cohort-summaries.json"
    p.write_text(json.dumps(summary, indent=2))
    provenance = output / "provenance/historical-export.json"
    provenance.parent.mkdir(parents=True, exist_ok=True)
    provenance.write_text(
        json.dumps(
            dict(
                coverage=coverage,
                cache_match_fields=MATCH_FIELDS,
                no_api_calls=True,
                source_manifest_sha256=hashlib.sha256(
                    (source / "manifest.jsonl").read_bytes()
                ).hexdigest(),
                elapsed_seconds=time.monotonic() - start,
            ),
            indent=2,
        )
    )
    print(
        f"DONE archive export: {len(coverage)} groups, {time.monotonic() - start:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--livekit-results-dir", type=Path)
    args = parser.parse_args()
    export(args.source_dir, args.output_dir, args.limit, args.livekit_results_dir)
