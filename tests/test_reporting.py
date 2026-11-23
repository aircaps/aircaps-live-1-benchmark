from aircaps_benchmarks.reporting import markdown


def test_legacy_judge_rows_are_not_highlighted_as_current_judge_winners():
    rows = [
        dict(model="current", wer=0.02, comparable_accuracy=True),
        dict(model="legacy", wer=0.01, comparable_accuracy=False),
    ]
    output = markdown(
        rows, [("model", "Model", False, 1, "str"), ("wer", "WER", False, 100, "pct")]
    )
    assert "**2.00%**" in output and "**1.00%**" not in output
