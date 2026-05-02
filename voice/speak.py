"""ElevenLabs TTS — text in, audio bytes out (mp3)."""

from typing import AsyncIterator

import httpx

from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID


def is_configured() -> bool:
    return bool(ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID)


def _payload(text: str) -> dict:
    return {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.8},
    }


def _url() -> str:
    return f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"


def _headers() -> dict:
    return {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "accept": "audio/mpeg",
    }


async def speak(text: str) -> bytes:
    if not text or not is_configured():
        return b""

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(_url(), headers=_headers(), json=_payload(text))
        r.raise_for_status()
        return r.content


async def speak_stream(text: str) -> AsyncIterator[bytes]:
    """Stream MP3 chunks as ElevenLabs produces them, so the browser starts playing fast."""
    if not text or not is_configured():
        return
    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream("POST", _url(), headers=_headers(), json=_payload(text)) as r:
            r.raise_for_status()
            async for chunk in r.aiter_bytes():
                if chunk:
                    yield chunk
