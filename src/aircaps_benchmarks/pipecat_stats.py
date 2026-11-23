"""SQLite aggregation matching the pinned upstream update-readme path.

In particular, upstream takes the upper middle positive TTFS value, not the
average of two middle values. WER rows are joined on sample/service/model.
"""


def service_stats(db, service, model):
    rows = list(
        db.execute(
            "SELECT * FROM results WHERE service_name=? AND model_name IS ?",
            (service, model),
        )
    )
    wer = list(
        db.execute(
            """SELECT w.* FROM wer_metrics w JOIN results r
        ON w.sample_id=r.sample_id AND w.service_name=r.service_name AND w.model_name=r.model_name
        WHERE w.service_name=? AND w.model_name IS ?""",
            (service, model),
        )
    )
    words = sum(r["reference_words"] for r in wer)
    errors = sum(r["substitutions"] + r["deletions"] + r["insertions"] for r in wer)
    latency = sorted(
        r["ttfb_seconds"] * 1000
        for r in rows
        if r["ttfb_seconds"] is not None and r["ttfb_seconds"] > 0
    )
    successful = sum(
        r["transcription"] is not None and r["transcription"] != "" for r in rows
    )
    return dict(
        mean_wer=sum(r["wer"] for r in wer) / len(wer) if wer else None,
        wer=errors / words if words else None,
        ttfs=latency[len(latency) // 2] if latency else 0.0,
        ttfs_p95=latency[int(len(latency) * 0.95)]
        if len(latency) > 1
        else latency[0]
        if latency
        else 0.0,
        ttfs_p99=latency[int(len(latency) * 0.99)]
        if len(latency) > 1
        else latency[0]
        if latency
        else 0.0,
        transcript_rate=successful / len(rows) if rows else 0.0,
        perfect_rate=sum(r["wer"] == 0 for r in wer) / len(wer) if wer else 0.0,
        failed=len(rows) - successful,
        samples=len(rows),
        semantic_scored=len(wer),
        reference_words=words,
        total_errors=errors,
    )
