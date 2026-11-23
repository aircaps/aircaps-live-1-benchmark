# Pipecat STT benchmark

Vendored from pipecat-ai/stt-benchmark at d4d85a9, with the AirCaps Live 1 adapter commit 3677567. Local public-benchmark edits exclude an out-of-scope provider from the registry, credentials template, dependency extras, and examples. The input processing, timing, semantic judge, and score calculations are retained.

The November 22 AirCaps Live 1 run is complete. Its sanitized SQLite database, judge traces, logs and source README row are archived under results/pipecat_stt at the repository root. Its semantic WER is separate from the historical conventional-ASR suite.

See the repository root README for reproduction and import commands. Upstream license: BSD-2-Clause; see LICENSE.

For a pinned reproduction, set STT_BENCHMARK_DATASET_REVISION to the actual run dataset commit. This optional public-copy setting defaults to None and does not alter the original run when unset.
