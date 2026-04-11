import json
from sqlalchemy.orm import Session
from models.metric import Metric
from models.feedback import Feedback
from models.cache import Cache
from models.question_frequency import QuestionFrequency


class MetricRepository:

    def log_error(self, db: Session, metric_type: str, metric_value: str, meta_data: dict):
        metric = Metric(
            metric_type=metric_type,
            metric_value=metric_value,
            meta_data=json.dumps(meta_data)
        )
        db.add(metric)
        db.commit()

    def get_metrics_summary(self, db: Session):

        total_questions = db.query(QuestionFrequency).count()
        cached_responses = sum([c.access_count for c in db.query(Cache).all()])
        positive_feedback = db.query(Feedback).filter(Feedback.feedback_type == "positive").count()
        negative_feedback = db.query(Feedback).filter(Feedback.feedback_type == "negative").count()

        total_feedback = positive_feedback + negative_feedback
        satisfaction_rate = (positive_feedback / total_feedback * 100) if total_feedback else 0

        popular_questions = db.query(QuestionFrequency).order_by(QuestionFrequency.count.desc()).limit(10).all()
        recent_feedback = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(10).all()

        return {
            "total_questions": total_questions,
            "cached_responses": cached_responses,
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "satisfaction_rate": round(satisfaction_rate, 2),
            "popular_questions": [q.as_dict() for q in popular_questions],
            "recent_feedback": [f.as_dict() for f in recent_feedback],
        }


metric_rp = MetricRepository()
