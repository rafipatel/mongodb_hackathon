"""ElevenLabs TTS — text in, audio bytes out (mp3)."""

import httpx

from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID


async def speak(text: str) -> bytes:
    if not text:
        return b""

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.8},
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            url,
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "accept": "audio/mpeg",
            },
            json=payload,
        )
        r.raise_for_status()
        return r.content
