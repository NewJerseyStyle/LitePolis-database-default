from sqlalchemy import ForeignKeyConstraint
from sqlmodel import SQLModel, Field, Relationship, Column, Index, ForeignKey
from sqlmodel import select
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC

from .utils import create_db_and_tables, get_session

class BaseModel(SQLModel):
    id: int = Field(primary_key=True)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Comment(BaseModel, table=True):
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comment_created", "created"),
        Index("ix_comment_conversation_id", "conversation_id"),
        Index("ix_comment_user_id", "user_id"),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_comment_user_id'),
        ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name='fk_comment_conversation_id')
    )

    text: str = Field(nullable=False)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id") # Removed redundant index=True
    conversation_id: Optional[int] = Field(default=None, foreign_key="conversations.id") # Removed redundant index=True
    parent_comment_id: Optional[int] = Field(default=None, foreign_key="comments.id", nullable=True)

    user: Optional["User"] = Relationship(back_populates="comments")
    conversation: Optional["Conversation"] = Relationship(back_populates="comments")
    votes: List["Vote"] = Relationship(back_populates="comment")
    replies: List["Comment"] = Relationship(back_populates="parent_comment", sa_relationship_kwargs={"foreign_keys": "[Comment.parent_comment_id]"})
    parent_comment: Optional["Comment"] = Relationship(back_populates="replies", sa_relationship_kwargs={"remote_side": "[Comment.id]"})


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
            return session.get(Comment, comment_id)

    @staticmethod
    def list_comments_by_conversation_id(conversation_id: int, page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "asc") -> List[Comment]:
        """Lists Comment records for a conversation with pagination and sorting."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        order_column = getattr(Comment, order_by, Comment.created)  # Default to created
        direction = "asc" if order_direction.lower() == "asc" else "desc"
        sort_order = order_column.asc() if direction == "asc" else order_column.desc()


        with get_session() as session:
            return session.exec(
                select(Comment)
                .where(Comment.conversation_id == conversation_id)
                .order_by(sort_order)
                .offset(offset)
                .limit(page_size)
            ).all()


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
    def search_comments(query: str) -> List[Comment]:
        """Search comments by text content."""
        search_term = f"%{query}%"
        with get_session() as session:
            return session.exec(
                select(Comment).where(Comment.text.like(search_term))
            ).all()
            
    @staticmethod
    def list_comments_by_user_id(user_id: int, page: int = 1, page_size: int = 10) -> List[Comment]:
        """List comments by user id with pagination."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        with get_session() as session:
            return session.exec(
                select(Comment).where(Comment.user_id == user_id).offset(offset).limit(page_size)
            ).all()
            
    @staticmethod
    def list_comments_created_in_date_range(start_date: datetime, end_date: datetime) -> List[Comment]:
        """List comments created in date range."""
        with get_session() as session:
            return session.exec(
                select(Comment).where(
                    Comment.created >= start_date, Comment.created <= end_date
                )
            ).all()
            
    @staticmethod
    def count_comments_in_conversation(conversation_id: int) -> int:
        """Counts comments in a conversation."""
        with get_session() as session:
            return session.scalar(
                select(Comment).where(Comment.conversation_id == conversation_id).count()
            ) or 0
            
    @staticmethod
    def get_comment_with_replies(comment_id: int) -> Optional[Comment]:
        """Reads a Comment record by ID with replies."""
        with get_session() as session:
            return session.get(Comment, comment_id) # Replies are loaded via relationship