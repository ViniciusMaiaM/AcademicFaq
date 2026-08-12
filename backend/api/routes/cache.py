from core.database import get_db
from core.deps import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from models.user import User
from repositories.cache import cache_rp
from schemas.cache import CacheStatsResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/cache", tags=["cache"])


class CacheController:
    @router.get("/stats", response_model=CacheStatsResponse)
    async def get_cache_stats(
        db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
    ):
        try:
            return cache_rp.get_stats(db)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error getting cache stats: {str(e)}"
            ) from e

    @router.delete("/clear")
    async def clear_cache(
        db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
    ):
        try:
            cache_rp.clear(db)
            return {"message": "Cache cleared successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}") from e
