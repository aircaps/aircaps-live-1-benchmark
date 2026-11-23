# Upstream-published reference entries

Source: https://github.com/pipecat-ai/stt-benchmark/blob/d4d85a9ec7d3465671ae5e18bf725c013cdfb4ca/README.md

| Vendor | Model | Transcripts | Perfect | WER Mean | Pooled WER | TTFS Median | TTFS P95 | TTFS P99 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| AssemblyAI | universal-3-6-pro | 99.9% | 88.7% | 0.89% | 0.80% | 307ms | 401ms | 498ms |
| AssemblyAI | universal-3-5-pro | 99.9% | 86.0% | 1.12% | 0.95% | 282ms | 354ms | 393ms |
| AssemblyAI | universal-streaming-english | 99.8% | 66.8% | 2.81% | 2.42% | 256ms | 362ms | 417ms |
| AWS | N/A | 100.0% | 79.1% | 1.26% | 1.35% | 1136ms | 1527ms | 1897ms |
| Azure | N/A | 100.0% | 83.5% | 0.98% | 1.01% | 1016ms | 1345ms | 1791ms |
| Cartesia | ink-2 | 100.0% | 83.6% | 1.14% | 1.02% | 299ms | 328ms | 1584ms |
| Cartesia | ink-whisper | 99.9% | 61.4% | 3.32% | 3.78% | 266ms | 364ms | 898ms |
| Deepgram | nova-3-general | 99.8% | 77.7% | 1.32% | 1.37% | 247ms | 298ms | 326ms |
| ElevenLabs | scribe_v2_realtime | 99.7% | 80.3% | 3.05% | 3.13% | 281ms | 348ms | 407ms |
| Google | gemini-3.5-transcribe-live | 99.9% | 78.3% | 1.93% | 1.97% | 458ms | 532ms | 599ms |
| Google | latest-long | 100.0% | 69.7% | 2.46% | 2.46% | 878ms | 1155ms | 1570ms |
| Gradium | default | 99.3% | 65.6% | 3.81% | 3.79% | 585ms | 614ms | 623ms |
| Meta | muse-voice-transcribe-1.0 | 99.9% | 89.5% | 0.80% | 0.73% | 392ms | 1292ms | 1922ms |
| Mistral | voxtral-mini-transcribe-realtime-2602 | 99.3% | 67.7% | 4.49% | 5.11% | 525ms | 973ms | 1913ms |
| NVIDIA | Nemotron 3.0 ASR (en) | 100.0% | 76.1% | 1.90%† | 1.95%† | 221ms | 238ms | 252ms |
| NVIDIA | Nemotron 3.5 ASR (multilingual) | 99.6% | 62.0% | 4.54%† | 4.58%† | 236ms | 253ms | 266ms |
| OpenAI | gpt-4o-transcribe | 99.3% | 75.7% | 3.10% | 2.95% | 637ms | 965ms | 1655ms |
| OpenAI | gpt-realtime-whisper | 100.0% | 73.3% | 2.41% | 2.30% | 740ms | 878ms | 1080ms |
| Smallest AI | pulse | 100.0% | 74.0% | 1.85% | 1.94% | 398ms | 533ms | 1593ms |
| Speechmatics | linden-1 | 99.5% | 83.9% | 1.11% | 0.96% | 369ms | 438ms | 690ms |
| Speechmatics | N/A | 99.7% | 83.1% | 1.17% | 0.96% | 495ms | 676ms | 736ms |
| xAI | grok-voice-transcribe-2.0 | 99.8% | 89.4% | 1.12% | 0.79% | 1322ms | 1895ms | 2148ms |

† Upstream identifies these WER entries as using the previous Claude Sonnet 4.5 judge, pending rescoring. Current-judge rows use Claude Sonnet 5.5. Upstream cautions that small WER differences are not reliably rankable. Per-model clip data, client locations and collection dates are not supplied in the README.
