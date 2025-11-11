from typing import Optional, List, Dict

from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    k: Optional[int] = 6

class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, str]]
    cached: bool = False
    response_time_ms: Optional[float] = None