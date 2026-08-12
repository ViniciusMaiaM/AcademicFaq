from fastapi import APIRouter

from .routes import auth, cache, feedback, metric, question

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(cache.router)
api_router.include_router(feedback.router)
api_router.include_router(metric.router)
api_router.include_router(question.router)
