from models.question_frequency import QuestionFrequency
from sqlalchemy.orm import Session


class QuestionFrequencyRepository:
    def get_by_hash(self, db: Session, question_hash: str) -> QuestionFrequency | None:
        """Busca uma entrada de frequência pelo hash da pergunta."""
        return (
            db.query(QuestionFrequency)
            .filter(QuestionFrequency.question_hash == question_hash)
            .first()
        )

    def increment_frequency(
        self, db: Session, question_hash: str, question: str
    ) -> QuestionFrequency:
        """Incrementa o contador de frequência ou cria uma nova entrada."""
        entry = self.get_by_hash(db, question_hash)
        if entry:
            entry.count += 1
        else:
            entry = QuestionFrequency(question_hash=question_hash, question=question, count=1)
            db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def get_most_frequent(self, db: Session, limit: int = 10) -> list[QuestionFrequency]:
        """Retorna as perguntas mais frequentes."""
        return (
            db.query(QuestionFrequency).order_by(QuestionFrequency.count.desc()).limit(limit).all()
        )

    def get_total_questions(self, db: Session) -> int:
        """Retorna o total de perguntas únicas registradas."""
        return db.query(QuestionFrequency).count()


question_frequency_rp = QuestionFrequencyRepository()
