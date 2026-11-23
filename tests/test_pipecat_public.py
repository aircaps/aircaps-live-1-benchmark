import pytest
from aircaps_benchmarks.pipecat_public import parse_upstream_readme


def test_snapshot_preserves_published_units_and_legacy_judge_flags():
    text = """<!-- RESULTS_TABLE:START -->
| Vendor | Model | Transcripts | Perfect | WER Mean | Pooled WER | TTFS Median | TTFS P95 | TTFS P99 |
|---|---|---|---|---|---|---|---|---|
| AssemblyAI | universal-3-6-pro | 99.9% | 88.7% | 0.89% | 0.80% | 307ms | 401ms | 498ms |
| NVIDIA | legacy model | 100.0% | 76.1% | 1.90%† | 1.95%† | 221ms | 238ms | 252ms |
<!-- RESULTS_TABLE:END -->"""
    current, legacy = parse_upstream_readme(text)
    assert current["wer"] == pytest.approx(0.008) and current["ttfs"] == 307
    assert current["transcript_rate"] == pytest.approx(0.999)
    assert current["raw_per_clip_available"] is False
    assert legacy["legacy_judge"] is True and legacy["comparable_accuracy"] is False
    assert legacy["wer"] == pytest.approx(0.0195)  # No guessed judge correction.


def test_parser_never_takes_the_aircaps_reference_row_in_place_of_our_raw_rerun():
    text = """<!-- RESULTS_TABLE:START -->
| AirCaps AI | aircaps-live-1 | 100.0% | 90.0% | 0.10% | 0.10% | 100ms | 120ms | 150ms |
| External fixture | model | 100.0% | 90.0% | 0.20% | 0.20% | 110ms | 130ms | 160ms |
<!-- RESULTS_TABLE:END -->"""
    [row] = parse_upstream_readme(text)
    assert row["vendor"] == "External fixture"
