import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models.user import User

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.execute(select(User).where(User.email == email)).scalar_one_or_none()

    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user
