"""Pinned upstream aggregates plus the independently archived AirCaps rerun."""

import hashlib
import json
import sqlite3
from pathlib import Path
from .io import REPO, write_json
from .pipecat_stats import service_stats


def parse_upstream_readme(text):
    start = "<!-- RESULTS_TABLE:START -->"
    end = "<!-- RESULTS_TABLE:END -->"
    if start not in text or end not in text:
        raise ValueError("Upstream result markers missing")
    rows = []

    def number(value, suffix):
        value = value.replace("†", "").strip()
        if not value.endswith(suffix):
            raise ValueError(f"Unexpected upstream numeric format: {value}")
        return float(value[: -len(suffix)])

    for line in text.split(start, 1)[1].split(end, 1)[0].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 9 or cells[0] in ("Vendor", "") or set(cells[0]) <= set("-: "):
            continue
        vendor, model, transcripts, perfect, mean, pooled, median, p95, p99 = cells
        if vendor.lower() == "soniox" or vendor.lower().startswith("aircaps"):
            continue
        legacy = "†" in mean or "†" in pooled
        rows.append(
            dict(
                vendor=vendor,
                model_name=model,
                model=vendor + " — " + model,
                transcript_rate=number(transcripts, "%") / 100,
                perfect_rate=number(perfect, "%") / 100,
                mean_wer=number(mean, "%") / 100,
                wer=number(pooled, "%") / 100,
                ttfs=number(median, "ms"),
                ttfs_p95=number(p95, "ms"),
                ttfs_p99=number(p99, "ms"),
                origin="Upstream aggregate",
                raw_per_clip_available=False,
                judge="Claude Sonnet 4.5" if legacy else "Claude Sonnet 5.5",
                comparable_accuracy=not legacy,
                legacy_judge=legacy,
                raw_markdown=line.strip(),
            )
        )
    if not rows:
        raise ValueError("No upstream entries parsed")
    return rows


def snapshot_upstream(root, commit, readme, license_text, fetched_utc):
    root = Path(root)
    rows = parse_upstream_readme(readme)
    folder = root / "results/pipecat_stt"
    folder.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(readme.encode()).hexdigest()
    source_url = f"https://github.com/pipecat-ai/stt-benchmark/blob/{commit}/README.md"
    snapshot = dict(
        repository="pipecat-ai/stt-benchmark",
        commit=commit,
        source_url=source_url,
        fetched_utc=fetched_utc,
        full_source_readme_sha256=sha,
        metric="semantic WER",
        source_current_judge="Claude Sonnet 5.5",
        source_previous_judge="Claude Sonnet 4.5",
        note="These are rounded upstream-published aggregates, not reruns or per-clip data captured by this project. Older-judge entries retain their qualification; no correction factor is applied.",
        rows=rows,
    )
    write_json(folder / "upstream-published.json", snapshot)
    header = "| Vendor | Model | Transcripts | Perfect | WER Mean | Pooled WER | TTFS Median | TTFS P95 | TTFS P99 |\n|---|---|---:|---:|---:|---:|---:|---:|---:|\n"
    tail = "\n\n† Upstream identifies these WER entries as using the previous Claude Sonnet 4.5 judge, pending rescoring. Current-judge rows use Claude Sonnet 5.5. Upstream cautions that small WER differences are not reliably rankable. Per-model clip data, client locations and collection dates are not supplied in the README.\n"
    (folder / "upstream-published-table.md").write_text(
        "# Upstream-published reference entries\n\nSource: "
        + source_url
        + "\n\n"
        + header
        + "\n".join(r["raw_markdown"] for r in rows)
        + tail
    )
    (root / "licenses/pipecat-stt-BSD-2-Clause.txt").write_text(license_text)
    return snapshot


def combined_rows(root=REPO):
    root = Path(root)
    folder = root / "results/pipecat_stt"
    snapshot = json.load((folder / "upstream-published.json").open())
    rows = [dict(r) for r in snapshot["rows"]]
    status = json.load((folder / "status.json").open())
    if status["status"] == "pending":
        rows.insert(
            0,
            dict(
                model="AirCaps Live 1 — pending",
                origin="Our rerun — pending",
                comparable_accuracy=False,
            ),
        )
    else:
        db = sqlite3.connect(
            (folder / "results.db").resolve().as_uri() + "?mode=ro", uri=True
        )
        db.row_factory = sqlite3.Row
        models = [
            r[0]
            for r in db.execute(
                "SELECT DISTINCT model_name FROM results WHERE service_name='aircaps_live_1'"
            )
        ]
        if len(models) != 1:
            raise ValueError("Import exactly one AirCaps model run")
        values = service_stats(db, "aircaps_live_1", models[0])
        db.close()
        comparable = (
            status.get("judge_matches_upstream") is True
            and status.get("input_reference_matches_canonical") is True
        )
        rows.insert(
            0,
            dict(
                model="AirCaps Live 1",
                origin="Our raw rerun",
                raw_per_clip_available=True,
                comparable_accuracy=comparable,
                legacy_judge=False,
                judge=status.get("judge_identifiers", []),
                **values,
            ),
        )
    return rows, snapshot, status
