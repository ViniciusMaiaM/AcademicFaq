from core.database import get_db
from core.deps import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from models.user import User
from repositories.cache import cache_rp
from repositories.feedback import feedback_rp
from schemas.feedback import FeedbackRequest
from services.hash import get_question_hash
from sqlalchemy.orm import Session

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackController:
    @router.post("/")
    async def submit_feedback(
        request: FeedbackRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        question_hash = get_question_hash(request.question)

        try:
            feedback_rp.create_feedback(db, request, question_hash)

            if request.feedback_type == "positive":
                cache_rp.upsert(db, question_hash, request.question, request.answer, [])

            return {
                "message": "Feedback submitted successfully",
                "feedback_type": request.feedback_type,
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error submitting feedback: {str(e)}"
            ) from e
