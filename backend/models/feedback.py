from core.database import Base
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    question_hash = Column(String)
    question = Column(Text)
    answer = Column(Text)
    feedback_type = Column(String)  # 'positive' ou 'negative'
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    session_id = Column(String)