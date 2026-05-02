from typing import List, Optional, TypedDict


class MediMindState(TypedDict, total=False):
    session_id: str
    transcript: str
    matched_skills: List[dict]      # [{id, score, code, name, description}]
    best_score: float
    forge_triggered: bool
    forged_code: Optional[str]
    forge_retries: int
    forge_validation_score: float
    new_skill_id: Optional[str]
    response_text: str
    spoken: bool
