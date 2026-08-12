from models.cache import Cache
from models.feedback import Feedback
from models.metric import Metric
from models.question_frequency import QuestionFrequency
from models.user import User

# Re-export explícito: `alembic/env.py` faz `from models import *` pra
# registrar todos os models em Base.metadata antes do autogenerate.
__all__ = ["Cache", "Feedback", "Metric", "QuestionFrequency", "User"]
