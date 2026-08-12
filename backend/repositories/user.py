from models.user import User
from sqlalchemy.orm import Session


class UserRepository:
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def get_by_api_key(self, db: Session, api_key: str) -> User | None:
        return db.query(User).filter(User.api_key == api_key).first()

    def create(self, db: Session, email: str, hashed_password: str, api_key: str) -> User:
        user = User(email=email, hashed_password=hashed_password, api_key=api_key)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


user_rp = UserRepository()
