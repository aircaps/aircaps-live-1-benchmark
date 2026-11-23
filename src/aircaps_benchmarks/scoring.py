"""Offline scoring of released records using the recorded benchmark definitions."""

import math
import time
from pathlib import Path
import numpy as np
import pandas as pd
from .io import REPO, manifest, records, write_json

LABELS = {
    "aircaps_aircaps-live-1": "AirCaps Live 1",
    "assemblyai_universal-3-5-pro": "AssemblyAI Universal-3.5 Pro",
    "assemblyai_universal-3-6-pro": "AssemblyAI Universal-3.6 Pro",
    "deepgram_flux-general-en": "Deepgram Flux",
    "deepgram_nova-3": "Deepgram Nova 3",
    "elevenlabs_scribe_v2_realtime": "ElevenLabs Scribe v2 Realtime",
    "elevenlabs_scribe_v3_live": "ElevenLabs Scribe v3 Live",
    "mai_mai-transcribe-2-streaming": "MAI Transcribe 2 Streaming",
}


def percentiles(values):
    return (
        dict(
            zip(("median", "p95", "p99"), np.percentile(values, [50, 95, 99]).tolist())
        )
        if values
        else None
    )


def asr_metrics(states, meta, verify_edits=True):
    from .vendor.coval_wer import compute_wer

    if set(states) != set(meta):
        raise ValueError(f"Clip coverage differs: {len(states)}/{len(meta)}")
    eligible = [
        r for r in states.values() if not r.get("error") and not r.get("pacing_invalid")
    ]
    scored = []
    for r in eligible:
        if not meta[r["id"]].get("reference"):
            continue
        w = compute_wer(meta[r["id"]]["reference"], r["text"])
        edits = dict(
            substitutions=w.substitutions,
            deletions=w.deletions,
            insertions=w.insertions,
            reference_words=w.reference_words,
        )
        if verify_edits:
            for k, v in edits.items():
                if r.get(k) != v:
                    raise ValueError(
                        f"Saved/recomputed {k} differs for {r['id']}: {r.get(k)}/{v}"
                    )
        scored.append(edits)
    words = sum(r["reference_words"] for r in scored)
    edits = {
        k: sum(r[k] for r in scored)
        for k in ("substitutions", "deletions", "insertions")
    }
    return dict(
        attempted=len(states),
        successful=len(eligible),
        failed=len(states) - len(eligible),
        scored=len(scored),
        reference_words=words,
        **edits,
        wer=sum(edits.values()) / words if words else None,
        mean_clip_wer=float(
            np.mean(
                [
                    sum(r[k] for k in edits) / r["reference_words"]
                    for r in scored
                    if r["reference_words"]
                ]
            )
        )
        if scored
        else None,
        ttfs_ms=percentiles(
            [r["ttfs_ms"] for r in eligible if r.get("ttfs_ms") is not None]
        ),
        ttft_ms=percentiles(
            [r["ttft_ms"] for r in eligible if r.get("ttft_ms") is not None]
        ),
        final_before_endpoint=sum(
            bool(r.get("final_before_endpoint")) for r in eligible
        ),
    )


def native_metrics(states, meta):
    if set(states) != set(meta):
        raise ValueError("Native result clip coverage differs from manifest")
    hold = bad = all_hold = all_bad = eot = hit = 0
    delays = []
    for key, m in meta.items():
        if states[key].get("error") or states[key].get("pacing_invalid"):
            raise ValueError(f"Invalid native record: {key}")
        for s in m["spans"]:
            ends = [t for t in states[key]["turns"] if s["start"] <= t <= s["end"]]
            if s.get("label") == "hold":
                all_hold += 1
                all_bad += bool(ends)
                if 0.2 - 1e-6 <= s["end"] - s["start"] <= 5 + 1e-6:
                    hold += 1
                    bad += bool(ends)
            else:
                eot += 1
                hit += bool(ends)
                if ends:
                    delays.append((min(ends) - s["start"]) * 1000)
    return dict(
        all_hold_spans=all_hold,
        all_false_cutoffs=all_bad,
        all_fpr=all_bad / all_hold,
        hold_spans=hold,
        false_cutoffs=bad,
        fpr=bad / hold,
        eot_spans=eot,
        eot_detected=hit,
        recall=hit / eot,
        median_ms=float(np.median(delays)) if delays else None,
        p95_ms=float(np.percentile(delays, 95)) if delays else None,
    )


