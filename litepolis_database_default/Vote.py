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

class Vote(BaseModel, table=True):
    __tablename__ = "votes"
    user_id: int = Field(foreign_key="users.id")
    comment_id: int = Field(foreign_key="comments.id")
    value: int  # -1, 0, 1
    # Relationships
    user: "User" = Relationship(back_populates="votes")
    comment: "Comment" = Relationship(back_populates="votes")

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
            vote_instance = session.get(Vote, vote_id)
            return vote_instance

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
    def list_votes() -> List[Vote]:
        """Lists all Vote records."""
        with get_session() as session:
            vote_instances = session.exec(select(Vote)).all()
            return vote_instances

create_db_and_tables()