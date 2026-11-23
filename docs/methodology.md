# Measurement methodology

## Historical conventional WER and forced-final response

One EC2 c7i.4xlarge client in AWS us-east-2 streamed the same selected audio in
real time. Session readiness precedes playback. Absolute deadlines use 20 ms
chunks for AirCaps, ElevenLabs and MAI, 80 ms for Flux, and 100 ms for AssemblyAI.
Source audio is decoded to float32, averaged across channels, resampled with
`scipy.signal.resample_poly` when needed, clipped to [-1,.999969], multiplied by
32768 and converted to PCM16. PriMock's PCM16 channels are cut directly at rounded
annotated sample offsets. Manifests retain exact prepared PCM hashes.

| Group | Requests | AirCaps reference words |
|---|---:|---:|
| Original Pipecat | 1,000 | 23,734 |
| Coval corrected Pipecat | 877 | 20,377 |
| WildASR English conditions | 2,506 | 42,287 |
| LiveKit speech-bearing clips | 1,744 | 19,130 |
| PriMock57 utterances | 3,084 | 49,133 |

Coval's 877 clips derive from the original Pipecat pool. WildASR clean and five
degraded conditions share 277 underlying utterances; 844 accent clips are
separate. The original pooled score retains this weighting and is not a count
of independent calls. Six LiveKit requests have no usable aligned-word reference.
Failed or pacing-invalid requests are excluded from WER and reported separately.
Flux has 130 forced-finalization failures; its surviving-request WER is provisional.

Conventional WER uses the exact vendored Coval v4 normalizer,
`whisper-normalizer==0.1.12` and `jiwer==4.0.0`. The scorer recomputes each saved
S/D/I count and pools sum(S+D+I)/sum(reference words), not mean clip WER.

ASR playback stops at the recorded speech boundary. The latency clock starts
immediately after the client sends finalize/commit and ends at the last final
transcript. It includes network but excludes connection setup and a separate
VAD/endpoint decision. Some groups use file end as the supplied boundary, not an
independently measured final speech sample. Already-final outputs are clamped
to zero and marked. NumPy linear percentiles round AirCaps's
37.554/51.506/64.700 ms to the page's 38/52/65 ms.

| Model | Historical ASR | Native endpoint evaluation |
|---|---|---|
| AirCaps Live 1 | EOU disabled, client finalize, public endpoint lookup | Selected LiveKit and Smart Turn configurations below |
| AssemblyAI Universal-3.5/3.6 Pro | min_latency, EOU confidence 1.0 | balanced, no explicit overrides |
| Deepgram Flux | threshold 1.0, timeout 60,000 ms, ForceEndTurn | threshold .7, timeout 5,000 ms |
| Deepgram Nova-3 | English, interim results, endpointing disabled, Finalize | Not evaluated |
| ElevenLabs Scribe v2/v3 | English PCM16, manual commit, timestamps disabled | Not evaluated |
| MAI Streaming | PCM16/16kHz, turn_detection null, client commit | Not evaluated |

Historical per-model limits: 4 AirCaps, 22 ElevenLabs, 12 AssemblyAI, 35 Deepgram,
4 MAI; account gates/start pacing were shared. Public replay uses one model per
invocation and caps AirCaps at four. No new streams reconstructed this archive.

## Page endpoint operating points

Native playback preserves pauses and adds two seconds of silence. The selected
LiveKit configuration uses 2,288 English clips, 1,744 true endings and 2,305 hold
spans. Minimum silence is 200 ms, EOU threshold .65, maximum silence 3,000 ms,
VAD .65, and mode is omitted. Delay is endpoint receipt minus annotated true-ending
start; its 301 ms median is conditional on detection, with misses in recall.
Native cutoffs divide false hold decisions by all 2,305 holds. Client-policy
columns use the official 2,158 eligible hold mask and the pinned EOT Bench grid:
confidence 0–1 in .01 increments, action delay .2–1.0 s in .1 increments, fallback
1–3.5 s in .5 increments. Each column independently optimizes a client policy
at the fixed backend configuration; mean delay includes timeout fallback.
Predictions can be rebuilt from original timestamped confidence messages using
`uv run aircaps-bench score --track turns/livekit --rebuild-predictions`.

Smart Turn uses all 5,367 natural English test clips: 2,649 complete and 2,718
incomplete. WebRTC VAD mode 2 on 20 ms frames estimates final speech. An endpoint
from 250 ms before that boundary through the stated 600 or 1,000 ms budget counts as positive.
FP/incomplete and TP/(TP+FP) produce the page's false-endpoint and precision
metrics. Pipecat's helper names FP/all a false-positive rate; that distinct
formula is preserved in the summary. This is a streaming STT diagnostic, not
the official Smart Turn classifier inference protocol. Existing trailing file
silence is included; endpoints during it are not discarded.

Smart Turn AirCaps settings: EOU true; minimum silence 80 ms; threshold .65;
maximum silence 1,800 ms; VAD .30; no mode field. LiveKit and Smart Turn use
different selected server configurations; both are disclosed in the tables.

## Official-harness Pipecat, November 22

AirCaps ran against production through the public API from Atlanta. The operator
reports a 1.7 ms client-to-endpoint distance. Upstream `d4d85a9` plus integration
`3677567` retains the inference, VAD, judge and aggregation algorithms. The local
public copy narrows registration and adds optional revision pinning. The
integration lock upgrades Pipecat from 1.12.0 to 1.16.0.

The harness selects 1,000 English non-synthetic inputs with streaming shuffle
seed 42 from smart-turn-data-v3.1-train. Imported reviewed references match the
canonical reference/notes files. The recorded judge is Claude Sonnet 5.5,
medium effort, one repeat, prompt revision d739a9b1. The resolved HF revision is
`847083fbabb4fbcfae7fe71f24961acdb03de4e3`, recovered from the original client cache
lock filename. The Hub reports this commit last changed September 29, before
the runs. Seed 42, offset 0 and first1000 samples are recorded. The manifest
contains the SHA-256, bytes, duration, sample ID and dataset index of every
prepared PCM file streamed by the original client; all IDs, indices and durations
match the archived SQLite database. These are original client-supplied hashes,
not new hashes of audio downloaded on this Mac. The client's recorded installed
package versions are archived alongside the input manifest; no runtime versions
are inferred from the source lockfile.

TTFS is last-final receipt minus VAD-estimated speech end, accounting for the
200 ms VAD stop delay. It includes native finalization behavior, unlike the
historical forced-final clock. Upstream aggregation selects the upper-middle
positive TTFS and integer percentile indices. Mean semantic WER averages clip
scores; pooled semantic WER sums edits over words. Perfect rate divides zero-error
scored outputs by scored outputs; returned rate divides nonempty outputs by attempts.

There are 1,000 attempts, 997 scored outputs, 936 perfect outputs, 83 errors and
23,613 scored reference words. The source SQLite is read-only; its sanitized
copy, table exports and judge conversations are retained. Semantic WER is never
pooled with historical conventional WER.

External rows are pinned upstream aggregates, not common-client reruns. Raw
competitor databases, network conditions and exact input identities are not
provided upstream. NVIDIA retains its previous-judge footnotes, without a guessed
correction. Best-value highlights are point estimates, not significance tests.
