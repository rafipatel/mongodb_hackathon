"""LiveKit voice gateway.

Subscribes to the configured room, accumulates ~1s buffers per audio track,
hands them to Fireworks Whisper, and calls `on_transcript(text)` for each utterance.

A token helper is exposed so a browser / test client can join the room.
"""

import asyncio
import io
import wave
from typing import Awaitable, Callable

from livekit import api, rtc
from livekit.protocol.agent_dispatch import RoomAgentDispatch
from livekit.protocol.room import RoomConfiguration

from config import (
    LIVEKIT_AGENT_NAME,
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    LIVEKIT_ROOM,
    LIVEKIT_URL,
)
from voice.transcribe import transcribe_bytes

OnTranscript = Callable[[str], Awaitable[None]]

SAMPLES_PER_CHUNK = 16000  # 1 second @ 16kHz mono


def generate_join_token(identity: str = "medimind-agent", room: str | None = None) -> str:
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    room_name = room or LIVEKIT_ROOM
    token = token.with_identity(identity).with_grants(
        api.VideoGrants(room_join=True, room=room_name)
    )
    # Tell LiveKit Cloud to dispatch our Agents-framework worker into this room when
    # the participant connects (must match LIVEKIT_AGENT_NAME on the worker).
    if LIVEKIT_AGENT_NAME:
        rc = RoomConfiguration()
        dispatch = RoomAgentDispatch()
        dispatch.agent_name = LIVEKIT_AGENT_NAME
        rc.agents.append(dispatch)
        token = token.with_room_config(rc)
    return token.to_jwt()


def _frames_to_wav(frames: list[rtc.AudioFrame], sample_rate: int = 16000) -> bytes:
    """Concatenate AudioFrames into a single 16-bit PCM WAV blob."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for frame in frames:
            wf.writeframes(bytes(frame.data))
    return buf.getvalue()


async def _consume_track(track: rtc.AudioTrack, on_transcript: OnTranscript) -> None:
    audio_stream = rtc.AudioStream(track)
    buffer: list[rtc.AudioFrame] = []
    samples = 0

    async for event in audio_stream:
        frame = event.frame
        buffer.append(frame)
        samples += frame.samples_per_channel
        if samples >= SAMPLES_PER_CHUNK:
            wav = _frames_to_wav(buffer, sample_rate=frame.sample_rate)
            buffer, samples = [], 0
            try:
                text = await transcribe_bytes(wav)
            except Exception as exc:  # noqa: BLE001
                print(f"[voice] transcribe error: {exc}")
                continue
            if text and len(text) > 2:
                await on_transcript(text)


async def run_voice_gateway(on_transcript: OnTranscript) -> None:
    """Connect to LiveKit and pump every audio track into on_transcript."""
    if not LIVEKIT_URL:
        print("[voice] LIVEKIT_URL not set — voice gateway disabled")
        return

    room = rtc.Room()
    track_tasks: list[asyncio.Task] = []

    @room.on("track_subscribed")
    def _on_track(track, publication, participant):  # noqa: ANN001
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            track_tasks.append(asyncio.create_task(_consume_track(track, on_transcript)))

    token = generate_join_token()
    await room.connect(LIVEKIT_URL, token)
    print(f"[voice] connected to LiveKit room={LIVEKIT_ROOM}")

    # Keep the coroutine alive
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        for t in track_tasks:
            t.cancel()
        await room.disconnect()
