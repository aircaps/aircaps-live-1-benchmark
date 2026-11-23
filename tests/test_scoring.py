import math
from aircaps_benchmarks.scoring import asr_metrics, native_metrics, smart_metrics


def test_wer_is_recomputed_and_failed_requests_are_excluded():
    states = {
        "ok": dict(
            id="ok",
            text="hello there",
            error=None,
            pacing_invalid=False,
            substitutions=1,
            deletions=0,
            insertions=0,
            reference_words=2,
            ttfs_ms=12,
            ttft_ms=5,
        ),
        "bad": dict(id="bad", text="", error="TimeoutError", pacing_invalid=False),
    }
    meta = {
        "ok": dict(reference="hello world"),
        "bad": dict(reference="another request"),
    }
    result = asr_metrics(states, meta)
    assert result["wer"] == 0.5 and result["reference_words"] == 2
    assert result["attempted"] == 2 and result["scored"] == 1 and result["failed"] == 1
    assert result["ttfs_ms"]["median"] == 12


def test_native_denominators_and_conditional_delay():
    states = {"a": dict(turns=[0.5, 3, 9.2])}
    meta = {
        "a": dict(
            spans=[
                dict(start=0, end=1, label="hold"),
                dict(start=2, end=8, label="hold"),
                dict(start=9, end=11, label="eot"),
            ]
        )
    }
    result = native_metrics(states, meta)
    assert result["all_hold_spans"] == 2 and result["hold_spans"] == 1
    assert result["all_false_cutoffs"] == 2 and result["false_cutoffs"] == 1
    assert result["recall"] == 1 and math.isclose(result["median_ms"], 200)


def test_smart_turn_counts_endpoint_during_trailing_file_silence():
    # The valid endpoint occurs well before file end. This catches the historical
    # mistake of aligning to file end instead of the final voiced frame.
    states = {"complete": dict(turns=[2.4]), "incomplete": dict(turns=[1.6])}
    meta = {
        "complete": dict(duration=10, label=True),
        "incomplete": dict(duration=10, label=False),
    }
    result = smart_metrics(states, meta, {"complete": 2.0, "incomplete": 2.0})
    assert result["600"]["tp"] == 1 and result["600"]["fp"] == 0
    assert result["600"]["recall"] == 1 and result["600"]["accuracy"] == 1
    assert result["earlier_endpoint_clip_rate"] == 0.5
    assert result["600"]["pipecat_formula"]["false_positive_rate"] == 0