def smart_metrics(states, meta, bounds):
    from .vendor.pipecat_metrics import compute_metrics_with_confusion

    if set(states) != set(meta):
        raise ValueError("Smart Turn result clip coverage differs from manifest")
    out = {}
    early = 0
    for budget in (0.6, 1.0):
        tp = fp = tn = fn = 0
        delays = []
        truths = []
        predictions = []
        for key, m in meta.items():
            b = bounds[key]
            if b is None:
                raise ValueError(f"Missing speech boundary: {key}")
            hits = [t for t in states[key]["turns"] if b - 0.25 <= t <= b + budget]
            yes = bool(hits)
            truth = m["label"]
            truths.append(int(truth))
            predictions.append(int(yes))
            tp += yes and truth
            fp += yes and not truth
            tn += not yes and not truth
            fn += not yes and truth
            if truth and hits:
                delays.append((min(hits) - b) * 1000)
            if budget == 0.6:
                early += any(t < b - 0.25 for t in states[key]["turns"])
        out[str(round(budget * 1000))] = dict(
            tp=tp,
            fp=fp,
            tn=tn,
            fn=fn,
            accuracy=(tp + tn) / len(meta),
            recall=tp / (tp + fn),
            fpr=fp / (fp + tn),
            precision=tp / (tp + fp) if tp + fp else 0.0,
            f1=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
            median_ms=float(np.median(delays)) if delays else None,
            p95_ms=float(np.percentile(delays, 95)) if delays else None,
            official_fpr=fp / len(meta),
            official_fnr=fn / len(meta),
        )
        out[str(round(budget * 1000))]["pipecat_formula"] = (
            compute_metrics_with_confusion(
                np.asarray(predictions, dtype=float), np.asarray(truths, dtype=int)
            )
        )
    out["earlier_endpoint_clip_rate"] = early / len(meta)
    return out


def policy_points(predictions):
    from .vendor import livekit_metrics as metrics

    curve = metrics.compute_tradeoff(predictions)
    p = metrics.get_pareto_operating_points(curve, "cutoff_rate", [0.05, 0.10])
    q = metrics.get_pareto_operating_points(curve, "mean_latency", [0.6])
    strict = curve[(curve.policy_type == "model") & (curve.mean_latency < 1.0)]
    return dict(
        delay_5=float(p.iloc[0].value) if p.iloc[0].feasible else None,
        delay_10=float(p.iloc[1].value) if p.iloc[1].feasible else None,
        cutoff_600=float(q.iloc[0].value) if q.iloc[0].feasible else None,
        cutoff_1000=float(strict.cutoff_rate.min()) if len(strict) else None,
    ), curve


def predictions_from_events(meta, logs, provider):
    rows = []
    for key, row in meta.items():
        if key not in logs:
            raise ValueError(f"No raw event trace for {key}")
        data = logs[key]
        events = []
        for receipt, msg in data["events"]:
            value = msg.get("end_of_turn_confidence")
            if value is not None:
                events.append((receipt - data["start"], float(value)))
        events.sort()
        for i, span in enumerate(row["spans"]):
            start, end = span["start"], span["end"]
            if end - start < 0.1 - 1e-6:
                continue
            label = span.get("label") or (
                "eot" if i == len(row["spans"]) - 1 else "hold"
            )
            inside = [e for e in events if start - 1e-6 <= e[0] <= end + 1e-6]
            usable = events if provider == "deepgram" else inside
            count = max(0, int(math.floor((end - start) / 0.1 + 1e-6)))
            grid = [round(start + j * 0.1, 6) for j in range(count + 1)]
            if grid[-1] < end - 1e-6:
                grid.append(round(end, 6))
            index = 0
            value = 0.0
            for timestamp in grid:
                while index < len(usable) and usable[index][0] <= timestamp + 1e-6:
                    value = usable[index][1]
                    index += 1
                r = dict(
                    id=key,
                    span_index=i,
                    timestamp=timestamp,
                    silence_dur=round(timestamp - start, 6),
                    p_eot=value,
                    label=label,
                    cohort=row["cohort"],
                )
                if provider != "aircaps":
                    r["language"] = "en"
                rows.append(r)
    return pd.DataFrame(rows)


