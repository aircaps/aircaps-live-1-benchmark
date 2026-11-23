"""Generate reviewable tables from public, recomputed summaries."""

import json
import math
from pathlib import Path
from .io import REPO, write_json


def markdown(rows, columns):
    best = {
        key: (max if high else min)(
            r[key]
            for r in rows
            if r.get(key) is not None
            and (
                key not in ("wer", "mean_wer", "perfect_rate")
                or r.get("comparable_accuracy", True)
            )
        )
        for key, _, high, scale, fmt in columns
        if fmt != "str"
    }
    out = (
        "| "
        + " | ".join(c[1] for c in columns)
        + " |\n|"
        + "|".join("---" if c[0] == "model" else "---:" for c in columns)
        + "|\n"
    )
    for row in rows:
        cells = []
        for key, _, high, scale, fmt in columns:
            v = row.get(key)
            if fmt == "str":
                cell = v
            elif v is None:
                cell = "N/A"
            else:
                cell = (
                    f"{v * scale:.2f}%"
                    if fmt == "pct"
                    else f"{v * scale:,.0f}"
                    if fmt == "int"
                    else f"{v * scale:,.1f}"
                )
                if (
                    key not in ("wer", "mean_wer", "perfect_rate")
                    or row.get("comparable_accuracy", True)
                ) and math.isclose(v, best[key], rel_tol=0, abs_tol=1e-10):
                    cell = "**" + cell + "**"
            cells.append(cell)
        out += "| " + " | ".join(cells) + " |\n"
    return out


