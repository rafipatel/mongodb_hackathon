"""Fireworks AI Whisper wrapper.

Two entrypoints:
- transcribe_bytes(audio: bytes) — for one-shot uploads (16kHz wav recommended)
- transcribe_file(path) — for tests / CLI
"""

import httpx

from config import FIREWORKS_API_KEY, FIREWORKS_WHISPER_MODEL

# The Fireworks audio API is OpenAI-compatible
FIREWORKS_AUDIO_URL = "https://audio-prod.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions"


async def transcribe_bytes(audio: bytes, content_type: str = "audio/wav") -> str:
    files = {"file": ("audio.wav", audio, content_type)}
    data = {"model": FIREWORKS_WHISPER_MODEL, "response_format": "text"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            FIREWORKS_AUDIO_URL,
            headers={"Authorization": f"Bearer {FIREWORKS_API_KEY}"},
            files=files,
            data=data,
        )
        r.raise_for_status()
        return r.text.strip()


async def transcribe_file(path: str) -> str:
    with open(path, "rb") as f:
        return await transcribe_bytes(f.read())
