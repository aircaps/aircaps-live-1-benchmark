# Derived from the recorded November 2026 runner; excluded provider removed, selected AirCaps parameters explicit, public package imports and finish drain added.
"""Causal real-time replay with common receipt-time evidence and native endpoint scoring."""

import asyncio, base64, hashlib, json, os, ssl, time
from pathlib import Path
from urllib.parse import urlencode
from websockets.asyncio.client import connect
from aircaps_benchmarks.vendor.coval_wer import compute_wer

SSL = ssl.create_default_context()
ENDPOINT_CONFIG = {}
MODELS = [
    ("aircaps", "aircaps-live-1", 4),
    ("elevenlabs", "scribe_v2_realtime", 45),
    ("elevenlabs", "scribe_v3_live", 45),
    ("assemblyai", "universal-3-5-pro", 24),
    ("assemblyai", "universal-3-6-pro", 24),
    ("deepgram", "nova-3", 50),
    ("deepgram", "flux-general-en", 50),
    ("mai", "mai-transcribe-2-streaming", 4),
]
LIMITS = {"aircaps": 4, "elevenlabs": 45, "assemblyai": 36, "deepgram": 70, "mai": 4}
STARTS = {"assemblyai": 2.1}
MAI_LOCK = asyncio.Lock()
MAI_NEXT = 0.0


