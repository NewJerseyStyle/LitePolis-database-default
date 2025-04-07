from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Type, Any, Dict
from datetime import datetime, UTC

# Removed BaseManager import
from .utils import create_db_and_tables, get_session # Import get_session
from sqlmodel import Session, select # Import Session and select

class BaseModel(SQLModel):
    id: int = Field(primary_key=True)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))

class User(BaseModel, table=True):
    __tablename__ = "users"
    email: str = Field(index=True)
    auth_token: str
    is_admin: bool = Field(default=False)
    # Relationships
    comments: List["Comment"] = Relationship(back_populates="user")
    votes: List["Vote"] = Relationship(back_populates="user")

class UserManager:
    @staticmethod
    def create_user(data: Dict[str, Any]) -> User:
        """Creates a new User record."""
        with get_session() as session:
            user_instance = User(**data)
            session.add(user_instance)
            session.commit()
            session.refresh(user_instance)
            return user_instance

    @staticmethod
    def read_user(user_id: int) -> Optional[User]:
        """Reads a User record by ID."""
        with get_session() as session:
            user_instance = session.get(User, user_id)
            return user_instance

    @staticmethod
    def list_users() -> List[User]:
        """Reads all User records."""
        with get_session() as session:
            users = session.exec(select(User)).all()
            return users

    @staticmethod
    def update_user(user_id: int, data: Dict[str, Any]) -> Optional[User]:
        """Updates a User record by ID."""
        with get_session() as session:
            user_instance = session.get(User, user_id)
            if not user_instance:
                return None
            for key, value in data.items():
                setattr(user_instance, key, value)
            session.add(user_instance)
            session.commit()
            session.refresh(user_instance)
            return user_instance

    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Deletes a User record by ID. Returns True if successful."""
        with get_session() as session:
            user_instance = session.get(User, user_id)
            if not user_instance:
                return False
            session.delete(user_instance)
            session.commit()
            return True

    @staticmethod
    def list_users() -> List[User]:
        """Lists all User records."""
        with get_session() as session:
            users = session.exec(select(User)).all()
            return users

create_db_and_tables()