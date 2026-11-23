# Comparison evidence and scope

`site-claims.json` maps comparison groups to source artifacts and formulas.
`website-metrics.json` contains values generated from recomputed archived results
and the pinned upstream Pipecat reference table. Website chart/rendering code
is maintained separately; it is not required to reproduce the benchmark scores.

```bash
uv run aircaps-bench score --track all
uv run aircaps-bench report
uv run python tools/build_claim_map.py
uv run python tools/audit_release.py
```

## Measurement definitions

- Historical final-response latency starts after client finalization. It does
  not include the preceding VAD or native turn-detection decision.
- The pool has 9,211 requests and 9,205 reference-bearing AirCaps evaluations.
  Pipecat/Coval recordings overlap and WildASR conditions share utterances;
  the score preserves the original condition weighting.
- Conventional WER is recomputed from complete references and saved transcripts.
  Every per-request result is present. Original message traces are unavailable
  for 21 historical competitor requests, limiting timestamp-level verification
  for those requests; their saved latency values remain in the aggregates.
- Selected LiveKit and Smart Turn runs use separately documented AirCaps settings.
  The native LiveKit median is conditional on a detected ending; recall reports
  misses. Policy columns independently optimize a client decision rule.
- Smart Turn measurements are streaming endpoint diagnostics, not official
  classifier-inference results. False endpoints divide by incomplete clips;
  the separate Pipecat helper formula divides FP by all clips.
- Native endpoint comparisons include AirCaps, AssemblyAI Universal-3.5/3.6 Pro
  and Deepgram Flux. ElevenLabs is not included in turn-detection comparisons.
- External Pipecat rows are upstream-published aggregates, not this project's
  common-client recordings. Their judge qualifications remain attached.
- Product prices are separately sourced dated quotes, not inference measurements.
  Performance conclusions apply to the stated models, inputs and operating points.

All underlying input/result records supporting the pooled score remain available,
including failures and cohorts where AirCaps does not lead. Best-value highlights
are observed point estimates, not significance tests. Offline scores reproduce
from the archive; fresh production API calls may differ as models, networks and
LLM judgments change.
