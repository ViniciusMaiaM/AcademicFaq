from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CacheMinimal(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    access_count: int
    last_accessed: Optional[datetime]

    


class CacheStatsResponse(BaseModel):
    
    cache_size: int
    total_accesses: int
    most_accessed: List[CacheMinimal]
