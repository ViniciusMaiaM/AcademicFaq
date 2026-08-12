from models.feedback import Feedback
from sqlalchemy.orm import Session


class FeedbackRepository:
    def create_feedback(self, db: Session, request, question_hash: str):
        feedback = Feedback(
            question_hash=question_hash,
            question=request.question,
            answer=request.answer,
            feedback_type=request.feedback_type,
            session_id=request.session_id,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback


feedback_rp = FeedbackRepository()
