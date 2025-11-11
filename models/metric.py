from core.database import Base
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func

class Metric(Base):
    __tablename__ = "metric"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String)
    metric_value = Column(String)
    metadata = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())