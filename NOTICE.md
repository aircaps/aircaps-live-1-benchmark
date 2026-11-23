# Attribution and licenses

New benchmark glue, adapters, preprocessing and reporting use the root
BSD-2-Clause license. Third-party code and datasets retain their own licenses.

| Component | Source / pin | License |
|---|---|---|
| Pipecat STT harness | https://github.com/pipecat-ai/stt-benchmark at `d4d85a9`; AirCaps integration `3677567` | BSD-2-Clause; copyright Daily |
| Pipecat published reference table | Commit and source URL in `results/pipecat_stt/upstream-published.json`; entries retained with qualifications | Upstream BSD-2-Clause; published aggregates, not our raw runs |
| Pipecat confusion metrics | https://github.com/pipecat-ai/smart-turn at `4e12f2bbef04e47c348836f57100885f6973a5ae`; function extracted without algorithm changes | BSD-2-Clause; copyright Daily |
| LiveKit policy scorer | https://github.com/livekit/eot-bench at `81078c0962e89bc03c74620f71127829b1aac812`; metrics.py unmodified | Apache-2.0 |
| Conventional WER normalizer v4 | https://github.com/coval-ai/benchmarks; archived wer.py SHA-256 `51755275911e965f702d361015947b9c6af45f25acbc3e5e1d626ee4244807fa` | Apache-2.0; copyright2026 Coval Benchmarks Authors |
| Pipecat STT input audio/labels | https://huggingface.co/datasets/pipecat-ai/smart-turn-data-v3.1-train; at 847083fbabb4fbcfae7fe71f24961acdb03de4e3 | CC BY4.0 |
| LiveKit audio, labels and aligned words | https://huggingface.co/datasets/livekit/eot-bench-data at `ae834af9e9bddf73d1f550c190aaeb99bf31f523` | CC BY4.0 |
| Smart Turn v3.2 test audio/labels | https://huggingface.co/datasets/pipecat-ai/smart-turn-data-v3.2-test at `dfc179241fee65b0efe81ca37786f41ce26f38ec` | CC BY4.0 |

Dataset contributors credited upstream include the Pipecat team, Liva AI,
Midcentury and MundoAI. Source cards and background-noise attribution are retained
in `licenses/dataset-cards/`. Dataset content is not relicensed as BSD software.

The Pipecat public copy excludes the out-of-scope provider from registry, enum,
credential template, dependency extras and examples; it adds optional input-
revision pinning. The upstream processing/timing/judge algorithms are retained.
Its AirCaps dependency lock is based on the adapter commit, including the
Pipecat1.16.0 upgrade required by that integration. The original source checkout
are unchanged.

The core LiveKit/endpoint runner is adapted from our recorded code with portable
paths, explicit CLI commands, a local four-stream AirCaps lock, sanitized output
and the two fixed selected endpoint profiles. PCM conversion, aligned-word
references, English/non-synthetic selection, confidence conversion and scoring
are open. Credential/quota/private-host/stage redactions do not alter local
transcription, timing, endpoint labels or metric inputs. No endorsement by
upstream projects or providers is implied.

External Pipecat rows are explicitly attributed rounded aggregates. No per-clip
transcripts, judge traces, exact counts or independent raw-run reproduction is
claimed for those entries. Their prior-judge qualifications remain visible.


Historical supporting data also includes:

| Component | Source / pin | License |
|---|---|---|
| Original Pipecat 1,000-clip audio/references | pipecat-ai/stt-benchmark-data at ea9d721efd21d6a15d7956f804070ac560936fda | CC-BY-4.0, as stated in the pinned dataset card |
| Coval corrected manifests | Archived v1.1.0 JSONs and source SHA-256 hashes under datasets/coval-manifests | Original manifest notices retained; underlying Pipecat card states CC-BY-4.0 despite older manifest metadata saying unspecified |
| WildASR condition inputs | bosonai/WildASR, selected by the frozen Coval manifests | Apache-2.0; FLEURS-derived audio CC-BY-4.0 |
| PriMock57 audio and transcripts | babylonhealth/primock57 at cd2ac707ad03cb4d2531f4ec6b90c659bf4357c5 | CC-BY-4.0 |

Attribution includes the Pipecat community contributors, Coval Benchmarks
Authors, the WildASR authors and FLEURS contributors, and Papadopoulos Korfiatis
et al. (2022), PriMock57: A Dataset of Primary Care Mock Consultations.
Audio is fetched from its pinned sources into external storage rather than
bundled or relicensed as BSD code.
