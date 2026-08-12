from core.database import Base
from sqlalchemy import TIMESTAMP, Column, Integer, String, Text
from sqlalchemy.sql import func


class Cache(Base):
    __tablename__ = "cache"

    id = Column(Integer, primary_key=True, index=True)
    question_hash = Column(String, unique=True)
    question = Column(Text)
    answer = Column(Text)
    sources = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    access_count = Column(Integer, default=1)
    last_accessed = Column(TIMESTAMP(timezone=True), server_default=func.now())
