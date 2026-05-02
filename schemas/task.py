from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Task:
    task_id: str
    type: str
    bed: Optional[str]
    ward: Optional[str]
    steps: List[str] = field(default_factory=list)
    confirmations: Dict[str, bool] = field(default_factory=dict)
    escalate_after_minutes: int = 20
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "type": self.type,
            "bed": self.bed,
            "ward": self.ward,
            "steps": self.steps,
            "confirmations": self.confirmations,
            "escalate_after_minutes": self.escalate_after_minutes,
            "created_at": self.created_at,
        }
