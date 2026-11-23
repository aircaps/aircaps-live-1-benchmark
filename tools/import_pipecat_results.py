"""Import a completed upstream SQLite run without credentials or excluded services.

The source is opened read-only and never modified. The public database retains
transcripts, references, per-clip semantic edits and judge traces, not just means.
"""

import argparse
from functools import cache
import gzip
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aircaps_benchmarks.io import clean, write_json


@cache
def permitted(service):
    # External main-table entries come only from the pinned upstream snapshot.
    return service == "aircaps_live_1"


def sanitize_cell(value, column):
    if isinstance(value, str):
        if value.lstrip().startswith(("{", "[")):
            try:
                parsed = json.loads(value)
                if column == "services" and isinstance(parsed, list):
                    parsed = [s for s in parsed if permitted(s)]
                return json.dumps(clean(parsed), ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        return clean(value)
    return value


def import_database(database, dataset_revision=None, logs_dir=None, source_readme=None):
    database = Path(database).resolve()
    dest = ROOT / "results/pipecat_stt"
    dest.mkdir(parents=True, exist_ok=True)
    output = dest / "results.db"
    if output.exists():
        raise ValueError(
            "Public results.db exists; archive it explicitly before replacing it"
        )
    source = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    source.execute("BEGIN")
    target = sqlite3.connect(output)
    try:
        schema = source.execute(
            "SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        required = {
            "samples",
            "results",
            "ground_truth",
            "wer_metrics",
            "semantic_wer_traces",
        }
        if not required <= {r["name"] for r in schema}:
            raise ValueError("Not a supported Pipecat benchmark database")
        counts = {}
        for table in schema:
            name = table["name"]
            if name not in required | {"runs"}:
                continue
            target.execute(table["sql"])
            count = 0
            for row in source.execute('SELECT * FROM "' + name + '"'):
                item = dict(row)
                if "service_name" in item and not permitted(item["service_name"]):
                    continue
                if name == "samples":
                    item["audio_path"] = "audio/" + item["sample_id"] + ".pcm"
                item = {k: sanitize_cell(v, k) for k, v in item.items()}
                columns = list(item)
                quoted = ",".join('"' + k + '"' for k in columns)
                target.execute(
                    'INSERT INTO "'
                    + name
                    + '" ('
                    + quoted
                    + ") VALUES ("
                    + ",".join("?" for _ in columns)
                    + ")",
                    [item[k] for k in columns],
                )
                count += 1
            counts[name] = count
        if counts["samples"] != 1000:
            raise ValueError(
                f"Expected the 1000-sample main run, found {counts['samples']}"
            )
        if counts["ground_truth"] != 1000:
            raise ValueError("The main run must include all 1000 reference rows")
        if not counts["wer_metrics"]:
            raise ValueError(
                "No completed semantic-WER results; keep the pending marker"
            )
        for service, model, n in target.execute(
            "SELECT service_name,model_name,COUNT(*) FROM results GROUP BY service_name,model_name"
        ):
            if n != 1000:
                raise ValueError(
                    f"Incomplete service {service}: {n}/1000 result rows; wait for completion"
                )
            needed = target.execute(
                "SELECT sample_id FROM results WHERE service_name=? AND model_name IS ? AND transcription IS NOT NULL",
                (service, model),
            ).fetchall()
            scored = {
                r[0]
                for r in target.execute(
                    "SELECT sample_id FROM wer_metrics WHERE service_name=? AND model_name IS ?",
                    (service, model),
                )
            }
            if any(r[0] not in scored for r in needed):
                raise ValueError(
                    f"Semantic WER is incomplete for {service}; wait for the judge"
                )
        target.commit()
        services = [
            r[0] for r in target.execute("SELECT DISTINCT service_name FROM results")
        ]
        for name in ("results", "wer_metrics", "semantic_wer_traces"):
            bad = target.execute(
                'SELECT COUNT(*) FROM "'
                + name
                + '" WHERE sample_id NOT IN (SELECT sample_id FROM samples)'
            ).fetchone()[0]
            if bad:
                raise ValueError("Result rows refer to missing samples")
        # Readable exports accompany SQLite for review and ordinary Git diffs.
        for name in (
            "samples",
            "ground_truth",
            "results",
            "wer_metrics",
            "semantic_wer_traces",
            "runs",
        ):
            if name not in counts:
                continue
            target.row_factory = sqlite3.Row
            with gzip.open(dest / (name + ".jsonl.gz"), "wt", compresslevel=5) as f:
                for row in target.execute('SELECT * FROM "' + name + '"'):
                    f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
        judges = set()
        for table, column in [
            ("wer_metrics", "judge"),
            ("semantic_wer_traces", "model_used"),
        ]:
            columns = {
                r[1] for r in target.execute('PRAGMA table_info("' + table + '")')
            }
            if column in columns:
                judges.update(
                    r[0]
                    for r in target.execute(
                        'SELECT DISTINCT "' + column + '" FROM "' + table + '"'
                    )
                    if r[0]
                )
        judge_matches = bool(judges) and all(
            "sonnet-5-5" in re.sub(r"[^a-z0-9]+", "-", v.lower()) for v in judges
        )
        reference_path = (
            ROOT / "benchmarks/pipecat_stt/ground_truth/2026-01-03_17-00-06.jsonl"
        )
        reference_match = None
        if reference_path.exists():
            references = {}
            for line in reference_path.open():
                r = json.loads(line)
                if r.get("type") == "sample":
                    references[r["sample_id"]] = r["transcription"]
            notes = reference_path.with_name(reference_path.stem + "_notes.jsonl")
            if notes.exists():
                for line in notes.open():
                    r = json.loads(line)
                    if r.get("type") == "edit":
                        references[r["sample_id"]] = r["corrected_text"]
            reference_match = all(
                sid in references and references[sid] == text
                for sid, text in target.execute(
                    "SELECT sample_id,text FROM ground_truth"
                )
            )
        metadata = dict(
            input_reference_matches_canonical=reference_match,
            judge_identifiers=sorted(judges),
            judge_matches_upstream=judge_matches,
            external_rows_source="Pinned upstream README aggregates only",
            status="results_imported",
            samples=counts["samples"],
            services=services,
            table_counts=counts,
            dataset="pipecat-ai/smart-turn-data-v3.1-train",
            dataset_revision=dataset_revision,
            upstream_commit="d4d85a9",
            aircaps_adapter_commit="3677567",
            source_database_sha256=hashlib.sha256(database.read_bytes()).hexdigest(),
            public_database_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
            note="Input dataset revision was not recorded by this import."
            if not dataset_revision
            else "Pinned source revision supplied with the completed run.",
        )
        write_json(dest / "status.json", metadata)
    except BaseException:
        target.close()
        source.close()
        output.unlink(missing_ok=True)
        raise
    else:
        target.close()
        source.close()
    if source_readme:
        # Regenerate the main leaderboard from SQLite; the supplied README is a
        # source artifact, not an independently verified result table.
        text = Path(source_readme).read_text()
        text = "\n".join(
            line
            for line in text.splitlines()
            if not any(s in line.lower() for s in ("soniox", "stt-rt-v5", "stt-rt-v6"))
        )
        (dest / "source-run-readme.md").write_text(clean(text) + "\n")
    if logs_dir:
        log_dest = dest / "logs"
        log_dest.mkdir(exist_ok=True)
        for p in Path(logs_dir).iterdir():
            if not p.is_file() or p.suffix not in (".log", ".txt"):
                continue
            text = clean(p.read_text(errors="replace"))
            text = re.sub(
                r"/home/(?:ec2-user|ubuntu)/[^\s\"<>]+",
                lambda m: "<CLIENT_PATH>/" + Path(m[0]).name,
                text,
            )
            text = re.sub(
                r"(?im)^(.*(?:api[_-]?key|authorization|secret_access_key)\s*[:=]).*$",
                r"\1 <REDACTED>",
                text,
            )
            with gzip.open(log_dest / (p.name + ".gz"), "wt", compresslevel=5) as f:
                f.write(text)
    print("IMPORTED", json.dumps(metadata), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("database", type=Path)
    p.add_argument("--dataset-revision")
    p.add_argument("--logs-dir", type=Path)
    p.add_argument("--source-readme", type=Path)
    a = p.parse_args()
    import_database(a.database, a.dataset_revision, a.logs_dir, a.source_readme)


if __name__ == "__main__":
    main()
