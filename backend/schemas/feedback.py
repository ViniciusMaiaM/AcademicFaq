from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    question: str
    answer: str
    feedback_type: str  # 'positive' or 'negative'
    session_id: str | None = None
