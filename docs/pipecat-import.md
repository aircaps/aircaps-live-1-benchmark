# Pipecat completed run import

The November 22 run has been imported read-only. Future imports should preserve:

- A consistent SQLite snapshot of `stt_benchmark_data/results.db`, including
  samples, references, transcripts, timing rows, semantic edit counts and judge traces.
- The run logs and updated README.
- Exact local Git commit, dependency lock, installed package versions, command
  line, seed, input count and client region/network observations.
- The actual Hugging Face dataset revision used by that run. Read it from that
  run's metadata/cache before deleting its machine; do not substitute today's SHA.
- Preferably a sample-ID-to-PCM-SHA-256 inventory of the 1,000 prepared inputs.

For an active database, use SQLite's backup API instead of copying a lone `.db`
while a WAL writer is active. A completed, closed database can be copied normally.

```bash
uv run python tools/import_pipecat_results.py /path/to/completed/results.db \
  --dataset-revision ACTUAL_HF_COMMIT \
  --logs-dir /path/to/logs --source-readme /path/to/README.md
uv run aircaps-bench report
uv run python tools/audit_release.py
```

The importer reads the source without writing to it. It creates a sanitized SQLite
database and compressed JSONL views, scoped to AirCaps Live 1 only. Credential
fields inside serialized configuration snapshots are removed; local audio paths
become portable relative paths. References, transcripts, semantic edits and judge
conversations are retained. Missing dataset revision information is explicitly
recorded, not fabricated. The main table is generated from the imported semantic-WER rows. No public upload or Git push is performed by these tools.

External main-table rows come from the commit-pinned upstream README snapshot,
never from other services in this imported database. Preserve the actual judge
identifier and reviewed references: unknown compatibility is marked explicitly.