class Adapter:
    def __init__(self, provider, model, native):
        self.p, self.model, self.native = (provider, model, native)
        self.text = ""
        self.final_text = ""
        self.segments = {}
        self.tokens = []
        self.ready = asyncio.Event()
        self.final = asyncio.Event()
        self.error = None
        self.events = []
        self.turns = []
        self.start = None
        self.t0 = None
        self.last_final = None
        self.first = None
        self.commit_sent = False

    def message(self, m):
        now = time.perf_counter()
        p = self.p
        kind = m.get("type", m.get("message_type", ""))
        self.events.append([now, m])
        if (
            kind.lower() == "error"
            or m.get("error_code")
            or m.get("error_message")
            or kind.endswith("_error")
        ):
            self.error = (
                m.get("code")
                or m.get("message")
                or m.get("error_message")
                or str(m.get("error") or kind)
            )
            self.ready.set()
            self.final.set()
            return
        text = None
        final = False
        turn = False
        if p == "aircaps":
            if kind == "ready":
                self.ready.set()
            if kind == "transcript":
                text = m.get("text", "")
                final = m.get("is_final", False)
                turn = m.get("end_of_turn", False)
        elif p == "elevenlabs":
            if kind == "session_started":
                self.ready.set()
            if kind == "partial_transcript":
                text = " ".join([*self.segments.values(), m.get("text", "")])
            if kind in ("committed_transcript", "committed_transcript_with_timestamps"):
                val = m.get("text", "")
                self.segments[len(self.segments)] = val
                text = " ".join(self.segments.values())
                final = True
                turn = self.native
        elif p == "assemblyai":
            if kind == "Begin":
                self.ready.set()
            if kind == "Turn":
                idx = m.get("turn_order", 0)
                val = m.get("transcript", "")
                self.segments[idx] = val
                text = " ".join((self.segments[k] for k in sorted(self.segments)))
                final = bool(m.get("end_of_turn"))
                turn = final and self.native
        elif p == "deepgram":
            if kind == "Connected":
                self.ready.set()
            if kind == "TurnInfo":
                self.segments[m.get("turn_index", 0)] = m.get("transcript", "")
                text = " ".join((self.segments[k] for k in sorted(self.segments)))
                final = m.get("event") == "EndOfTurn"
                turn = final and self.native
            if kind == "Results":
                val = (m.get("channel", {}).get("alternatives") or [{}])[0].get(
                    "transcript", ""
                )
                if m.get("is_final"):
                    self.tokens.append(val)
                    text = " ".join(self.tokens)
                else:
                    text = " ".join(self.tokens + [val])
                final = bool(m.get("from_finalize"))
                turn = bool(m.get("speech_final")) and self.native
        elif p == "mai":
            if kind == "session.updated":
                self.ready.set()
            if kind.endswith("input_audio_transcription.delta"):
                self.tokens.append(m.get("delta", ""))
                text = "".join(self.tokens)
            if kind.endswith("input_audio_transcription.intermediate"):
                text = "".join(self.tokens) + m.get("intermediate", "")
            if kind.endswith("input_audio_transcription.completed"):
                text = m.get("transcript", "")
                final = True
            if kind.endswith("input_audio_transcription.failed"):
                self.error = "input_transcription_failed"
                self.final.set()
        if text is not None:
            self.text = text
            if text.strip() and self.first is None:
                self.first = now
        if final:
            self.final_text = self.text
            self.last_final = now
            if self.commit_sent:
                self.final.set()
        if turn:
            self.turns.append(now)

    async def setup(self, session):
        global MAI_NEXT
        p = self.p
        model = self.model
        native = self.native
        task = asyncio.current_task()
        if p == "mai" and getattr(task, "mai_ws", None):
            cached = task.mai_ws
            if (
                time.monotonic() - task.mai_opened < 2700
                and cached.state.name == "OPEN"
            ):
                self.url_host = os.environ["MAI_HOST"]
                self.ready.set()
                return cached
            await cached.close()
            task.mai_ws = None
        if p == "mai":
            async with MAI_LOCK:
                await asyncio.sleep(max(0, MAI_NEXT - time.monotonic()))
                MAI_NEXT = time.monotonic() + 6.1
        headers = {}
        config = None
        if p == "aircaps":
            headers = {"Authorization": "Bearer " + os.environ["AIRCAPS_API_KEY"]}
            async with session.get(
                "https://api.aircaps.com/v1/realtime/endpoint",
                params={"model": model},
                headers=headers,
                timeout=12,
            ) as r:
                r.raise_for_status()
                url = (await r.json())["websocket_url"]
            config = dict(
                type="start",
                model=model,
                encoding="pcm_s16le",
                sample_rate=16000,
                channels=1,
            )
            if native:
                config.update(end_of_turn=True, **ENDPOINT_CONFIG)
        elif p == "elevenlabs":
            headers = {
                "xi-api-key": os.environ.get("ELEVENLABS_API_KEY_STT_ONLY")
                or os.environ["ELEVENLABS_API_KEY"]
            }
            url = "wss://api.elevenlabs.io/v1/speech-to-text/realtime?" + urlencode(
                dict(
                    model_id=model,
                    audio_format="pcm_16000",
                    language_code="en",
                    commit_strategy="vad" if native else "manual",
                    include_timestamps="false",
                )
            )
        elif p == "assemblyai":
            headers = {"Authorization": os.environ["ASSEMBLYAI_API_KEY"]}
            q = dict(speech_model=model, sample_rate=16000)
            q["mode"] = "balanced" if native else "min_latency"
            if not native:
                q["end_of_turn_confidence_threshold"] = 1.0
            url = "wss://streaming.assemblyai.com/v3/ws?" + urlencode(q)
        elif p == "deepgram":
            headers = {"Authorization": "Token " + os.environ["DEEPGRAM_API_KEY"]}
            q = dict(model=model, encoding="linear16", sample_rate=16000)
            flux = model.startswith("flux")
            if flux:
                q.update(
                    eot_threshold=0.7 if native else 1.0,
                    eot_timeout_ms=5000 if native else 60000,
                )
            else:
                q.update(
                    language="en",
                    interim_results="true",
                    endpointing="300" if native else "false",
                )
            url = (
                "wss://api.deepgram.com/"
                + ("v2" if flux else "v1")
                + "/listen?"
                + urlencode(q)
            )
        else:
            headers = {"api-key": os.environ["MAI_API_KEY"]}
            url = (
                "wss://"
                + os.environ["MAI_HOST"]
                + "/mai/v1/realtime?intent=transcription"
            )
            config = {
                "type": "session.update",
                "session": {
                    "type": "transcription",
                    "audio": {
                        "input": {
                            "format": {"type": "audio/pcm", "rate": 16000},
                            "transcription": {"model": model, "language": "en"},
                            "turn_detection": None,
                        }
                    },
                },
            }
        self.url_host = url.split("/")[2]
        ws = await connect(
            url,
            additional_headers=headers,
            ssl=SSL,
            open_timeout=15,
            close_timeout=2,
            max_size=8 * 1024 * 1024,
        )
        if p == "mai":
            task.mai_ws = ws
            task.mai_opened = time.monotonic()
        if config:
            await ws.send(json.dumps(config))
            self.events.append(
                (
                    time.perf_counter(),
                    {"type": "client_start_payload", "payload": config},
                )
            )
        if p == "deepgram" and model == "nova-3":
            self.ready.set()
        return ws

    async def send_audio(self, ws, b):
        if self.p == "elevenlabs":
            await ws.send(
                json.dumps(
                    dict(
                        message_type="input_audio_chunk",
                        audio_base_64=base64.b64encode(b).decode(),
                    )
                )
            )
        elif self.p == "mai":
            await ws.send(
                json.dumps(
                    dict(
                        type="input_audio_buffer.append",
                        audio=base64.b64encode(b).decode(),
                    )
                )
            )
        else:
            await ws.send(b)

    async def commit(self, ws):
        self.commit_sent = True
        if self.last_final is not None and self.text == self.final_text:
            self.final.set()
        p = self.p
        if p == "aircaps":
            m = {"type": "finalize"}
        elif p == "elevenlabs":
            m = {
                "message_type": "input_audio_chunk",
                "audio_base_64": "",
                "commit": True,
            }
        elif p == "assemblyai":
            m = {"type": "ForceEndpoint"}
        elif p == "deepgram":
            m = {
                "type": "ForceEndTurn" if self.model.startswith("flux") else "Finalize"
            }
        else:
            m = {"type": "input_audio_buffer.commit"}
        await ws.send(json.dumps(m))

    async def close(self, ws):
        p = self.p
        if p == "mai" and (not self.error):
            return
        try:
            if p == "aircaps":
                await ws.send('{"type":"finish"}')
                if self.native:
                    async with asyncio.timeout(4):
                        while True:
                            message = json.loads(await ws.recv())
                            if message.get("type") in ("finished", "error"):
                                break
            elif p == "assemblyai":
                await ws.send('{"type":"Terminate"}')
            elif p == "deepgram":
                await ws.send('{"type":"CloseStream"}')
        except Exception:
            pass
        await ws.close()


