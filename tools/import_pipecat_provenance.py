"""Validate recovered client metadata against the archived Pipecat database."""

import argparse
import hashlib
import json
import math
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def import_provenance(source_dir, root=ROOT):
    source_dir, root = Path(source_dir), Path(root)
    original = source_dir / "input_manifest.json"
    metadata = json.loads(original.read_text())
    revision = metadata["resolved_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Expected a full resolved dataset commit")
    rows = metadata["files"]
    db = sqlite3.connect(
        (root / "results/pipecat_stt/results.db").resolve().as_uri() + "?mode=ro",
        uri=True,
    )
    db.row_factory = sqlite3.Row
    samples = {r["sample_id"]: dict(r) for r in db.execute("SELECT * FROM samples")}
    db.close()
    if (
        len(rows) != 1000
        or len({r["sample_id"] for r in rows}) != 1000
        or {r["sample_id"] for r in rows} != set(samples)
    ):
        raise ValueError("Recovered manifest must match all 1000 archived samples")
    for row in rows:
        expected = samples[row["sample_id"]]
        if row["dataset_index"] != expected["dataset_index"]:
            raise ValueError("Dataset index differs from database")
        if not math.isclose(
            row["duration_seconds"],
            expected["duration_seconds"],
            abs_tol=1 / 16000,
            rel_tol=0,
        ):
            raise ValueError("Duration differs from archived sample")
        if not math.isclose(
            row["bytes"] / 32000, row["duration_seconds"], abs_tol=1 / 16000, rel_tol=0
        ):
            raise ValueError("Prepared PCM byte count and duration differ")
        if not re.fullmatch(r"[0-9a-f]{64}", row["pcm_sha256"]):
            raise ValueError("Missing prepared PCM SHA-256")
        row["file"] = Path(row["file"]).name
    metadata["evidence"] = [Path(v).name for v in metadata["evidence"]]
    metadata["source_manifest_sha256"] = hashlib.sha256(
        original.read_bytes()
    ).hexdigest()
    metadata["database_sample_identity_check"] = (
        "1000/1000 IDs, indices, durations matched"
    )
    metadata["hash_provenance"] = (
        "Prepared PCM hashes supplied from the original client's streamed files; audio was not downloaded or rehashed on this Mac."
    )
    destination = root / "results/pipecat_stt"
    (destination / "input_manifest.json").write_text(
        json.dumps(metadata, indent=2) + "\n"
    )
    versions = (source_dir / "dependency_versions.txt").read_text()
    kept = [
        line
        for line in versions.splitlines()
        if re.fullmatch(r"[A-Za-z0-9_.-]+==[^\s]+", line)
    ]
    (destination / "dependency_versions.txt").write_text("\n".join(kept) + "\n")
    status_path = destination / "status.json"
    status = json.loads(status_path.read_text())
    status.update(
        dataset_revision=revision,
        input_manifest="results/pipecat_stt/input_manifest.json",
        prepared_audio_hashes_recorded=1000,
        installed_versions="results/pipecat_stt/dependency_versions.txt",
        note="Resolved dataset commit recovered from the original client cache; manifest identities and durations match the archived database.",
    )
    status_path.write_text(json.dumps(status, indent=2) + "\n")
    source_path = root / "datasets/sources.json"
    sources = json.loads(source_path.read_text())
    sources["pipecat_stt"].update(
        revision=revision,
        status="Completed run; resolved revision, actual-input hashes and installed versions recovered",
        selection="Seed 42, offset 0, first 1000 English non-synthetic samples; original prepared PCM hashes retained.",
    )
    source_path.write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n")
    client_path = root / "provenance/pipecat-production-client.json"
    client = json.loads(client_path.read_text())
    client.update(
        input_revision=revision,
        input_manifest="results/pipecat_stt/input_manifest.json",
        installed_versions="results/pipecat_stt/dependency_versions.txt",
        cache_commit_evidence=metadata["evidence"],
    )
    client_path.write_text(json.dumps(client, indent=2) + "\n")
    print(
        f"IMPORTED PROVENANCE: {revision}; 1000 input identities/durations verified; {len(kept)} installed package versions; no audio or API calls",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    import_provenance(parser.parse_args().source_dir)
