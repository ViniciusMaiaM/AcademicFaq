import json
from datetime import datetime

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from models.user import User
from repositories.cache import cache_rp
from repositories.metric import metric_rp
from repositories.question_frequency import question_frequency_rp
from schemas.question import QuestionRequest, QuestionResponse
from services.hash import get_question_hash
from services.rag import answer_question
from services.semantic_cache import find_semantic_match, index_question
from sqlalchemy.orm import Session

router = APIRouter(prefix="/ask", tags=["ask"])


class QuestionController:
    """Controller responsável por processar perguntas ao sistema RAG."""

    @router.post("/", response_model=QuestionResponse)
    @limiter.limit(settings.RATE_LIMIT_ASK)
    def ask_question(
        request: Request,
        payload: QuestionRequest,
        response: Response,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        start_time = datetime.now()
        question_hash = get_question_hash(payload.question)

        try:
            cached_result = cache_rp.get_by_hash(db, question_hash)

            if not cached_result:
                semantic_match_hash = find_semantic_match(payload.question)
                if semantic_match_hash:
                    cached_result = cache_rp.get_by_hash(db, semantic_match_hash)

            if cached_result:
                cache_rp.increment_access(db, cached_result.question_hash)
                question_frequency_rp.increment_frequency(db, question_hash, payload.question)

                if cached_result.question_hash != question_hash:
                    cache_rp.upsert(
                        db,
                        question_hash,
                        payload.question,
                        cached_result.answer,
                        json.loads(cached_result.sources),
                    )
                    index_question(payload.question, question_hash)

                response_time = (datetime.now() - start_time).total_seconds() * 1000
                return QuestionResponse(
                    question=payload.question,
                    answer=cached_result.answer,
                    sources=json.loads(cached_result.sources),
                    cached=True,
                    response_time_ms=response_time,
                )

            result = answer_question(payload.question, k=payload.k)

            cache_rp.upsert(
                db, question_hash, payload.question, result["answer"], result["sources"]
            )

            if not result.get("error"):
                index_question(payload.question, question_hash)
            question_frequency_rp.increment_frequency(db, question_hash, payload.question)

            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return QuestionResponse(
                question=result["question"],
                answer=result["answer"],
                sources=result["sources"],
                cached=False,
                response_time_ms=response_time,
            )

        except Exception as e:
            metric_rp.log_error(
                db=db,
                metric_type="error",
                metric_value=str(e),
                meta_data=json.dumps({"question": payload.question}),
            )
            raise HTTPException(
                status_code=500, detail=f"Error processing question: {str(e)}"
            ) from e
