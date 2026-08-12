from contextlib import asynccontextmanager

from api import api_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.rag import get_llm, load_vectorstore
from services.semantic_cache import get_semantic_cache_vectorstore
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from core.config import settings
from core.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_vectorstore()
    get_llm()
    get_semantic_cache_vectorstore()
    yield


def start_application():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/")
    async def root():
        return {"message": "Academic FAQ RAG API", "version": "1.0.0"}

    app.include_router(api_router, prefix="/api/v1")

    return app
