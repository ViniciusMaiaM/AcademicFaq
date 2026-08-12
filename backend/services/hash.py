import hashlib
import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")
_TRAILING_PUNCTUATION_RE = re.compile(r"[?!.,;:]+$")


def normalize_question(question: str) -> str:
    """Normalize question text so trivial variations hit the same cache key."""
    normalized = unicodedata.normalize("NFC", question)
    normalized = normalized.lower().strip()
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    normalized = _TRAILING_PUNCTUATION_RE.sub("", normalized).strip()
    return normalized


def get_question_hash(question: str) -> str:
    """Generate hash for question to use as cache key"""
    return hashlib.md5(normalize_question(question).encode()).hexdigest()
