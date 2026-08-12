from core.database import Base
from sqlalchemy import TIMESTAMP, Column, Integer, String, Text
from sqlalchemy.sql import func


class QuestionFrequency(Base):
    __tablename__ = "question_frequency"

    question_hash = Column(String, primary_key=True, index=True)
    question = Column(Text)
    count = Column(Integer, default=1)
    last_asked = Column(TIMESTAMP(timezone=True), server_default=func.now())
