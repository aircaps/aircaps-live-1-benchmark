"""Fetch a commit-pinned public README reference table; never publish or run APIs."""

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aircaps_benchmarks.pipecat_public import snapshot_upstream


def fetch(url):
    with urllib.request.urlopen(
        urllib.request.Request(
            url, headers={"User-Agent": "aircaps-benchmark-source-snapshot"}
        ),
        timeout=20,
    ) as response:
        return response.read().decode()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--commit")
    a = p.parse_args()
    commit = (
        a.commit
        or json.loads(
            fetch("https://api.github.com/repos/pipecat-ai/stt-benchmark/commits/main")
        )["sha"]
    )
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("Use a full upstream commit SHA")
    base = "https://raw.githubusercontent.com/pipecat-ai/stt-benchmark/" + commit + "/"
    snapshot = snapshot_upstream(
        ROOT,
        commit,
        fetch(base + "README.md"),
        fetch(base + "LICENSE"),
        datetime.now(timezone.utc).isoformat(),
    )
    print(
        "SNAPSHOT",
        commit,
        len(snapshot["rows"]),
        "external aggregate rows; no raw third-party runs implied",
        flush=True,
    )


if __name__ == "__main__":
    main()