def report(root=REPO):
    root = Path(root)
    from .pipecat_public import combined_rows

    historic = json.load((root / "results/historical/asr/summary.json").open())
    historical_rows = []
    for r in historic["results"]:
        m = r["metrics"]
        historical_rows.append(
            dict(
                model=r["model"],
                model_key=r["model_key"],
                wer=m["wer"],
                ttfs=m["ttfs_ms"]["median"],
                ttfs_p95=m["ttfs_ms"]["p95"],
                ttfs_p99=m["ttfs_ms"]["p99"],
                failed=m["failed"],
                scored=m["scored"],
                words=m["reference_words"],
            )
        )
    historical_rows.sort(key=lambda r: r["wer"])
    parts = [
        "## November 19 evaluation — conventional WER and forced-final response\n\nThese are the archived measurements behind the original website charts. All 9,211 requested clip evaluations are retained; AirCaps has 9,205 WER-scored evaluations and 154,661 reference words. The pool includes overlapping Pipecat/Coval recordings and paired WildASR conditions. It is not a count of independent utterances. Latency starts after client-forced finalization, includes network, and excludes failed requests.\n\n"
        + markdown(
            historical_rows,
            [
                ("model", "Model", False, 1, "str"),
                ("wer", "Pooled WER ↓", False, 100, "pct"),
                ("ttfs", "Final response median ms ↓", False, 1, "int"),
                ("ttfs_p95", "p95 ms ↓", False, 1, "int"),
                ("ttfs_p99", "p99 ms ↓", False, 1, "int"),
                ("failed", "Failed / 9,211 ↓", False, 1, "int"),
            ],
        )
    ]
    cards = {}
    for cohort, title in [
        ("pipecat", "Original Pipecat audio — our conventional-WER protocol"),
        ("stt-v3", "Coval corrected Pipecat subset — 877 clips"),
        ("livekit-general", "LiveKit general — 400 clips"),
        ("livekit-accented", "LiveKit accented — 800 requests, 798 references"),
    ]:
        rows = [
            dict(
                model=r["model"],
                model_key=r["model_key"],
                wer=r["cohorts"][cohort]["wer"],
            )
            for r in historic["results"]
        ]
        rows.sort(key=lambda r: r["wer"])
        cards[cohort] = rows
        parts.append(
            "## "
            + title
            + "\n\n"
            + markdown(
                rows,
                [
                    ("model", "Model", False, 1, "str"),
                    ("wer", "Pooled conventional WER ↓", False, 100, "pct"),
                ],
            )
        )
    smart = json.load((root / "results/turns/smart_turn/summary.json").open())
    smart_tables = {
        budget: [
            dict(model=r["model"], **r["metrics"][budget]) for r in smart["results"]
        ]
        for budget in ("600", "1000")
    }
    for budget, smart_rows in smart_tables.items():
        parts.append(
            f"## Pipecat Smart Turn streaming endpoint diagnostic — {int(budget):,} ms\n\n5,367 natural-English clips: 2,649 complete and 2,718 incomplete. This is a VAD-aligned streaming STT endpoint diagnostic, not official classifier inference. The selected AirCaps configuration omits mode; see configs/turn_taking.json.\n\n"
            + markdown(
                smart_rows,
                [
                    ("model", "Model", False, 1, "str"),
                    ("accuracy", "Accuracy ↑", True, 100, "pct"),
                    ("recall", "Complete-turn recall ↑", True, 100, "pct"),
                    ("precision", "Precision ↑", True, 100, "pct"),
                    ("f1", "F1 ↑", True, 100, "pct"),
                    ("fpr", "False endpoints / incomplete ↓", False, 100, "pct"),
                    ("median_ms", "Matched median ms ↓", False, 1, "int"),
                ],
            )
        )
    native = json.load((root / "results/turns/livekit/summary.json").open())
    native_rows = [dict(model=r["model"], **r["metrics"]) for r in native["results"]]
    parts.append(
        "## LiveKit turn detection — selected configuration\n\n2,288 English clips; 2,305 all hold spans, 2,158 eligible hold spans, and 1,744 true endings. AirCaps: minimum silence 200 ms, EOU threshold .65, maximum silence 3,000 ms, VAD .65; mode omitted. Native cutoff rate uses all hold spans. Policy columns use the official eligible-span mask and independently optimize a client policy at the fixed backend configuration. Delays include network; native median is conditional on detected true endings.\n\n"
        + markdown(
            native_rows,
            [
                ("model", "Model", False, 1, "str"),
                ("all_fpr", "Native cutoffs ↓", False, 100, "pct"),
                ("recall", "EOT recall ↑", True, 100, "pct"),
                ("median_ms", "Native median ms ↓", False, 1, "int"),
                ("delay_5", "Mean delay at ≤5% cutoffs ms ↓", False, 1000, "int"),
                ("delay_10", "At ≤10% ms ↓", False, 1000, "int"),
                ("cutoff_600", "Cutoffs at ≤600 ms mean ↓", False, 100, "pct"),
                ("cutoff_1000", "At <1,000 ms mean ↓", False, 100, "pct"),
            ],
        )
    )
    rows, snapshot, status = combined_rows(root)
    write_json(
        root / "results/pipecat_stt/comparison.json",
        dict(status=status, upstream_source=snapshot["source_url"], rows=rows),
    )
    display = [
        dict(r, model=r["model"] + (" †" if r.get("legacy_judge") else ""))
        for r in rows
    ]
    parts.append(
        "## Pipecat STT — official-harness semantic WER and TTFS\n\nOur completed November 22 AirCaps run used the public production API from Atlanta. The SQLite database, semantic edits, judge conversations and sanitized logs are included. External rows are rounded published aggregates from the [pinned public Pipecat table]("
        + snapshot["source_url"]
        + "). They were not collected by this project on a common client.\n\n"
        + markdown(
            display,
            [
                ("model", "Model", False, 1, "str"),
                ("mean_wer", "Mean semantic WER ↓", False, 100, "pct"),
                ("wer", "Pooled semantic WER ↓", False, 100, "pct"),
                ("perfect_rate", "Perfect transcripts ↑", True, 100, "pct"),
                ("ttfs", "TTFS median ms ↓", False, 1, "int"),
                ("ttfs_p95", "p95 ms ↓", False, 1, "int"),
                ("ttfs_p99", "p99 ms ↓", False, 1, "int"),
                ("transcript_rate", "Returned ↑", True, 100, "pct"),
            ],
        )
        + "\nAirCaps: 83 semantic edits / 23,613 reference words; 936 perfect / 997 returned; 1,000 attempted. Current-judge references and judge identifiers match. Dataset revision 847083fbabb4fbcfae7fe71f24961acdb03de4e3, all 1000 prepared-audio hashes and the original installed package versions are archived. Client distance 1.7 ms is the run operator's reported measurement. † NVIDIA accuracy rows retain the upstream previous-judge qualification and are excluded from current-judge accuracy highlights. No semantic score is pooled with conventional WER.\n"
    )
    text = (
        "\n\n".join(parts)
        + "\n\nBold indicates the best observed value in each displayed comparison, not statistical significance. See [claim mapping](../claims/README.md) for source formulas and measurement scope.\n"
    )
    (root / "results/README.md").write_text(text)
    p = root / "README.md"
    if p.exists():
        old = p.read_text()
        a = "<!-- RESULTS:START -->"
        b = "<!-- RESULTS:END -->"
        if a in old and b in old:
            p.write_text(
                old.split(a)[0] + a + "\n\n" + text + "\n" + b + old.split(b, 1)[1]
            )
    folder = root / "claims"
    folder.mkdir(exist_ok=True)
    write_json(
        folder / "website-metrics.json",
        dict(
            historical=historical_rows,
            dataset_cards=cards,
            smart_turn_600=smart_tables["600"],
            smart_turn_1000=smart_tables["1000"],
            livekit_native=native_rows,
            pipecat=rows,
            upstream=snapshot["source_url"],
        ),
    )
    print(
        "DONE REPORT: website-scoped historical charts, endpoint metrics and separate official Pipecat comparison",
        flush=True,
    )
