import gzip
import importlib.util
import json
from pathlib import Path


def test_valid_original_rows_survive_a_corrupted_gzip_footer(tmp_path):
    source = Path(__file__).resolve().parents[1] / "tools/recover_cached_asr_traces.py"
    spec = importlib.util.spec_from_file_location("recover_archive", source)
    recovery = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recovery)
    expected = [{"id": str(i), "text": "original response"} for i in range(20)]
    data = bytearray(
        gzip.compress("".join(json.dumps(r) + "\n" for r in expected).encode())
    )
    data[-8] ^= 0xFF  # Damage the checksum; do not modify the original JSON payload.
    path = tmp_path / "interrupted.jsonl.gz"
    path.write_bytes(data)
    assert list(recovery.readable_members(path)) == expected
