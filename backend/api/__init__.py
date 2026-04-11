# importe suas rota da api aqui

from .routes import cache, feedback, metric, question
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(cache.router)
api_router.include_router(feedback.router)
api_router.include_router(metric.router)
api_router.include_router(question.router)