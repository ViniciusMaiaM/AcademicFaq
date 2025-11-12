from api import api_router
from core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse


def start_application():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS
        )
    
    @app.get("/")
    async def root():
        return {"message": "Academic FAQ RAG API", "version": "1.0.0"}
    
    app.include_router(api_router, prefix="/api/v1")

    return app
