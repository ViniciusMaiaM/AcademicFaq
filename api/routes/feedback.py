from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from repositories.feedback import feedback_rp
from repositories.cache import cache_rp
from schemas.feedback import FeedbackRequest
from services.hash import get_question_hash

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackController:

    @router.post("/")
    async def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
        question_hash = get_question_hash(request.question)

        try:
            feedback_rp.create_feedback(db, request, question_hash)

            # Se positivo, garante presença no cache
            if request.feedback_type == "positive":
                cache_rp.upsert(db, question_hash, request.question, request.answer, [])

            return {"message": "Feedback submitted successfully", "feedback_type": request.feedback_type}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")
