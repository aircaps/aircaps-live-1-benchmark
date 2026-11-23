import asyncio
import json
from urllib.parse import urlparse, parse_qs
from aircaps_benchmarks import adapters


class Socket:
    def __init__(self):
        self.sent = []

    async def send(self, value):
        self.sent.append(json.loads(value))


class Response:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def raise_for_status(self):
        pass

    async def json(self):
        return {"websocket_url": "wss://rt1.aircaps.ai/test"}


class Session:
    def get(self, *args, **kwargs):
        return Response()


def test_aircaps_selected_parameters_omit_mode(monkeypatch):
    monkeypatch.setenv("AIRCAPS_API_KEY", "test-placeholder")
    monkeypatch.setattr(
        adapters,
        "ENDPOINT_CONFIG",
        dict(
            min_turn_silence_ms=200,
            end_of_turn_threshold=0.65,
            max_turn_silence_ms=3000,
            vad_threshold=0.65,
        ),
    )
    ws = Socket()

    async def connect(*args, **kwargs):
        return ws

    monkeypatch.setattr(adapters, "connect", connect)
    asyncio.run(adapters.Adapter("aircaps", "aircaps-live-1", True).setup(Session()))
    assert ws.sent[0]["end_of_turn"] is True
    assert ws.sent[0]["max_turn_silence_ms"] == 3000
    assert "end_of_turn_mode" not in ws.sent[0]


def test_third_party_native_settings_remain_fixed(monkeypatch):
    captured = []

    async def connect(url, **kwargs):
        captured.append(parse_qs(urlparse(url).query))
        return Socket()

    monkeypatch.setattr(adapters, "connect", connect)
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-placeholder")
    monkeypatch.setenv("ASSEMBLYAI_API_KEY", "test-placeholder")
    asyncio.run(adapters.Adapter("deepgram", "flux-general-en", True).setup(Session()))
    asyncio.run(
        adapters.Adapter("assemblyai", "universal-3-6-pro", True).setup(Session())
    )
    assert captured[0]["eot_threshold"] == ["0.7"] and captured[0][
        "eot_timeout_ms"
    ] == ["5000"]
    assert (
        captured[1]["mode"] == ["balanced"]
        and "end_of_turn_confidence_threshold" not in captured[1]
    )
