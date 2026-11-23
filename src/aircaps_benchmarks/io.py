"""Portable manifests, compressed records, and credential-free output."""

import gzip
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MANIFESTS = {
    "historical/asr": "historical-asr.jsonl",
    "turns/livekit": "livekit-turns.jsonl",
    "turns/smart_turn": "smart-turn.jsonl",
}


def json_rows(path):
    path = Path(path)
    with gzip.open(path, "rt") if path.suffix == ".gz" else path.open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def manifest(track, root=REPO):
    return {
        r["id"]: r
        for r in json_rows(Path(root) / "datasets/manifests" / MANIFESTS[track])
    }


def records(path):
    return {r["id"]: r for r in json_rows(path)}


def clean(value):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            lower = k.lower()
            if lower in {
                "api_key",
                "authorization",
                "x-api-key",
                "xi-api-key",
                "access_token",
                "refresh_token",
                "secret",
                "quota_ms",
                "used_ms",
                "provider_remaining_hours",
                "stage",
                "token",
                "aws_access_key_id",
                "aws_secret_access_key",
                "aws_session_token",
                "client_secret",
            } or lower.endswith(("_api_key", "_access_token", "_refresh_token")):
                continue
            if (
                lower
                in {
                    "data_dir",
                    "audio_dir",
                    "results_db",
                    "google_application_credentials",
                }
                and isinstance(v, str)
                and v.startswith(("/", "~"))
            ):
                out[k] = "<LOCAL_PATH>"
                continue
            if k == "endpoint_host" and isinstance(v, str) and ".azure." in v:
                out[k] = "<MAI_HOST>"
            else:
                out[k] = clean(v)
        return out
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"(?:aircaps_sk_|sk-ant-)[A-Za-z0-9_\-]+", "<REDACTED>", value)
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(clean(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
