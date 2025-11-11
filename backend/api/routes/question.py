from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json

from core.database import get_db
from repositories.cache import cache_rp
from repositories.metric import metric_rp
from repositories.question_frequency import question_frequency_rp
from schemas.question import QuestionRequest, QuestionResponse
from rag_chain import answer_question
from services.hash import get_question_hash

router = APIRouter(prefix="/ask", tags=["ask"])


class QuestionController:
    """Controller responsável por processar perguntas ao sistema RAG."""

    @router.post("/", response_model=QuestionResponse)
    async def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
        start_time = datetime.now()
        question_hash = get_question_hash(request.question)

        try:
            # 1️⃣ Tenta buscar no cache
            cached_result = cache_rp.get_by_hash(db, question_hash)

            if cached_result:
                cache_rp.increment_access(db, question_hash)
                question_frequency_rp.increment_frequency(db, question_hash, request.question)

                response_time = (datetime.now() - start_time).total_seconds() * 1000
                return QuestionResponse(
                    question=cached_result.question,
                    answer=cached_result.answer,
                    sources=json.loads(cached_result.sources),
                    cached=True,
                    response_time_ms=response_time
                )

            # 2️⃣ Se não tiver cache, consulta o RAG
            result = answer_question(request.question, k=request.k)

            # 3️⃣ Salva no cache e atualiza frequência
            cache_rp.upsert(
                db, question_hash, request.question, result["answer"], result["sources"]
            )
            question_frequency_rp.increment_frequency(db, question_hash, request.question)

            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return QuestionResponse(
                question=result["question"],
                answer=result["answer"],
                sources=result["sources"],
                cached=False,
                response_time_ms=response_time
            )

        except Exception as e:
            # 4️⃣ Registra métrica de erro
            metric_rp.log_error(
                db=db,
                metric_type="error",
                metric_value=str(e),
                metadata=json.dumps({"question": request.question}),
            )
            raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
