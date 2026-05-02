from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class Skill:
    id: str
    name: str
    description: str
    code: str
    embedding: List[float]
    trigger_conditions: List[str]
    validation_score: float
    usage_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trust_origin: str = "MediMind"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "embedding": self.embedding,
            "trigger_conditions": self.trigger_conditions,
            "validation_score": self.validation_score,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "trust_origin": self.trust_origin,
        }
