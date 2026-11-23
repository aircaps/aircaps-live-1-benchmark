import importlib.util
import json
import sqlite3
from pathlib import Path


def test_completed_database_import_filters_services_and_redacts_config(
    tmp_path, monkeypatch
):
    source = Path(__file__).resolve().parents[1] / "tools/import_pipecat_results.py"
    spec = importlib.util.spec_from_file_location("public_pipecat_import", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path / "repo"
    enum = root / "benchmarks/pipecat_stt/src/stt_benchmark/models.py"
    enum.parent.mkdir(parents=True)
    enum.write_text('class ServiceName:\n    AIRCAPS_LIVE_1="aircaps_live_1"\n')
    monkeypatch.setattr(module, "ROOT", root)
    module.permitted.cache_clear()
    db_path = tmp_path / "source.db"
    db = sqlite3.connect(db_path)
    db.executescript("""CREATE TABLE samples(sample_id TEXT PRIMARY KEY,audio_path TEXT);
    CREATE TABLE results(sample_id TEXT,service_name TEXT,model_name TEXT,transcription TEXT,error TEXT,ttfb_seconds REAL);
    CREATE TABLE ground_truth(sample_id TEXT,text TEXT);
    CREATE TABLE wer_metrics(sample_id TEXT,service_name TEXT,model_name TEXT,wer REAL);
    CREATE TABLE semantic_wer_traces(sample_id TEXT,service_name TEXT,model_name TEXT,conversation_trace TEXT);
    CREATE TABLE runs(run_id TEXT,services TEXT,config_snapshot TEXT);""")
    for i in range(1000):
        sid = str(i)
        db.execute(
            "INSERT INTO samples VALUES (?,?)", (sid, "/private/audio/" + sid + ".pcm")
        )
        db.execute("INSERT INTO ground_truth VALUES (?,?)", (sid, "hello"))
        db.execute(
            "INSERT INTO results VALUES (?,?,?,?,?,?)",
            (sid, "aircaps_live_1", "aircaps-live-1", "hello", None, 0.1),
        )
        db.execute(
            "INSERT INTO wer_metrics VALUES (?,?,?,?)",
            (sid, "aircaps_live_1", "aircaps-live-1", 0.0),
        )
    db.execute(
        "INSERT INTO results VALUES (?,?,?,?,?,?)",
        ("0", "excluded_service", "excluded_model", "hello", None, 0.1),
    )
    db.execute(
        "INSERT INTO runs VALUES (?,?,?)",
        (
            "run",
            json.dumps(["aircaps_live_1", "excluded_service"]),
            json.dumps(
                dict(
                    aircaps_api_key="test-private-credential",
                    audio_dir="/private/audio",
                    seed=42,
                )
            ),
        ),
    )
    db.commit()
    db.close()
    original = db_path.read_bytes()
    module.import_database(db_path, dataset_revision="fixture-revision")
    assert db_path.read_bytes() == original
    public = sqlite3.connect(root / "results/pipecat_stt/results.db")
    assert public.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 1000
    config = json.loads(
        public.execute("SELECT config_snapshot FROM runs").fetchone()[0]
    )
    assert "aircaps_api_key" not in config and config["audio_dir"] == "<LOCAL_PATH>"
    assert (
        public.execute("SELECT audio_path FROM samples LIMIT 1").fetchone()[0]
        == "audio/0.pcm"
    )
