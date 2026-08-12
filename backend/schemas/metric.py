from typing import Any

from pydantic import BaseModel


class MetricsResponse(BaseModel):
    total_questions: int
    cached_responses: int
    positive_feedback: int
    negative_feedback: int
    satisfaction_rate: float
    popular_questions: list[dict[str, Any]]
    recent_feedback: list[dict[str, Any]]
