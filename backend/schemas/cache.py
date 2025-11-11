from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CacheMinimal(BaseModel):

    id: int
    question: str
    access_count: int
    last_accessed: Optional[datetime]

    class Config:
        orm_mode = True


class CacheStatsResponse(BaseModel):
    
    cache_size: int
    total_accesses: int
    most_accessed: List[CacheMinimal]
