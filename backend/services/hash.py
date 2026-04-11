import hashlib

def get_question_hash(question: str) -> str:
    """Generate hash for question to use as cache key"""
    return hashlib.md5(question.lower().strip().encode()).hexdigest()