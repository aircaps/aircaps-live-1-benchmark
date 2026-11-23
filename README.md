# AirCaps Live 1 — benchmark evidence

Runner code, adapters, exact input manifests, raw results and scoring behind the
AirCaps Live 1 website comparisons. Source and archived evidence are published at
[aircaps/aircaps-live-1-benchmark](https://github.com/aircaps/aircaps-live-1-benchmark).
The historical conventional-WER evaluation, configured endpoint diagnostics,
and official-harness Pipecat semantic-WER evaluation are separate protocols.
Their clocks and scores are not interchangeable.

<!-- RESULTS:START -->

## November 19 evaluation — conventional WER and forced-final response

These are the archived measurements behind the original website charts. All 9,211 requested clip evaluations are retained; AirCaps has 9,205 WER-scored evaluations and 154,661 reference words. The pool includes overlapping Pipecat/Coval recordings and paired WildASR conditions. It is not a count of independent utterances. Latency starts after client-forced finalization, includes network, and excludes failed requests.

| Model | Pooled WER ↓ | Final response median ms ↓ | p95 ms ↓ | p99 ms ↓ | Failed / 9,211 ↓ |
|---|---:|---:|---:|---:|---:|
| AirCaps Live 1 | **3.65%** | **38** | **52** | **65** | **0** |
| ElevenLabs Scribe v3 Live | 4.10% | 79 | 121 | 191 | **0** |
| MAI Transcribe 2 Streaming | 4.12% | 63 | 208 | 758 | **0** |
| AssemblyAI Universal-3.6 Pro | 4.31% | 99 | 211 | 318 | 3 |
| AssemblyAI Universal-3.5 Pro | 4.42% | 89 | 155 | 210 | 2 |
| ElevenLabs Scribe v2 Realtime | 4.48% | 101 | 146 | 186 | **0** |
| Deepgram Nova 3 | 6.28% | 78 | 128 | 150 | **0** |
| Deepgram Flux | 7.48% | 98 | 168 | 193 | 130 |


## Original Pipecat audio — our conventional-WER protocol

| Model | Pooled conventional WER ↓ |
|---|---:|
| AirCaps Live 1 | **1.52%** |
| AssemblyAI Universal-3.6 Pro | 1.66% |
| ElevenLabs Scribe v3 Live | 1.70% |
| MAI Transcribe 2 Streaming | 1.82% |
| ElevenLabs Scribe v2 Realtime | 1.85% |
| AssemblyAI Universal-3.5 Pro | 1.87% |
| Deepgram Nova 3 | 3.24% |
| Deepgram Flux | 3.55% |


## Coval corrected Pipecat subset — 877 clips

| Model | Pooled conventional WER ↓ |
|---|---:|
| AirCaps Live 1 | **1.12%** |
| AssemblyAI Universal-3.6 Pro | 1.28% |
| ElevenLabs Scribe v3 Live | 1.32% |
| MAI Transcribe 2 Streaming | 1.39% |
| ElevenLabs Scribe v2 Realtime | 1.41% |
| AssemblyAI Universal-3.5 Pro | 1.44% |
| Deepgram Nova 3 | 2.65% |
| Deepgram Flux | 3.07% |


## LiveKit general — 400 clips

| Model | Pooled conventional WER ↓ |
|---|---:|
| AirCaps Live 1 | **7.02%** |
| MAI Transcribe 2 Streaming | 7.60% |
| Deepgram Nova 3 | 8.08% |
| Deepgram Flux | 8.20% |
| AssemblyAI Universal-3.6 Pro | 8.36% |
| AssemblyAI Universal-3.5 Pro | 8.57% |
| ElevenLabs Scribe v2 Realtime | 8.86% |
| ElevenLabs Scribe v3 Live | 9.02% |


## LiveKit accented — 800 requests, 798 references

| Model | Pooled conventional WER ↓ |
|---|---:|
| AirCaps Live 1 | **5.23%** |
| ElevenLabs Scribe v3 Live | 5.85% |
| ElevenLabs Scribe v2 Realtime | 6.11% |
| Deepgram Nova 3 | 6.94% |
| MAI Transcribe 2 Streaming | 7.90% |
| AssemblyAI Universal-3.6 Pro | 8.15% |
| AssemblyAI Universal-3.5 Pro | 8.49% |
| Deepgram Flux | 8.99% |


## Pipecat Smart Turn streaming endpoint diagnostic — 600 ms

5,367 natural-English clips: 2,649 complete and 2,718 incomplete. This is a VAD-aligned streaming STT endpoint diagnostic, not official classifier inference. The selected AirCaps configuration omits mode; see configs/turn_taking.json.

| Model | Accuracy ↑ | Complete-turn recall ↑ | Precision ↑ | F1 ↑ | False endpoints / incomplete ↓ | Matched median ms ↓ |
|---|---:|---:|---:|---:|---:|---:|
| AirCaps Live 1 | **82.21%** | **66.21%** | **96.69%** | **78.60%** | **2.21%** | **209** |
| AssemblyAI Universal-3.5 Pro | 70.54% | 65.91% | 72.03% | 68.84% | 24.94% | 319 |
| AssemblyAI Universal-3.6 Pro | 71.90% | 64.93% | 74.82% | 69.52% | 21.30% | 337 |
| Deepgram Flux | 61.95% | 52.47% | 63.97% | 57.65% | 28.81% | 214 |


## Pipecat Smart Turn streaming endpoint diagnostic — 1,000 ms

5,367 natural-English clips: 2,649 complete and 2,718 incomplete. This is a VAD-aligned streaming STT endpoint diagnostic, not official classifier inference. The selected AirCaps configuration omits mode; see configs/turn_taking.json.

| Model | Accuracy ↑ | Complete-turn recall ↑ | Precision ↑ | F1 ↑ | False endpoints / incomplete ↓ | Matched median ms ↓ |
|---|---:|---:|---:|---:|---:|---:|
| AirCaps Live 1 | **87.83%** | **78.78%** | **95.82%** | **86.47%** | **3.35%** | **248** |
| AssemblyAI Universal-3.5 Pro | 71.46% | 75.01% | 69.55% | 72.18% | 32.01% | 340 |
| AssemblyAI Universal-3.6 Pro | 73.23% | 75.73% | 71.64% | 73.63% | 29.21% | 376 |
| Deepgram Flux | 59.34% | 73.12% | 56.85% | 63.97% | 54.08% | 316 |


## LiveKit turn detection — selected configuration

2,288 English clips; 2,305 all hold spans, 2,158 eligible hold spans, and 1,744 true endings. AirCaps: minimum silence 200 ms, EOU threshold .65, maximum silence 3,000 ms, VAD .65; mode omitted. Native cutoff rate uses all hold spans. Policy columns use the official eligible-span mask and independently optimize a client policy at the fixed backend configuration. Delays include network; native median is conditional on detected true endings.

| Model | Native cutoffs ↓ | EOT recall ↑ | Native median ms ↓ | Mean delay at ≤5% cutoffs ms ↓ | At ≤10% ms ↓ | Cutoffs at ≤600 ms mean ↓ | At <1,000 ms mean ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| AirCaps Live 1 | **12.62%** | **98.68%** | **301** | **1,320** | 756 | 15.38% | **6.35%** |
| AssemblyAI Universal-3.5 Pro | 30.89% | 97.71% | 342 | 2,000 | 1,022 | 25.35% | 10.38% |
| AssemblyAI Universal-3.6 Pro | 20.22% | 97.25% | 390 | 2,000 | 954 | 20.67% | 9.55% |
| Deepgram Flux | 13.32% | 94.44% | 383 | 1,379 | **743** | **11.96%** | 7.23% |


## Pipecat STT — official-harness semantic WER and TTFS

Our completed November 22 AirCaps run used the public production API from Atlanta. The SQLite database, semantic edits, judge conversations and sanitized logs are included. External rows are rounded published aggregates from the [pinned public Pipecat table](https://github.com/pipecat-ai/stt-benchmark/blob/d4d85a9ec7d3465671ae5e18bf725c013cdfb4ca/README.md). They were not collected by this project on a common client.

| Model | Mean semantic WER ↓ | Pooled semantic WER ↓ | Perfect transcripts ↑ | TTFS median ms ↓ | p95 ms ↓ | p99 ms ↓ | Returned ↑ |
|---|---:|---:|---:|---:|---:|---:|---:|
| AirCaps Live 1 | **0.44%** | **0.35%** | **93.88%** | **209** | **214** | **223** | 99.70% |
| AssemblyAI — universal-3-6-pro | 0.89% | 0.80% | 88.70% | 307 | 401 | 498 | 99.90% |
| AssemblyAI — universal-3-5-pro | 1.12% | 0.95% | 86.00% | 282 | 354 | 393 | 99.90% |
| AssemblyAI — universal-streaming-english | 2.81% | 2.42% | 66.80% | 256 | 362 | 417 | 99.80% |
| AWS — N/A | 1.26% | 1.35% | 79.10% | 1,136 | 1,527 | 1,897 | **100.00%** |
| Azure — N/A | 0.98% | 1.01% | 83.50% | 1,016 | 1,345 | 1,791 | **100.00%** |
| Cartesia — ink-2 | 1.14% | 1.02% | 83.60% | 299 | 328 | 1,584 | **100.00%** |
| Cartesia — ink-whisper | 3.32% | 3.78% | 61.40% | 266 | 364 | 898 | 99.90% |
| Deepgram — nova-3-general | 1.32% | 1.37% | 77.70% | 247 | 298 | 326 | 99.80% |
| ElevenLabs — scribe_v2_realtime | 3.05% | 3.13% | 80.30% | 281 | 348 | 407 | 99.70% |
| Google — gemini-3.5-transcribe-live | 1.93% | 1.97% | 78.30% | 458 | 532 | 599 | 99.90% |
| Google — latest-long | 2.46% | 2.46% | 69.70% | 878 | 1,155 | 1,570 | **100.00%** |
| Gradium — default | 3.81% | 3.79% | 65.60% | 585 | 614 | 623 | 99.30% |
| Meta — muse-voice-transcribe-1.0 | 0.80% | 0.73% | 89.50% | 392 | 1,292 | 1,922 | 99.90% |
| Mistral — voxtral-mini-transcribe-realtime-2602 | 4.49% | 5.11% | 67.70% | 525 | 973 | 1,913 | 99.30% |
| NVIDIA — Nemotron 3.0 ASR (en) † | 1.90% | 1.95% | 76.10% | 221 | 238 | 252 | **100.00%** |
| NVIDIA — Nemotron 3.5 ASR (multilingual) † | 4.54% | 4.58% | 62.00% | 236 | 253 | 266 | 99.60% |
| OpenAI — gpt-4o-transcribe | 3.10% | 2.95% | 75.70% | 637 | 965 | 1,655 | 99.30% |
| OpenAI — gpt-realtime-whisper | 2.41% | 2.30% | 73.30% | 740 | 878 | 1,080 | **100.00%** |
| Smallest AI — pulse | 1.85% | 1.94% | 74.00% | 398 | 533 | 1,593 | **100.00%** |
| Speechmatics — linden-1 | 1.11% | 0.96% | 83.90% | 369 | 438 | 690 | 99.50% |
| Speechmatics — N/A | 1.17% | 0.96% | 83.10% | 495 | 676 | 736 | 99.70% |
| xAI — grok-voice-transcribe-2.0 | 1.12% | 0.79% | 89.40% | 1,322 | 1,895 | 2,148 | 99.80% |

AirCaps: 83 semantic edits / 23,613 reference words; 936 perfect / 997 returned; 1,000 attempted. Current-judge references and judge identifiers match. Dataset revision 847083fbabb4fbcfae7fe71f24961acdb03de4e3, all 1000 prepared-audio hashes and the original installed package versions are archived. Client distance 1.7 ms is the run operator's reported measurement. † NVIDIA accuracy rows retain the upstream previous-judge qualification and are excluded from current-judge accuracy highlights. No semantic score is pooled with conventional WER.


Bold indicates the best observed value in each displayed comparison, not statistical significance. See [claim mapping](../claims/README.md) for source formulas and measurement scope.

<!-- RESULTS:END -->

## Reproduce the archived results offline

Python 3.12 and uv are required. No provider or judge calls run here:

```bash
uv sync --frozen
uv run aircaps-bench score --track all
uv run aircaps-bench report
uv run python tools/audit_release.py
```

WER is recomputed from references and transcripts, verifying every saved edit
count, original cohort summary and pooled latency percentile. Endpoint metrics
are recomputed from native events. Pipecat semantic edits are reaggregated from
SQLite using its upper-middle positive-latency convention. Its judge conversations
are retained; running the judge again requires API access and may change judgments.

See [claim mapping](claims/README.md), [machine-readable claims](claims/site-claims.json),
[methodology](docs/methodology.md), [configs](configs/turn_taking.json), and
[attribution](NOTICE.md). The mapping records formulas, input locations and the measurement scope of each
comparison. See the methodology for timing definitions and dataset overlap.

## Archive layout

| Location | Contents |
|---|---|
| `datasets/manifests/historical-asr.jsonl` | All 9,211 requested historical inputs, references, boundaries and PCM hashes |
| `datasets/coval-manifests/` | Exact corrected manifests, source WAV hashes and provenance |
| `results/historical/asr/records/` | Complete transcripts, edit counts, timing, failures and status |
| `results/historical/asr/events/` | Available original timestamped server messages and send clocks |
| `results/turns/` | The two page-relevant endpoint operating points and raw evidence |
| `results/pipecat_stt/results.db` | Samples, references, outputs, semantic edits, judge traces and run metadata |
| `results/pipecat_stt/*.jsonl.gz` | Readable SQLite table exports |
| `results/pipecat_stt/logs/` | Sanitized completed-run logs |
| `results/pipecat_stt/upstream-published.json` | Commit-pinned external aggregates with judge qualifications |

The historical pool contains both the original 1,000 Pipecat clips and 877
Coval-derived versions, plus paired WildASR conditions, LiveKit and PriMock57.
This preserves the original weighting; it is not a deduplicated independent-call
score. Failures are retained and excluded from WER under the original rule.
Flux's forced-final timeouts limit interpretation of surviving-request WER.

Every result record is present. Some original message traces were recovered from
exactly matching cached pilot requests, not new replays. One additional original
trace was recovered from valid output preceding a damaged gzip chunk and verified
against its transcript and timing record. Twenty-one historical competitor message
traces remain missing, listed in
`provenance/historical-export.json`. AirCaps message coverage is complete.

## Replay the historical protocol

Audio is not bundled in Git. Choose external or cloud storage explicitly:

```bash
cp .env.example .env
uv run aircaps-bench prepare --track historical/asr \
  --audio-dir /mnt/benchmark/audio --cache-dir /mnt/benchmark/cache
uv run aircaps-bench run --track historical/asr \
  --model aircaps_aircaps-live-1 --concurrency 4 \
  --audio-dir /mnt/benchmark/audio --output-dir ./replays/example
uv run aircaps-bench score --track historical/asr --results-dir ./replays/example
```

Tracks: `historical/asr`, `turns/livekit`, `turns/smart_turn`. Downloaders verify
prepared PCM hashes. Archived manifests pin the exact selection, references and
PriMock intervals. Do not regenerate corrected Coval manifests using an older
build recipe. AirCaps is capped at four streams, with a process lock. New replay
outputs cannot overwrite this archive.

## Replay Pipecat's official protocol

```bash
cd benchmarks/pipecat_stt
cp env.example .env
uv sync --frozen
STT_BENCHMARK_DATASET_REVISION=847083fbabb4fbcfae7fe71f24961acdb03de4e3 \
  uv run stt-benchmark download --num-samples 1000
uv run stt-benchmark ground-truth import ground_truth/2026-01-03_17-00-06.jsonl
uv run stt-benchmark run --services aircaps_live_1
uv run stt-benchmark wer --services aircaps_live_1
uv run stt-benchmark update-readme
```

Code: upstream `d4d85a9` plus AirCaps integration `3677567`. Inference, VAD, judge
and aggregation algorithms are retained. The integration lock uses Pipecat
1.16.0; upstream base used 1.12.0. The actual resolved dataset commit is
`847083fbabb4fbcfae7fe71f24961acdb03de4e3`, recovered from the original client's
cache lock filename. All 1000 streamed PCM hashes, byte lengths, durations and
input identities are retained in `results/pipecat_stt/input_manifest.json`.
Original installed package versions are in `results/pipecat_stt/dependency_versions.txt`;
they describe the actual client and may differ from a fresh lockfile install.
Use the recorded commit and verify regenerated audio against those hashes.
External rows are upstream aggregates; their per-clip databases are not available upstream.

## AirCaps endpoint settings on the page

| Evaluation | Settings |
|---|---|
| Smart Turn, 600 / 1,000 ms | EOU true; minimum silence 80 ms; threshold .65; maximum silence 1,800 ms; VAD .30; mode omitted |
| LiveKit full | EOU true; minimum silence 200 ms; threshold .65; maximum silence 3,000 ms; VAD .65; mode omitted |

These are different fixed operating points. No parameter-search history is
included. Credentials, quotas and private deployment identifiers are removed;
scoring inputs and failures are preserved. Fresh API runs can differ as production
models, network conditions and LLM judgments change.
