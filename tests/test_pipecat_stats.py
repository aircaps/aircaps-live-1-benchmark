import sqlite3
import pytest
from aircaps_benchmarks.pipecat_stats import service_stats


def test_matches_upstream_upper_middle_latency_and_joined_pooled_wer():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript("""CREATE TABLE results(sample_id TEXT, service_name TEXT, model_name TEXT, transcription TEXT, ttfb_seconds REAL);
    CREATE TABLE wer_metrics(sample_id TEXT, service_name TEXT, model_name TEXT, wer REAL, substitutions INTEGER, deletions INTEGER, insertions INTEGER, reference_words INTEGER);""")
    for i, latency in enumerate((0.1, 0.2, 0.3, 0.4)):
        db.execute(
            "INSERT INTO results VALUES (?,?,?,?,?)",
            (str(i), "test", "model", "hello", latency),
        )
        db.execute(
            "INSERT INTO wer_metrics VALUES (?,?,?,?,?,?,?,?)",
            (
                str(i),
                "test",
                "model",
                0.5 if i == 0 else 0,
                1 if i == 0 else 0,
                0,
                0,
                2,
            ),
        )
    result = service_stats(db, "test", "model")
    assert result["ttfs"] == 300  # Upstream DB aggregation; not numpy's 250 ms median.
    assert result["mean_wer"] == pytest.approx(0.125)
    assert result["wer"] == pytest.approx(1 / 8)
    assert result["transcript_rate"] == 1 and result["perfect_rate"] == 0.75
