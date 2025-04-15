"""
This module defines the database schema for votes, including the `Vote` type hint
and `VoteManager` class for managing votes using SQLAlchemy Core API.

The database schema includes tables for users, comments, and votes,
with relationships defined between them. The `vote_table` object represents the
votes table storing information about individual votes.

.. list-table:: Table Schemas
   :header-rows: 1

   * - Table Name
     - Description
   * - users
     - Stores user information (id, email, auth_token, etc.).
   * - comments
     - Stores comment information (id, text, user_id, conversation_id, parent_comment_id, created, modified).
   * - votes
     - Stores vote information (id, user_id, comment_id, value, created, modified).

.. list-table:: Votes Table Details
   :header-rows: 1

   * - Column Name
     - Description
   * - id (int)
     - Primary key for the vote.
   * - user_id (int, optional)
     - Foreign key referencing the user who created the vote.
   * - comment_id (int, optional)
     - Foreign key referencing the comment being voted on.
   * - value (int)
     - The value of the vote.
   * - created (datetime)
     - Timestamp of when the vote was created.
   * - modified (datetime)
     - Timestamp of when the vote was last modified.

.. list-table:: Classes
   :header-rows: 1

   * - Class Name
     - Description
   * - BaseModel
     - Base class for type hinting common fields like `id`, `created`, and `modified`.
   * - Vote
     - Type hint class representing a vote record.
   * - VoteManager
     - Provides static methods for managing votes using SQLAlchemy Core API.

To use the methods in this module, import `DatabaseActor` from
`litepolis_database_default`. For example:

.. code-block:: py

    from litepolis_database_default import DatabaseActor

    vote_data = DatabaseActor.create_vote({
        "value": 1,
        "user_id": 1,
        "comment_id": 1
    })
"""


from sqlalchemy import (
    Table, Column, Integer, DateTime, ForeignKey, MetaData, Index,
    UniqueConstraint, ForeignKeyConstraint, select, insert, update, delete,
    func, asc, desc, and_
)
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC

from .utils import get_session, engine, metadata

class BaseModel:
    def __init__(self, id: int, created: datetime, modified: datetime):
        self.id = id
        self.created = created
        self.modified = modified

vote_table = Table(
    "votes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=True),
    Column("comment_id", Integer, ForeignKey("comments.id"), nullable=True),
    Column("value", Integer, nullable=False),
    Column("created", DateTime(timezone=True), default=datetime.now(UTC)),
    Column("modified", DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC)), # Add onupdate
    Index("ix_vote_user_id", "user_id"),
    Index("ix_vote_comment_id", "comment_id"),
    UniqueConstraint("user_id", "comment_id", name="uc_user_comment"),
    ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_vote_user_id'),
    ForeignKeyConstraint(['comment_id'], ['comments.id'], name='fk_vote_comment_id'),
    starrocks_key_desc='PRIMARY KEY(id)',
    starrocks_distribution_desc='DISTRIBUTED BY HASH(id)',
)

class Vote(BaseModel): # Keep the Vote class for type hinting
    value: int
    user_id: Optional[int] = None
    comment_id: Optional[int] = None

    def __init__(self, id: int, created: datetime, modified: datetime, value: int, user_id: Optional[int] = None, comment_id: Optional[int] = None):
        super().__init__(id=id, created=created, modified=modified)
        self.value = value
        self.user_id = user_id
        self.comment_id = comment_id
    # Note: Relationships like user, comment need manual handling

