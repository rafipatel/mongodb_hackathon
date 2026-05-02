from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Session:
    session_id: str
    transcript: str
    matched_skills: List[str] = field(default_factory=list)
    forge_triggered: bool = False
    forge_skill_id: Optional[str] = None
    response_text: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "transcript": self.transcript,
            "matched_skills": self.matched_skills,
            "forge_triggered": self.forge_triggered,
            "forge_skill_id": self.forge_skill_id,
            "response_text": self.response_text,
            "timestamp": self.timestamp,
        }