def _compare(actual, expected, path=""):
    for k, v in actual.items():
        if k not in expected:
            continue
        if isinstance(v, dict):
            _compare(v, expected[k], path + "/" + k)
        elif isinstance(v, (int, float)) and expected[k] is not None:
            if not math.isclose(v, expected[k], rel_tol=0, abs_tol=1e-8):
                raise ValueError(f"Score mismatch {path}/{k}: {v} versus {expected[k]}")


def score_track(track, root=REPO, rebuild_predictions=False, results_dir=None):
    root = Path(root)
    meta = manifest(track, root)
    folder = Path(results_dir or root) / "results" / track
    outputs = []
    expected_path = folder / "expected-summary.json"
    import json

    expected = json.load(expected_path.open()) if expected_path.exists() else {}
    bounds = (
        json.load((root / "datasets/smart-turn-vad-bounds.json").open())
        if track == "turns/smart_turn"
        else None
    )
    for path in sorted((folder / "records").glob("*.jsonl.gz")):
        name = path.name.removesuffix(".jsonl.gz")
        states = records(path)
        start = time.monotonic()
        if track.startswith("asr/") or track == "historical/asr":
            stat = asr_metrics(states, meta)
            cohorts = {
                c: asr_metrics(
                    {k: states[k] for k, m in meta.items() if m["cohort"] == c},
                    {k: m for k, m in meta.items() if m["cohort"] == c},
                )
                for c in sorted({m["cohort"] for m in meta.values()})
            }
            original = folder / "original-cohort-summaries.json"
            if original.exists():
                for old in json.load(original.open()):
                    if old["run"] != name + "_full":
                        continue
                    new = stat if old["cohort"] == "ALL" else cohorts[old["cohort"]]
                    _compare(
                        {
                            k: new[k]
                            for k in ("attempted", "successful", "scored", "wer")
                        },
                        old,
                        name + "/" + old["cohort"],
                    )
                    if new["reference_words"] != old["words"]:
                        raise ValueError("Archived reference-word count differs")
                    for field in ("ttfs", "ttft"):
                        vals = new[field + "_ms"]
                        old_vals = old[field + "_ms_p50_p95_p99"]
                        if vals is not None:
                            for k, v in zip(("median", "p95", "p99"), old_vals):
                                if not math.isclose(
                                    vals[k], v, rel_tol=0, abs_tol=1e-8
                                ):
                                    raise ValueError(
                                        "Archived latency percentiles differ"
                                    )
        elif track == "turns/smart_turn":
            stat = {
                k: v
                for k, v in smart_metrics(states, meta, bounds).items()
                if k in ("600", "1000")
            }
            cohorts = None
        else:
            stat = native_metrics(states, meta)
            pred_path = folder / "predictions" / (name + ".parquet")
            if rebuild_predictions or not pred_path.exists():
                pred = predictions_from_events(
                    meta,
                    records(folder / "events" / (name + ".jsonl.gz")),
                    name.split("_", 1)[0],
                )
                if pred_path.exists():
                    old = pd.read_parquet(pred_path)
                    pd.testing.assert_frame_equal(
                        pred.sort_values(["id", "span_index", "timestamp"]).reset_index(
                            drop=True
                        )[old.columns],
                        old.sort_values(["id", "span_index", "timestamp"]).reset_index(
                            drop=True
                        ),
                        check_dtype=False,
                        atol=1e-9,
                        rtol=0,
                    )
                else:
                    pred_path.parent.mkdir(parents=True, exist_ok=True)
                    pred.to_parquet(pred_path, index=False)
            else:
                pred = pd.read_parquet(pred_path)
            if set(pred.id) != set(meta):
                raise ValueError("Policy prediction clip coverage differs")
            op, curve = policy_points(pred)
            stat.update(op)
            cohorts = None
        if name in expected:
            _compare(stat, expected[name], name)
        outputs.append(
            dict(
                model=LABELS[name],
                model_key=name,
                clips=len(meta),
                metrics=stat,
                cohorts=cohorts,
            )
        )
        print(
            f"SCORED {track} {name} {len(outputs)} models; {time.monotonic() - start:.1f}s; archived scores verified",
            flush=True,
        )
    if not outputs:
        raise ValueError(f"No published raw records for {track}")
    write_json(
        folder / "summary.json", dict(track=track, clips=len(meta), results=outputs)
    )
    return outputs
