from typing import List, Dict, Any

from pydantic import BaseModel


class MetricsResponse(BaseModel):
    total_questions: int
    cached_responses: int
    positive_feedback: int
    negative_feedback: int
    satisfaction_rate: float
    popular_questions: List[Dict[str, Any]]
    recent_feedback: List[Dict[str, Any]]