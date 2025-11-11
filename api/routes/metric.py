from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from repositories.metric import metric_rp
from schemas.metric import MetricsResponse

router = APIRouter(prefix="/metrics", tags=["metrics"])


class MetricsController:

    @router.get("/", response_model=MetricsResponse)
    async def get_metrics(db: Session = Depends(get_db)):
        try:
            return metric_rp.get_metrics_summary(db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")
