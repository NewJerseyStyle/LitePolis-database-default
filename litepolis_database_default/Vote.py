from sqlalchemy import ForeignKeyConstraint
from sqlmodel import SQLModel, Field, Relationship, Column, Index, ForeignKey
from sqlmodel import UniqueConstraint, select
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC

from .utils import get_session

class BaseModel(SQLModel):
    id: int = Field(primary_key=True)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Vote(BaseModel, table=True):
    __tablename__ = "votes"
    __table_args__ = (
        Index("ix_vote_user_id", "user_id"),
        Index("ix_vote_comment_id", "comment_id"),
        UniqueConstraint("user_id", "comment_id", name="uc_user_comment"),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_vote_user_id'),
        ForeignKeyConstraint(['comment_id'], ['comments.id'], name='fk_vote_comment_id')
    )
    
    value: int  = Field(nullable=False)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    comment_id: Optional[int] = Field(default=None, foreign_key="comments.id")
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: Optional["User"] = Relationship(back_populates="votes", sa_relationship_kwargs={"foreign_keys": "Vote.user_id"})
    comment: Optional["Comment"] = Relationship(back_populates="votes", sa_relationship_kwargs={"foreign_keys": "Vote.comment_id"})


class VoteManager:
    @staticmethod
    def create_vote(data: Dict[str, Any]) -> Vote:
        """Creates a new Vote record."""
        with get_session() as session:
            vote_instance = Vote(**data)
            session.add(vote_instance)
            session.commit()
            session.refresh(vote_instance)
            return vote_instance

    @staticmethod
    def read_vote(vote_id: int) -> Optional[Vote]:
        """Reads a Vote record by ID."""
        with get_session() as session:
            return session.get(Vote, vote_id)

    @staticmethod
    def get_vote_by_user_comment(user_id: int, comment_id: int) -> Optional[Vote]:
        """Reads a Vote record by user and comment IDs."""
        with get_session() as session:
            return session.exec(
                select(Vote).where(Vote.user_id == user_id, Vote.comment_id == comment_id)
            ).first()


    @staticmethod
    def list_votes_by_comment_id(comment_id: int, page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "asc") -> List[Vote]:
        """Lists Vote records for a comment with pagination and sorting."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        order_column = getattr(Vote, order_by, Vote.created)  # Default to created
        direction = "asc" if order_direction.lower() == "asc" else "desc"
        sort_order = order_column.asc() if direction == "asc" else order_column.desc()


        with get_session() as session:
            return session.exec(
                select(Vote)
                .where(Vote.comment_id == comment_id)
                .order_by(sort_order)
                .offset(offset)
                .limit(page_size)
            ).all()



    @staticmethod
    def update_vote(vote_id: int, data: Dict[str, Any]) -> Optional[Vote]:
        """Updates a Vote record by ID."""
        with get_session() as session:
            vote_instance = session.get(Vote, vote_id)
            if not vote_instance:
                return None
            for key, value in data.items():
                setattr(vote_instance, key, value)
            session.add(vote_instance)
            session.commit()
            session.refresh(vote_instance)
            return vote_instance

    @staticmethod
    def delete_vote(vote_id: int) -> bool:
        """Deletes a Vote record by ID."""
        with get_session() as session:
            vote_instance = session.get(Vote, vote_id)
            if not vote_instance:
                return False
            session.delete(vote_instance)
            session.commit()
            return True
            
    

    @staticmethod
    def list_votes_by_user_id(user_id: int, page: int = 1, page_size: int = 10) -> List[Vote]:
        """List votes by user id with pagination."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        with get_session() as session:
            return session.exec(
                select(Vote).where(Vote.user_id == user_id).offset(offset).limit(page_size)
            ).all()
            
    @staticmethod
    def list_votes_created_in_date_range(start_date: datetime, end_date: datetime) -> List[Vote]:
        """List votes created in date range."""
        with get_session() as session:
            return session.exec(
                select(Vote).where(
                    Vote.created >= start_date, Vote.created <= end_date
                )
            ).all()
            
    @staticmethod
    def count_votes_for_comment(comment_id: int) -> int:
        """Counts votes for a comment."""
        with get_session() as session:
            return session.scalar(
                select(Vote).where(Vote.comment_id == comment_id).count()
            ) or 0
            
    @staticmethod
    def get_vote_value_distribution_for_comment(comment_id: int) -> Dict[int, int]:
        """Gets vote value distribution for a comment."""
        with get_session() as session:
            results = session.exec(
                select(Vote.value, func.count())
                .where(Vote.comment_id == comment_id)
                .group_by(Vote.value)
            ).all()
            return {value: count for value, count in results}