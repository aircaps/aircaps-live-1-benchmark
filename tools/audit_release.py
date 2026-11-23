"""Audit dataset/model scope, trace coverage, fixed configs, and secret patterns."""

import ast
import hashlib
import gzip
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aircaps_benchmarks.io import MANIFESTS, manifest, json_rows, records, write_json
from aircaps_benchmarks.scoring import LABELS

SECRET = re.compile(
    r"(?:aircaps_sk_[A-Za-z0-9_-]{12,}|sk-ant-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,})"
)
PRIVATE = (
    r"/Users/[A-Za-z0-9_. -]+/",
    r"/home/(?:ec2-user|ubuntu)/",
    r"arn:aws:[^:]+:[^:]*:\d{12}:",
)
BLOCKED_PROVIDERS = (
    "soniox",
    "bluejay-export",
)
BAD_KEYS = {
    "api_key",
    "authorization",
    "x-api-key",
    "xi-api-key",
    "access_token",
    "refresh_token",
    "aws_secret_access_key",
    "aws_session_token",
    "client_secret",
}


def validate_value(value, where):
    if isinstance(value, dict):
        for k, v in value.items():
            if (k.lower() in BAD_KEYS or k.lower().endswith("_api_key")) and v:
                raise ValueError(f"Credential field in {where}: {k}")
            validate_value(v, where)
    elif isinstance(value, list):
        for v in value:
            validate_value(v, where)
    elif isinstance(value, str) and SECRET.search(value):
        raise ValueError(f"Secret pattern in {where}")


