---
license: cc-by-4.0
configs:
- config_name: all
  default: true
  data_files:
  - split: validation
    path: data/*/validation-*.parquet
- config_name: en
  data_files:
  - split: validation
    path: data/en/validation-*.parquet
- config_name: ar
  data_files:
  - split: validation
    path: data/ar/validation-*.parquet
- config_name: de
  data_files:
  - split: validation
    path: data/de/validation-*.parquet
- config_name: es
  data_files:
  - split: validation
    path: data/es/validation-*.parquet
- config_name: fr
  data_files:
  - split: validation
    path: data/fr/validation-*.parquet
- config_name: hi
  data_files:
  - split: validation
    path: data/hi/validation-*.parquet
- config_name: id
  data_files:
  - split: validation
    path: data/id/validation-*.parquet
- config_name: it
  data_files:
  - split: validation
    path: data/it/validation-*.parquet
- config_name: ja
  data_files:
  - split: validation
    path: data/ja/validation-*.parquet
- config_name: ko
  data_files:
  - split: validation
    path: data/ko/validation-*.parquet
- config_name: nl
  data_files:
  - split: validation
    path: data/nl/validation-*.parquet
- config_name: pt
  data_files:
  - split: validation
    path: data/pt/validation-*.parquet
- config_name: tr
  data_files:
  - split: validation
    path: data/tr/validation-*.parquet
- config_name: zh
  data_files:
  - split: validation
    path: data/zh/validation-*.parquet
tags:
- eot
- turn-detection
- conversational
---

# LiveKit EoT Benchmark

This dataset contains a minimal public subset of the LiveKit end-of-turn
benchmark. It is sampled from the full release-ready dataset preserved on the
`full` revision.

## Links

- Blog post: [Solving end-of-turn detection](https://livekit.com/blog/solving-end-of-turn-detection)
- Benchmark code: [github.com/livekit/eot-bench](https://github.com/livekit/eot-bench)

The sample is deterministic: up to 400 turns per language were sampled
without replacement using seed `20260603`. Languages with fewer than the requested sample size include all available rows: `ar` (381 available), `id` (396 available), `ja` (356 available), `ko` (377 available), `zh` (344 available).

## Configs

- `all`: all available sampled languages.
- Language configs such as `en`, `de`, and `ja`: one language only.

All configs use the same schema. English rows include `language = "en"`.

## Version 1.1

Version 1.1 adds 1,888 English rows in two cohorts and two schema fields.

- `accented`: 800 turns of accented English speech.
- `short_turns`: 1,088 short replies. 544 rows end at the end of the turn. The
  other 544 rows stop at a mid-turn pause, so they have no end-of-turn span.

Each silence span now has a `label`, and each row has a `cohort`. The rows from
the first release are unchanged apart from these two fields. Their cohort is
`general`.

## Schema

- `id`: globally unique turn id.
- `audio`: 16 kHz mono WAV audio.
- `language`: normalized language code.
- `duration`: audio duration in seconds.
- `silence_spans`: candidate silence spans with `start`, `end`, and `label`.
  The label is `eot` for the true end of the turn and `hold` for a mid-turn
  pause. A row has at most one `eot` span, and it is always the last span. A
  `short_turns` row can end in a `hold` span.
- `words`: word-level transcript timings.
- `messages`: prior conversation messages. Rows in the `accented` and
  `short_turns` cohorts contain only the preceding assistant message.
- `cohort`: `general`, `accented`, or `short_turns`.

In the `general` cohort, rows whose final end-of-turn silence span is shorter
than 0.2s are excluded, so every turn can be evaluated at a 0.2s score point.
Rows with any silence span longer than 5.0s are also excluded so the benchmark
focuses on ordinary endpointing pauses. The `accented` cohort keeps longer
mid-turn pauses; the benchmark harness ignores `hold` spans longer than 5.0s.

## Languages

The `en` count is 400 `general` rows, 800 `accented` rows, and 1,088
`short_turns` rows.

| Language | Rows |
| --- | ---: |
| `en` | 2288 |
| `ar` | 381 |
| `de` | 400 |
| `es` | 400 |
| `fr` | 400 |
| `hi` | 400 |
| `id` | 396 |
| `it` | 400 |
| `ja` | 356 |
| `ko` | 377 |
| `nl` | 400 |
| `pt` | 400 |
| `tr` | 400 |
| `zh` | 344 |
| `all` | 7342 |