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

class Comment(BaseModel, table=True):
    __tablename__ = "comments"
    text: str
    user_id: int = Field(foreign_key="users.id")
    conversation_id: int = Field(foreign_key="conversations.id")
    parent_comment_id: Optional[int] = Field(foreign_key="comments.id")
    # Relationships
    user: "User" = Relationship(back_populates="comments")
    conversation: "Conversation" = Relationship(back_populates="comments")
    votes: List["Vote"] = Relationship(back_populates="comment")

class CommentManager:
    @staticmethod
    def create_comment(data: Dict[str, Any]) -> Comment:
        """Creates a new Comment record."""
        with get_session() as session:
            comment_instance = Comment(**data)
            session.add(comment_instance)
            session.commit()
            session.refresh(comment_instance)
            return comment_instance

    @staticmethod
    def read_comment(comment_id: int) -> Optional[Comment]:
        """Reads a Comment record by ID."""
        with get_session() as session:
            comment_instance = session.get(Comment, comment_id)
            return comment_instance

    @staticmethod
    def update_comment(comment_id: int, data: Dict[str, Any]) -> Optional[Comment]:
        """Updates a Comment record by ID."""
        with get_session() as session:
            comment_instance = session.get(Comment, comment_id)
            if not comment_instance:
                return None
            for key, value in data.items():
                setattr(comment_instance, key, value)
            session.add(comment_instance)
            session.commit()
            session.refresh(comment_instance)
            return comment_instance

    @staticmethod
    def delete_comment(comment_id: int) -> bool:
        """Deletes a Comment record by ID."""
        with get_session() as session:
            comment_instance = session.get(Comment, comment_id)
            if not comment_instance:
                return False
            session.delete(comment_instance)
            session.commit()
            return True

    @staticmethod
    def list_comments() -> List[Comment]:
        """Lists all Comment records."""
        with get_session() as session:
            comment_instances = session.exec(select(Comment)).all()
            return comment_instances

create_db_and_tables()