def audit(root=ROOT):
    root = Path(root)
    start = time.monotonic()
    summaries = {}
    files = []
    from aircaps_benchmarks.pipecat_public import parse_upstream_readme

    main = root / "results/pipecat_stt"
    snapshot = json.load((main / "upstream-published.json").open())
    assert len(snapshot["commit"]) == 40
    source = (main / "upstream-published-table.md").read_text()
    reparsed = parse_upstream_readme(
        "<!-- RESULTS_TABLE:START -->\n" + source + "\n<!-- RESULTS_TABLE:END -->"
    )
    assert reparsed == snapshot["rows"], (
        "Published JSON differs from its filtered source rows"
    )
    assert all(
        r["origin"] == "Upstream aggregate" and r["raw_per_clip_available"] is False
        for r in snapshot["rows"]
    )
    status = json.load((main / "status.json").open())
    if status["status"] == "pending":
        assert not (main / "results.db").exists()
    else:
        from aircaps_benchmarks.pipecat_stats import service_stats

        db = sqlite3.connect(
            (main / "results.db").resolve().as_uri() + "?mode=ro", uri=True
        )
        db.row_factory = sqlite3.Row
        manifest_path = main / "input_manifest.json"
        if manifest_path.exists():
            inputs = json.load(manifest_path.open())
            assert inputs["resolved_commit"] == status["dataset_revision"]
            assert len(inputs["files"]) == 1000
            assert {r["sample_id"] for r in inputs["files"]} == {
                r[0] for r in db.execute("SELECT sample_id FROM samples")
            }
            assert all(
                re.fullmatch(r"[0-9a-f]{64}", r["pcm_sha256"]) for r in inputs["files"]
            )
        values = service_stats(db, "aircaps_live_1", "")
        assert values["samples"] == 1000 and values["semantic_scored"] == 997
        assert values["total_errors"] == 83 and values["reference_words"] == 23613
        assert values["failed"] == 3
        assert (
            round(values["ttfs"]) == 209
            and round(values["ttfs_p95"]) == 214
            and round(values["ttfs_p99"]) == 223
        )
        assert (
            db.execute("SELECT COUNT(*) FROM semantic_wer_traces").fetchone()[0] == 997
        )
        for table in (
            "samples",
            "ground_truth",
            "results",
            "wer_metrics",
            "semantic_wer_traces",
            "runs",
        ):
            for row in db.execute('SELECT * FROM "' + table + '"'):
                validate_value(dict(row), "Pipecat/" + table)
        db.close()
    assert not (root / "results/asr/pipecat_original").exists()
    assert not (root / "results/asr/pooled-summary.json").exists()
    print(
        f"AUDIT Pipecat: {len(snapshot['rows'])} source-verified upstream aggregate rows; AirCaps {status['status']}",
        flush=True,
    )
    claim_map = json.load((root / "claims/site-claims.json").open())
    assert len(claim_map["claims"]) == 19
    # The evidence audit must not silently certify the unchanged scope errors.
    claim_status = {r["id"]: r["evidence_status"] for r in claim_map["claims"]}
    assert claim_status["native-38ms-wording"] == "copy_clock_discrepancy"
    assert claim_status["livekit-input-count"] == "reproduced_selected_operating_point"
    configs = json.load((root / "configs/turn_taking.json").open())
    assert configs["livekit"]["aircaps"] == dict(
        end_of_turn=True,
        min_turn_silence_ms=200,
        end_of_turn_threshold=0.65,
        max_turn_silence_ms=3000,
        vad_threshold=0.65,
    )
    assert configs["smart_turn"]["aircaps"] == dict(
        end_of_turn=True,
        min_turn_silence_ms=80,
        end_of_turn_threshold=0.65,
        max_turn_silence_ms=1800,
        vad_threshold=0.3,
    )
    coverage = json.load((root / "provenance/event-trace-coverage.json").open())
    counts = {
        "historical/asr": 9211,
        "turns/livekit": 2288,
        "turns/smart_turn": 5367,
    }
    for track in MANIFESTS:
        meta = manifest(track, root)
        assert len(meta) == counts[track]
        folder = root / "results" / track
        for p in sorted((folder / "records").glob("*.jsonl.gz")):
            name = p.name.removesuffix(".jsonl.gz")
            assert name in LABELS
            expected_models = 8 if track == "historical/asr" else 4
            assert len(list((folder / "records").glob("*.jsonl.gz"))) == expected_models
            rows = records(p)
            assert set(rows) == set(meta), (track, name, "record coverage")
            for r in rows.values():
                validate_value(r, str(p.relative_to(root)))
            events = folder / "events" / (name + ".jsonl.gz")
            seen = set()
            requests = 0
            for r in json_rows(events):
                assert r["id"] in meta
                seen.add(r["id"])
                validate_value(r, str(events.relative_to(root)))
                if name == "aircaps_aircaps-live-1" and track.startswith("turns/"):
                    expected = configs[
                        "livekit" if track.endswith("livekit") else "smart_turn"
                    ]["aircaps"]
                    for _, m in r["events"]:
                        if m.get("type") == "client_start_payload":
                            payload = m["payload"]
                            assert "end_of_turn_mode" not in payload
                            assert all(payload[k] == v for k, v in expected.items())
                            requests += 1
            published = coverage[track + "/" + name]
            assert seen == set(meta) - set(published["missing_ids"])
            if track.startswith("turns/"):
                assert len(seen) == len(meta)
            if name == "aircaps_aircaps-live-1" and track.startswith("turns/"):
                assert requests >= len(meta)
            summaries[track + "/" + name] = dict(
                records=len(rows),
                event_traces=len(seen),
                missing_event_traces=len(meta) - len(seen),
            )
            print(
                f"AUDIT {track} {name}: {len(rows)} records, {len(seen)} trace IDs",
                flush=True,
            )
    for p in root.rglob("*"):
        if not p.is_file() or any(
            part in (".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache")
            for part in p.relative_to(root).parts
        ):
            continue
        rel = str(p.relative_to(root))
        if rel.startswith("results/pipecat_stt/logs/") and p.suffix == ".gz":
            with gzip.open(p, "rt") as log:
                text = log.read()
            assert not SECRET.search(text), f"Secret in compressed log: {rel}"
            assert not any(re.search(pattern, text) for pattern in PRIVATE), (
                f"Private path in compressed log: {rel}"
            )
        if p.name == ".env" or p.name.startswith(".env.") and p.name != ".env.example":
            raise ValueError("Environment secrets file in release tree")
        if (
            p.suffix
            in (".py", ".md", ".json", ".toml", ".yml", ".yaml", ".example", ".txt")
            or p.name == "env.example"
        ):
            text = p.read_text(errors="replace")
            if SECRET.search(text):
                raise ValueError(f"Secret pattern in {rel}")
            if any(re.search(pattern, text) for pattern in PRIVATE):
                raise ValueError(f"Private infrastructure identifier in {rel}")
            if p.suffix == ".py":
                ast.parse(text, filename=rel)
            if p.suffix == ".json":
                json.loads(text)
        if rel.startswith(("results/", "datasets/manifests/", "configs/")) and any(
            s in rel.lower() for s in BLOCKED_PROVIDERS
        ):
            raise ValueError(f"Out-of-scope result/data path: {rel}")
        if p.name != "release-manifest.json" and rel != "provenance/release-audit.json":
            files.append(
                dict(
                    path=rel,
                    bytes=p.stat().st_size,
                    sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                )
            )
    write_json(
        root / "provenance/release-audit.json",
        dict(
            status="passed",
            elapsed_seconds=time.monotonic() - start,
            track_model_coverage=summaries,
            no_api_calls_made=True,
        ),
    )
    write_json(
        root / "release-manifest.json",
        dict(algorithm="sha256", files=sorted(files, key=lambda r: r["path"])),
    )
    print(
        f"DONE AUDIT {len(files)} files, {len(summaries)} track/model pairs, {time.monotonic() - start:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    audit()
