"""Rebuild the exact archived inputs into explicitly chosen external storage."""

import hashlib
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def inputs(meta, sources, cache_dir, decode):
    import pyarrow.parquet as pq
    import soundfile as sf
    from huggingface_hub import HfApi, hf_hub_download

    coval = [(k, r) for k, r in meta.items() if k.startswith("coval/")]

    def coval_input(pair):
        key, row = pair
        blob = fetch(
            "https://storage.googleapis.com/coval-benchmarks-datasets/"
            + key.removeprefix("coval/")
        )
        if hashlib.sha256(blob).hexdigest() != row["source_sha256"]:
            raise ValueError(f"Source WAV hash differs: {key}")
        return key, decode(blob)

    with ThreadPoolExecutor(max_workers=8) as pool:
        yield from pool.map(coval_input, coval)
    for name, prefix, id_field in (
        ("historical_pipecat", "pipecat/", "sample_id"),
        ("livekit", "livekit/", "id"),
    ):
        selected = {k for k in meta if k.startswith(prefix)}
        if not selected:
            continue
        source = sources[name]
        api = HfApi()
        info = api.dataset_info(source["repository"], revision=source["revision"])
        for entry in info.siblings:
            if not entry.rfilename.endswith(".parquet") or not selected:
                continue
            path = hf_hub_download(
                source["repository"],
                entry.rfilename,
                repo_type="dataset",
                revision=source["revision"],
                cache_dir=str(cache_dir / "huggingface"),
                etag_timeout=30,
            )
            for batch in pq.ParquetFile(path).iter_batches(batch_size=16):
                for row in batch.to_pylist():
                    key = prefix + row[id_field]
                    if key in selected:
                        selected.remove(key)
                        yield key, decode(row["audio"]["bytes"])
        if selected:
            raise ValueError(f"Missing pinned inputs: {len(selected)} in {name}")
    channels = defaultdict(list)
    for key in meta:
        if key.startswith("primock57/"):
            channel, offsets = key.removeprefix("primock57/").split("@")
            a, b = map(float, offsets.split(":"))
            channels[channel].append((key, a, b))
    for channel, intervals in channels.items():
        path = cache_dir / "primock57" / (channel + ".wav")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            url = f"https://media.githubusercontent.com/media/babylonhealth/primock57/{sources['primock57']['revision']}/audio/{channel}.wav"
            path.write_bytes(fetch(url))
        samples, sr = sf.read(path, dtype="int16")
        if sr != 16000 or samples.ndim != 1:
            raise ValueError(f"Unexpected source channel format: {channel}")
        for key, a, b in intervals:
            yield key, samples[round(a * sr) : round(b * sr)].astype("<i2").tobytes()
