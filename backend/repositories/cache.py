import json
from sqlalchemy.orm import Session
from models.cache import Cache


class CacheRepository:

    def get_by_hash(self, db: Session, question_hash: str) -> Cache | None:
        return db.query(Cache).filter(Cache.question_hash == question_hash).first()

    def increment_access(self, db: Session, question_hash: str) -> None:
        cache = self.get_by_hash(db, question_hash)
        if cache:
            cache.access_count += 1
            db.commit()

    def upsert(self, db: Session, question_hash: str, question: str, answer: str, sources: list[str]):
        existing = self.get_by_hash(db, question_hash)
        sources_json = json.dumps(sources)

        if existing:
            existing.answer = answer
            existing.sources = sources_json
        else:
            db.add(Cache(question_hash=question_hash, question=question, answer=answer, sources=sources_json))

        db.commit()
        db.flush()
        return existing or self.get_by_hash(db, question_hash)

    def clear(self, db: Session):
        db.query(Cache).delete()
        db.commit()

    def get_stats(self, db: Session):
        cache_size = db.query(Cache).count()
        total_accesses = sum([c.access_count for c in db.query(Cache).all()])
        most_accessed = db.query(Cache).order_by(Cache.access_count.desc()).limit(5).all()

        return {
            "cache_size": cache_size,
            "total_accesses": total_accesses,
            "most_accessed": [c.as_dict() for c in most_accessed],
        }


cache_rp = CacheRepository()
