import os
from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


def _opt(name: str, default: str) -> str:
    return os.environ.get(name, default)


# MongoDB Atlas
MONGODB_URI = _required("MONGODB_URI")
MONGODB_DB = _opt("MONGODB_DB", "MediMind")
ATLAS_SEARCH_INDEX = _opt("ATLAS_SEARCH_INDEX", "skill_index")

# Voyage AI
VOYAGE_API_KEY = _required("VOYAGE_API_KEY")
VOYAGE_MODEL = _opt("VOYAGE_MODEL", "voyage-3")
VOYAGE_DIM = 1024

# Fireworks AI
FIREWORKS_API_KEY = _required("FIREWORKS_API_KEY")
FIREWORKS_WHISPER_MODEL = _opt("FIREWORKS_WHISPER_MODEL", "whisper-v3")
FIREWORKS_CODE_MODEL = _opt(
    "FIREWORKS_CODE_MODEL",
    "accounts/fireworks/models/kimi-k2p6",
)

# AWS Lambda
AWS_LAMBDA_FUNCTION = _opt("AWS_LAMBDA_FUNCTION", "MediMind-skill-validator")
AWS_REGION = _opt("AWS_REGION", "eu-west-2")

# LiveKit
LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "")
LIVEKIT_ROOM = _opt("LIVEKIT_ROOM", "medimind-ward")

# ElevenLabs
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")

# Discord notifications (webhook URL — text + audio attachments)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Behaviour
SKILL_MATCH_THRESHOLD = float(_opt("SKILL_MATCH_THRESHOLD", "0.78"))
FORGE_MAX_RETRIES = int(_opt("FORGE_MAX_RETRIES", "3"))
FORGE_PASS_SCORE = float(_opt("FORGE_PASS_SCORE", "0.80"))
ESCALATE_AFTER_MINUTES = int(_opt("ESCALATE_AFTER_MINUTES", "20"))
