from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import hashlib
import os
from datetime import datetime
import sqlite3
from contextlib import contextmanager
from rag_chain import answer_question
import uvicorn

app = FastAPI(title="Academic FAQ RAG API", version="1.0.0")

# Database setup
DB_PATH = "analytics.db"

def init_database():
    """Initialize SQLite database with required tables"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Cache table for storing question-answer pairs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_hash TEXT UNIQUE,
                question TEXT,
                answer TEXT,
                sources TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Feedback table for thumbs up/down
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_hash TEXT,
                question TEXT,
                answer TEXT,
                feedback_type TEXT CHECK(feedback_type IN ('positive', 'negative')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                FOREIGN KEY (question_hash) REFERENCES cache (question_hash)
            )
        """)
        
        # Metrics table for general analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT,
                metric_value TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Questions frequency table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_frequency (
                question_hash TEXT PRIMARY KEY,
                question TEXT,
                count INTEGER DEFAULT 1,
                last_asked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_question_hash(question: str) -> str:
    """Generate hash for question to use as cache key"""
    return hashlib.md5(question.lower().strip().encode()).hexdigest()

# Pydantic models
class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    k: Optional[int] = 6

class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, str]]
    cached: bool = False
    response_time_ms: Optional[float] = None

class FeedbackRequest(BaseModel):
    question: str
    answer: str
    feedback_type: str  # 'positive' or 'negative'
    session_id: Optional[str] = None

class MetricsResponse(BaseModel):
    total_questions: int
    cached_responses: int
    positive_feedback: int
    negative_feedback: int
    satisfaction_rate: float
    popular_questions: List[Dict[str, Any]]
    recent_feedback: List[Dict[str, Any]]

# Initialize database on startup
init_database()

@app.get("/")
async def root():
    return {"message": "Academic FAQ RAG API", "version": "1.0.0"}

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question to the RAG system with caching"""
    start_time = datetime.now()
    question_hash = get_question_hash(request.question)
    
    try:
        # Check cache first
        with get_db() as conn:
            cursor = conn.cursor()
            cached_result = cursor.execute(
                "SELECT question, answer, sources FROM cache WHERE question_hash = ?",
                (question_hash,)
            ).fetchone()
            
            if cached_result:
                # Update access count and last accessed
                cursor.execute(
                    "UPDATE cache SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE question_hash = ?",
                    (question_hash,)
                )
                conn.commit()
                
                # Update question frequency
                cursor.execute(
                    "INSERT OR REPLACE INTO question_frequency (question_hash, question, count, last_asked) VALUES (?, ?, COALESCE((SELECT count FROM question_frequency WHERE question_hash = ?) + 1, 1), CURRENT_TIMESTAMP)",
                    (question_hash, request.question, question_hash)
                )
                conn.commit()
                
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                return QuestionResponse(
                    question=cached_result["question"],
                    answer=cached_result["answer"],
                    sources=json.loads(cached_result["sources"]),
                    cached=True,
                    response_time_ms=response_time
                )
        
        # If not cached, get answer from RAG
        result = answer_question(request.question, k=request.k)
        
        # Store in cache
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO cache (question_hash, question, answer, sources) VALUES (?, ?, ?, ?)",
                (question_hash, request.question, result["answer"], json.dumps(result["sources"]))
            )
            
            # Update question frequency
            cursor.execute(
                "INSERT OR REPLACE INTO question_frequency (question_hash, question, count, last_asked) VALUES (?, ?, COALESCE((SELECT count FROM question_frequency WHERE question_hash = ?) + 1, 1), CURRENT_TIMESTAMP)",
                (question_hash, request.question, question_hash)
            )
            conn.commit()
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        return QuestionResponse(
            question=result["question"],
            answer=result["answer"],
            sources=result["sources"],
            cached=False,
            response_time_ms=response_time
        )
        
    except Exception as e:
        # Log error metric
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO metrics (metric_type, metric_value, metadata) VALUES (?, ?, ?)",
                ("error", str(e), json.dumps({"question": request.question}))
            )
            conn.commit()
        
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for a question-answer pair"""
    question_hash = get_question_hash(request.question)
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback (question_hash, question, answer, feedback_type, session_id) VALUES (?, ?, ?, ?, ?)",
                (question_hash, request.question, request.answer, request.feedback_type, request.session_id)
            )
            
            # If positive feedback, ensure it's in cache
            if request.feedback_type == "positive":
                cursor.execute(
                    "INSERT OR IGNORE INTO cache (question_hash, question, answer, sources) VALUES (?, ?, ?, ?)",
                    (question_hash, request.question, request.answer, "[]")
                )
            
            conn.commit()
        
        return {"message": "Feedback submitted successfully", "feedback_type": request.feedback_type}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get analytics metrics"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Total questions
            total_questions = cursor.execute("SELECT COUNT(*) as count FROM question_frequency").fetchone()["count"]
            
            # Cached responses
            cached_responses = cursor.execute("SELECT SUM(access_count) as count FROM cache").fetchone()["count"] or 0
            
            # Feedback counts
            positive_feedback = cursor.execute("SELECT COUNT(*) as count FROM feedback WHERE feedback_type = 'positive'").fetchone()["count"]
            negative_feedback = cursor.execute("SELECT COUNT(*) as count FROM feedback WHERE feedback_type = 'negative'").fetchone()["count"]
            
            # Satisfaction rate
            total_feedback = positive_feedback + negative_feedback
            satisfaction_rate = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
            
            # Popular questions
            popular_questions = cursor.execute(
                "SELECT question, count, last_asked FROM question_frequency ORDER BY count DESC LIMIT 10"
            ).fetchall()
            
            # Recent feedback
            recent_feedback = cursor.execute(
                "SELECT question, feedback_type, created_at FROM feedback ORDER BY created_at DESC LIMIT 10"
            ).fetchall()
            
            return MetricsResponse(
                total_questions=total_questions,
                cached_responses=cached_responses,
                positive_feedback=positive_feedback,
                negative_feedback=negative_feedback,
                satisfaction_rate=round(satisfaction_rate, 2),
                popular_questions=[dict(row) for row in popular_questions],
                recent_feedback=[dict(row) for row in recent_feedback]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cache_size = cursor.execute("SELECT COUNT(*) as count FROM cache").fetchone()["count"]
            total_accesses = cursor.execute("SELECT SUM(access_count) as count FROM cache").fetchone()["count"] or 0
            most_accessed = cursor.execute(
                "SELECT question, access_count, last_accessed FROM cache ORDER BY access_count DESC LIMIT 5"
            ).fetchall()
            
            return {
                "cache_size": cache_size,
                "total_accesses": total_accesses,
                "most_accessed": [dict(row) for row in most_accessed]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")

@app.delete("/cache/clear")
async def clear_cache():
    """Clear the cache (admin function)"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache")
            conn.commit()
            
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
