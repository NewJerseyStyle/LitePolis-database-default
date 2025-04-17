"""
This module defines the database schema for votes, including the `Vote` model
and `VoteManager` class for managing votes.

The database schema includes tables for users, comments, and votes,
with relationships defined between them. The `Vote` table stores information
about individual votes, including the voter, target comment, and vote value.

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
     - Base class for all database models, providing common fields like `id`, `created`, and `modified`.
   * - Vote
     - SQLModel class representing the `votes` table.
   * - VoteManager
     - Provides static methods for managing votes.

To use the methods in this module, import `DatabaseActor` from
`litepolis_database_default`. For example:

.. code-block:: py

    from litepolis_database_default import DatabaseActor

    vote = DatabaseActor.create_vote({
        "value": 1,
        "user_id": 1,
        "comment_id": 1
    })
"""

from sqlalchemy import DDL, text
from sqlalchemy import ForeignKeyConstraint
from sqlmodel import SQLModel, Field, Relationship, Column, Index, ForeignKey
from sqlmodel import UniqueConstraint, select
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC

from .utils import get_session, connect_db, is_starrocks_engine, wait_for_alter_completion

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

def create_starrocks_table_votes():
    """Create votes table optimized for StarRocks' primary key model"""
    if not is_starrocks_engine():
        return

    engine = connect_db()

    ddl = """
    CREATE TABLE IF NOT EXISTS votes (
        id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
        value INT NOT NULL COMMENT 'Vote value (-1, 0, 1)',
        user_id BIGINT COMMENT 'Voter ID',
        comment_id BIGINT COMMENT 'Target comment ID',
        created DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Vote time',
        modified DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Last modified'
    )
    PRIMARY KEY(id)
    DISTRIBUTED BY HASH(id)
    PROPERTIES (
        "enable_persistent_index" = "true",
        "compression" = "LZ4",
        "bloom_filter_columns" = "user_id,comment_id",
        "foreign_key_constraints" = "(user_id) REFERENCES users(id);(comment_id) REFERENCES comments(id)"
    )
    """

    indexes = [
        DDL("""
        ALTER TABLE votes 
        ADD INDEX idx_user (user_id) USING BITMAP COMMENT 'User-composite index'
        """),
        DDL("""
        ALTER TABLE votes 
        ADD INDEX idx_comment (comment_id) USING BITMAP COMMENT 'User-composite index'
        """)
    ]

    with engine.connect() as conn:
        if conn.execute(text("SHOW TABLES LIKE 'votes'")).scalar():
            return

        conn.execute(DDL(ddl))
        wait_for_alter_completion(conn, "votes")
        
        # Add indexes
        for index in indexes:
            try:
                conn.execute(index)
            except Exception as e:
                print(f"Index error: {str(e)}")

        try:
            conn.execute(DDL("""
                ALTER TABLE votes 
                ADD CONSTRAINT uc_user_comment UNIQUE (user_id, comment_id)
            """))
        except Exception as e:
            print(f"Note: StarRocks ignores unique constraints - enforce at app layer: {str(e)}")

        wait_for_alter_completion(conn, "votes")
        print("Created StarRocks-optimized 'votes' table")

# Attach to SQLModel's metadata
create_starrocks_table_votes()


from sqlalchemy import func