class VoteManager:
    @staticmethod
    def _row_to_vote(row) -> Optional[Vote]:
        """Converts a SQLAlchemy Row object to a Vote type hint object."""
        if row is None:
            return None
        return Vote(
            id=row.id,
            created=row.created,
            modified=row.modified,
            value=row.value,
            user_id=row.user_id,
            comment_id=row.comment_id
        )

    @staticmethod
    def create_vote(data: Dict[str, Any]) -> Optional[Vote]:
        """Creates a new Vote record using Core API."""
        stmt = insert(vote_table).values(**data)
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
                result = VoteManager.list_votes_by_comment_id(data["comment_id"])
                for vote in result:
                    if vote.user_id == data["user_id"]:
                        return vote
            except Exception as e:
                session.rollback()
                print(f"Error creating vote: {e}")
                return None

    @staticmethod
    def read_vote(vote_id: int) -> Optional[Vote]:
        """Reads a Vote record by ID using Core API."""
        stmt = select(vote_table).where(vote_table.c.id == vote_id)
        with get_session() as session:
            result = session.execute(stmt)
            row = result.first()
            return VoteManager._row_to_vote(row)

    @staticmethod
    def get_vote_by_user_comment(user_id: int, comment_id: int) -> Optional[Vote]:
        """Reads a Vote record by user and comment IDs using Core API."""
        stmt = select(vote_table).where(
            and_(vote_table.c.user_id == user_id, vote_table.c.comment_id == comment_id)
        )
        with get_session() as session:
            result = session.execute(stmt)
            row = result.first()
            return VoteManager._row_to_vote(row)


    @staticmethod
    def list_votes_by_comment_id(comment_id: int, page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "asc") -> List[Vote]:
        """Lists Vote records for a comment with pagination and sorting using Core API."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size

        sort_column = vote_table.c.get(order_by, vote_table.c.created)
        sort_func = desc if order_direction.lower() == "desc" else asc
        stmt = (
            select(vote_table)
            .where(vote_table.c.comment_id == comment_id)
            .order_by(sort_func(sort_column))
            .offset(offset)
            .limit(page_size)
        )
        votes = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                vote = VoteManager._row_to_vote(row)
                if vote:
                    votes.append(vote)
        return votes


    @staticmethod
    def update_vote(vote_id: int, data: Dict[str, Any]) -> Optional[Vote]:
        """Updates a Vote record by ID using Core API."""
        if 'modified' not in data: # Ensure 'modified' timestamp is updated
             data['modified'] = datetime.now(UTC)
        row = VoteManager.read_vote(vote_id)
        for k, v in vars(row).items():
            if k not in data:
                data[k] = v
        VoteManager.delete_vote(vote_id)
        return VoteManager.create_vote(data)

    @staticmethod
    def delete_vote(vote_id: int):
        """Deletes a Vote record by ID using Core API."""
        stmt = delete(vote_table).where(vote_table.c.id == vote_id)
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error deleting vote {vote_id}: {e}")


    @staticmethod
    def list_votes_by_user_id(user_id: int, page: int = 1, page_size: int = 10) -> List[Vote]:
        """List votes by user id with pagination using Core API."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        stmt = (
            select(vote_table)
            .where(vote_table.c.user_id == user_id)
            .offset(offset)
            .limit(page_size)
        )
        votes = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 vote = VoteManager._row_to_vote(row)
                 if vote:
                    votes.append(vote)
        return votes

    @staticmethod
    def list_votes_created_in_date_range(start_date: datetime, end_date: datetime) -> List[Vote]:
        """List votes created in date range using Core API."""
        stmt = select(vote_table).where(
            vote_table.c.created >= start_date,
            vote_table.c.created <= end_date
        )
        votes = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 vote = VoteManager._row_to_vote(row)
                 if vote:
                    votes.append(vote)
        return votes

    @staticmethod
    def count_votes_for_comment(comment_id: int) -> int:
        """Counts votes for a comment using Core API."""
        stmt = select(func.count(vote_table.c.id)).where(vote_table.c.comment_id == comment_id)
        with get_session() as session:
            result = session.execute(stmt)
            count = result.scalar()
            return count if count is not None else 0

    @staticmethod
    def get_vote_value_distribution_for_comment(comment_id: int) -> Dict[int, int]:
        """Gets vote value distribution for a comment using Core API."""
        stmt = (
            select(vote_table.c.value, func.count(vote_table.c.id).label("count"))
            .where(vote_table.c.comment_id == comment_id)
            .group_by(vote_table.c.value)
        )
        distribution = {}
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                distribution[row.value] = row.count
        return distribution