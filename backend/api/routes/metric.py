from core.database import get_db
from core.deps import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from models.user import User
from repositories.metric import metric_rp
from schemas.metric import MetricsResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/metrics", tags=["metrics"])


class MetricsController:
    @router.get("/", response_model=MetricsResponse)
    async def get_metrics(
        db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
    ):
        try:
            return metric_rp.get_metrics_summary(db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}") from e