class VoteManager:
    @staticmethod
    def create_vote(data: Dict[str, Any]) -> Vote:
        """Creates a new Vote record.

        Args:
            data (Dict[str, Any]): A dictionary containing the data for the new Vote.

        Returns:
            Vote: The newly created Vote instance.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                vote = DatabaseActor.create_vote({
                    "value": 1,
                    "user_id": 1,
                    "comment_id": 1
                })
        """
        with get_session() as session:
            vote_instance = Vote(**data)
            session.add(vote_instance)
            session.commit()
            if is_starrocks_engine():
                return session.exec(
                    select(Vote).where(
                        Vote.user_id == data["user_id"],
                        Vote.comment_id == data["comment_id"]
                    )
                ).first()
            session.refresh(vote_instance)
            return vote_instance

    @staticmethod
    def read_vote(vote_id: int) -> Optional[Vote]:
        """Reads a Vote record by ID.

        Args:
            vote_id (int): The ID of the Vote to read.

        Returns:
            Optional[Vote]: The Vote instance if found, otherwise None.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                vote = DatabaseActor.read_vote(vote_id=1)
        """
        with get_session() as session:
            return session.get(Vote, vote_id)

    @staticmethod
    def get_vote_by_user_comment(user_id: int, comment_id: int) -> Optional[Vote]:
        """Reads a Vote record by user and comment IDs.

        Args:
            user_id (int): The ID of the user.
            comment_id (int): The ID of the comment.

        Returns:
            Optional[Vote]: The Vote instance if found, otherwise None.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                vote = DatabaseActor.get_vote_by_user_comment(user_id=1, comment_id=1)
        """
        with get_session() as session:
            return session.exec(
                select(Vote).where(Vote.user_id == user_id, Vote.comment_id == comment_id)
            ).first()


    @staticmethod
    def list_votes_by_comment_id(comment_id: int, page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "asc") -> List[Vote]:
        """Lists Vote records for a comment with pagination and sorting.

        Args:
            comment_id (int): The ID of the comment.
            page (int): The page number to retrieve (default: 1).
            page_size (int): The number of votes per page (default: 10).
            order_by (str): The field to order the votes by (default: "created").
            order_direction (str): The direction to order the votes ("asc" or "desc", default: "asc").

        Returns:
            List[Vote]: A list of Vote instances.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                votes = DatabaseActor.list_votes_by_comment_id(comment_id=1, page=1, page_size=10, order_by="created", order_direction="asc")
        """
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
        """Updates a Vote record by ID.

        Args:
            vote_id (int): The ID of the Vote to update.
            data (Dict[str, Any]): A dictionary containing the data to update.

        Returns:
            Optional[Vote]: The updated Vote instance if found, otherwise None.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                updated_vote = DatabaseActor.update_vote(vote_id=1, data={"value": -1})
        """
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
        """Deletes a Vote record by ID.

        Args:
            vote_id (int): The ID of the Vote to delete.

        Returns:
            bool: True if the Vote was successfully deleted, False otherwise.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                success = DatabaseActor.delete_vote(vote_id=1)
        """
        with get_session() as session:
            vote_instance = session.get(Vote, vote_id)
            if not vote_instance:
                return False
            session.delete(vote_instance)
            session.commit()
            return True
            
    

    @staticmethod
    def list_votes_by_user_id(user_id: int, page: int = 1, page_size: int = 10) -> List[Vote]:
        """List votes by user id with pagination.

        Args:
            user_id (int): The ID of the user.
            page (int): The page number to retrieve (default: 1).
            page_size (int): The number of votes per page (default: 10).

        Returns:
            List[Vote]: A list of Vote instances.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                votes = DatabaseActor.list_votes_by_user_id(user_id=1, page=1, page_size=10)
        """
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
        """List votes created in date range.

        Args:
            start_date (datetime): The start date of the range.
            end_date (datetime): The end date of the range.

        Returns:
            List[Vote]: A list of Vote instances.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor
                from datetime import datetime

                start = datetime(2023, 1, 1)
                end = datetime(2023, 1, 31)
                votes = DatabaseActor.list_votes_created_in_date_range(start_date=start, end_date=end)
        """
        with get_session() as session:
            return session.exec(
                select(Vote).where(
                    Vote.created >= start_date, Vote.created <= end_date
                )
            ).all()
            
    @staticmethod
    def count_votes_for_comment(comment_id: int) -> int:
        """Counts votes for a comment.

        Args:
            comment_id (int): The ID of the comment.

        Returns:
            int: The number of votes for the comment.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                count = DatabaseActor.count_votes_for_comment(comment_id=1)
        """
        with get_session() as session:
            return session.scalar(
                select(func.count(Vote.id)).where(Vote.comment_id == comment_id)
            ) or 0
            
    @staticmethod
    def get_vote_value_distribution_for_comment(comment_id: int) -> Dict[int, int]:
        """Gets vote value distribution for a comment.

        Args:
            comment_id (int): The ID of the comment.

        Returns:
            Dict[int, int]: A dictionary where the keys are vote values and the values are the counts.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                distribution = DatabaseActor.get_vote_value_distribution_for_comment(comment_id=1)
        """
        with get_session() as session:
            results = session.exec(
                select(Vote.value, func.count())
                .where(Vote.comment_id == comment_id)
                .group_by(Vote.value)
            ).all()
            return {value: count for value, count in results}