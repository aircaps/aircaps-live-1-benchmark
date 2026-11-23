"""Map comparison measurements to raw evidence and their scope."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aircaps_benchmarks.io import write_json


def build(root=ROOT):
    root = Path(root)
    claims = []

    def add(key, text, status, sources, formula, note=""):
        claims.append(
            dict(
                id=key,
                page_claim=text,
                evidence_status=status,
                source_files=sources,
                reproduction="uv run aircaps-bench score --track all && uv run aircaps-bench report",
                formula=formula,
                note=note,
            )
        )

    historical = [
        "datasets/manifests/historical-asr.jsonl",
        "results/historical/asr/records/",
        "results/historical/asr/summary.json",
        "src/aircaps_benchmarks/adapters.py",
        "src/aircaps_benchmarks/scoring.py",
    ]
    add(
        "pooled-wer",
        "3.65% WER; displayed competitors make 12–105% more errors",
        "reproduced_historical_measurement",
        historical,
        "sum(S+D+I)/sum(reference words); competitor/AirCaps - 1",
        "Original condition weighting retained, including overlapping Pipecat/Coval inputs. Failed requests excluded and retained in raw results.",
    )
    add(
        "forced-final-latency",
        "38 ms median; 52 ms p95; 65 ms p99; displayed competitors 2.3–4.1× slower at p95",
        "reproduced_historical_measurement",
        historical,
        "NumPy linear percentiles of successful per-clip ttfs_ms; competitor p95/AirCaps p95",
        "Clock begins after client finalize/commit, not before native end-of-turn detection.",
    )
    add(
        "four-times",
        "Approximately 4× faster than Universal-3.6 and MAI at p95",
        "reproduced_historical_measurement",
        historical,
        "211.3678/51.5055 and 208.0794/51.5055",
    )
    add(
        "tail-versus-median",
        "AirCaps p95 beats every other displayed model's median",
        "reproduced_historical_measurement",
        historical,
        "AirCaps p95 < min(displayed competitor medians)",
    )
    for cohort, text in [
        ("pipecat", "1.52% original Pipecat WER; competitor excess-error chart"),
        ("stt-v3", "1.12% corrected Coval subset WER; competitor excess-error chart"),
        ("livekit-general", "7.02% LiveKit general WER; competitor excess-error chart"),
        (
            "livekit-accented",
            "5.23% LiveKit accented WER; competitor excess-error chart",
        ),
    ]:
        add(
            "wer-" + cohort,
            text,
            "reproduced_historical_measurement",
            historical,
            "Select cohort="
            + cohort
            + "; sum(S+D+I)/sum(reference words); competitor/AirCaps - 1",
            "The original Pipecat card uses conventional WER, not the separate official-harness semantic score.",
        )
    add(
        "scatter-and-comparison-matrix",
        "Original WER-versus-p95 plot and model comparison matrix",
        "reproduced_historical_measurement",
        historical,
        "Coordinates and ratios from the same historical summaries; do not insert official Pipecat aggregates into this pool",
    )
    add(
        "smart-turn",
        "2.21% false endpoints, 96.69% precision; 13.05× fewer false endpoints than Flux, 9.65×/11.30× fewer than AssemblyAI 3.6/3.5",
        "reproduced_selected_operating_point",
        [
            "results/turns/smart_turn/records/",
            "results/turns/smart_turn/events/",
            "datasets/smart-turn-vad-bounds.json",
            "configs/turn_taking.json",
            "results/turns/smart_turn/summary.json",
        ],
        "FP/2718; TP/(TP+FP); comparator FP/AirCaps FP",
        "VAD-aligned 600 ms streaming endpoint diagnostic, not official Smart Turn classifier inference.",
    )
    add(
        "livekit-native-median",
        "301 ms native endpoint median, 12.62% native cutoffs, 98.68% EOT recall, and eligible-span policy columns",
        "reproduced_selected_operating_point",
        [
            "results/turns/livekit/records/",
            "results/turns/livekit/events/",
            "datasets/manifests/livekit-turns.jsonl",
            "configs/turn_taking.json",
            "results/turns/livekit/summary.json",
        ],
        "median(endpoint receipt - annotated true-ending start), conditional on detection",
        "Selected LiveKit settings: 200/.65/3000/.65, mode omitted. Policy columns are independent offline client operating points; the native median is conditional on detection.",
    )
    add(
        "official-pipecat",
        "Mean semantic WER 0.44%, pooled 0.35%, perfect 93.9%, returned 99.7%, TTFS 209/214/223 ms; lowest reported values in six columns",
        "reproduced_database_aggregation_plus_attributed_external_comparison",
        [
            "results/pipecat_stt/results.db",
            "results/pipecat_stt/semantic_wer_traces.jsonl.gz",
            "results/pipecat_stt/upstream-published.json",
            "src/aircaps_benchmarks/pipecat_stats.py",
            "benchmarks/pipecat_stt/",
        ],
        "83/23613 pooled semantic WER; 936/997 perfect; 997/1000 returned; upstream positive-TTFS order statistics",
        "External rows are published aggregates. Input HF revision and 1000 prepared PCM hashes are archived with the original installed versions. Prior-judge NVIDIA accuracy retains its footnote. Does not win returned-transcript rate.",
    )
    add(
        "native-38ms-wording",
        "Caller finished speaking and final transcript in 38 ms",
        "copy_clock_discrepancy",
        historical,
        "38 ms reproduces only the forced-final response clock",
        "The copy combines native turn detection with a client-finalization response time. No benchmark proves native detection plus final transcript in 38 ms.",
    )
    add(
        "livekit-input-count",
        "LiveKit EOT Bench English, 2,288 clips",
        "reproduced_selected_operating_point",
        [
            "datasets/manifests/livekit-turns.jsonl",
            "datasets/manifests/smart-turn.jsonl",
        ],
        "2288 LiveKit clips; 2305 all hold spans, 2158 eligible holds, 1744 true endings",
        "Native cutoffs use all hold spans; policy columns use the eligible-span mask.",
    )
    add(
        "9205-five-benchmarks",
        "9,205 voice-agent clips / five public benchmarks",
        "requires_scope_qualification",
        historical,
        "9211 requests; AirCaps 9205 reference-bearing evaluations; 154661 words",
        "These are clip evaluations with source overlap and repeated acoustic conditions, not 9205 independent calls or five independent corpora.",
    )
    add(
        "universal-superlatives",
        "Fastest, most accurate, #1, alone on Pareto frontier, below every leading API",
        "supported_only_for_named_measurements_and_models",
        historical + ["claims/prices.json"],
        "Compare the eight displayed models at the stated protocol and quoted prices",
        "Does not establish universal superiority across datasets, configurations, current model releases or all APIs.",
    )
    add(
        "price",
        "$0.20/h; displayed competitors $0.22–$0.54/h; 10–170% higher",
        "product_price_and_dated_external_quotes",
        ["claims/prices.json"],
        "competitor quoted hourly price/.20 - 1",
        "Not an inference benchmark result. Legacy AssemblyAI quotes need a dated rate source to be certified as current; no benchmark can prove the cheapest price among every leading API.",
    )
    add(
        "competitor-turn-detection",
        "Native endpoint comparison includes AirCaps, AssemblyAI Universal-3.5/3.6 Pro and Deepgram Flux; ElevenLabs is not evaluated in these comparisons.",
        "comparison_scope",
        ["docs/methodology.md"],
        "No native replay was performed for other displayed model families",
        "Coverage labels refer to these benchmark comparisons, not an exhaustive product capability survey.",
    )
    add(
        "api-and-product-features",
        "WebSocket, framework integration, explicit finalize, English, three modes, free hours and account/data policies",
        "product_contract_not_statistical_measurement",
        [
            "src/aircaps_benchmarks/adapters.py",
            "benchmarks/pipecat_stt/src/stt_benchmark/services.py",
            "configs/turn_taking.json",
            "claims/prices.json",
        ],
        "Runnable integration examples plus dated public product documentation",
        "Benchmark evidence supports the exercised API operations, not account entitlements, privacy policy promises or every future session's behavior.",
    )
    write_json(
        root / "claims/site-claims.json",
        dict(
            page="https://aircaps.ai/models/live-1",
            claims=claims,
            metrics="claims/website-metrics.json",
            scope="Displayed comparisons and all underlying records; no omitted failures or invented trace evidence.",
        ),
    )
    print(
        f"DONE CLAIM MAP {len(claims)} comparison groups with source formulas and scope",
        flush=True,
    )


if __name__ == "__main__":
    build()
