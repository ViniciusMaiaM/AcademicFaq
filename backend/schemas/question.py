from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str
    session_id: str | None = None
    k: int | None = 6


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: list[dict[str, str]]
    cached: bool = False
    response_time_ms: float | None = None