async def transcribe(session, provider, model, row, native=False):
    a = Adapter(provider, model, native)
    raw = Path(row["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row["sha256"]
    end = row["speech_end"]
    pcm = raw if native else raw[: round(end * 16000) * 2]
    if native:
        pcm += bytes(64000)
    chunk_ms = (
        100 if provider == "assemblyai" else 80 if model.startswith("flux") else 20
    )
    chunk = chunk_ms * 32
    gaps = []
    sent = []
    error = None
    receiver = None
    ws = None
    try:
        async with asyncio.timeout(len(pcm) / 32000 + 45):
            ws = await a.setup(session)

            async def receive():
                async for raw_msg in ws:
                    a.message(json.loads(raw_msg))

            receiver = asyncio.create_task(receive())
            await asyncio.wait_for(a.ready.wait(), 15)
            if a.error:
                raise RuntimeError(str(a.error))
            sizes = [min(chunk, len(pcm) - o) for o in range(0, len(pcm), chunk)]
            if provider == "assemblyai" and len(sizes) > 1 and (sizes[-1] < 1600):
                sizes[-2] -= 1600
                sizes[-1] += 1600
            a.start = time.perf_counter()
            offset = 0
            for packet_size in sizes:
                due = a.start + (offset + packet_size) / 32000
                await asyncio.sleep(max(0, due - time.perf_counter()))
                if a.error:
                    raise RuntimeError(str(a.error))
                await a.send_audio(ws, pcm[offset : offset + packet_size])
                sent.append(time.perf_counter())
                offset += packet_size
            if not native:
                await a.commit(ws)
                a.t0 = time.perf_counter()
                await asyncio.wait_for(a.final.wait(), 12)
                if a.error:
                    raise RuntimeError(str(a.error))
            else:
                a.t0 = a.start + end
    except Exception as exc:
        error = f"{type(exc).__name__}: {str(exc)[:220]}"
    finally:
        if receiver:
            receiver.cancel()
            await asyncio.gather(receiver, return_exceptions=True)
        if ws:
            if provider == "mai" and error:
                await ws.close()
                asyncio.current_task().mai_ws = None
            else:
                await a.close(ws)
    if sent:
        gaps = [(b - a) * 1000 for a, b in zip(sent, sent[1:])]
    bad_pacing = max(gaps, default=0) > max(40, chunk_ms + 30)
    out = dict(
        id=row["id"],
        cohort=row["cohort"],
        provider=provider,
        model=model,
        native=native,
        text=a.text,
        error=error,
        pacing_invalid=bad_pacing,
        max_gap_ms=max(gaps, default=0),
        endpoint_host=getattr(a, "url_host", None),
        audio_duration=len(pcm) / 32000,
        ttfs_ms=max(0, (a.last_final - a.t0) * 1000) if a.last_final and a.t0 else None,
        ttft_ms=(a.first - a.start) * 1000 if a.first and a.start else None,
        final_before_endpoint=bool(a.last_final and a.t0 and (a.last_final < a.t0)),
        turns=[t - a.start for t in a.turns] if a.start else [],
        completed_utc=__import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .isoformat(),
    )
    if row.get("reference") and (not error) and (not bad_pacing):
        w = compute_wer(row["reference"], a.text)
        out.update(
            wer=w.wer,
            substitutions=w.substitutions,
            deletions=w.deletions,
            insertions=w.insertions,
            reference_words=w.reference_words,
        )
    evidence = {
        "id": row["id"],
        "events": a.events,
        "sent": sent,
        "start": a.start,
        "t0": a.t0,
    }
    return (out, evidence)
