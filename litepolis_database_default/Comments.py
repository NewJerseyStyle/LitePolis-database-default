"""
This module defines the database schema for comments, including the `Comment` type hint
and related functionalities for managing comments using SQLAlchemy Core API.

The database schema includes tables for users, conversations, comments, and votes,
with relationships defined between them. The `comment_table` object represents the
comments table storing information about individual comments.

The `CommentManager` class provides methods for creating, reading, updating, and
deleting comments using SQLAlchemy Core API.

.. list-table:: Table Schemas
   :header-rows: 1

   * - Table Name
     - Description
   * - users
     - Stores user information (id, email, auth_token, etc.).
   * - conversations
     - Stores conversation information (id, title, etc.).
   * - comments
     - Stores comment information (id, text, user_id, conversation_id, parent_comment_id, created, modified).

.. list-table:: Comments Table Details
   :header-rows: 1

   * - Column Name
     - Description
   * - id (int)
     - Primary key for the comment.
   * - text (str)
     - The content of the comment.
   * - user_id (int, optional)
     - Foreign key referencing the user who created the comment.
   * - conversation_id (int, optional)
     - Foreign key referencing the conversation the comment belongs to.
   * - parent_comment_id (int, optional)
     - Foreign key referencing the parent comment (for replies).
   * - created (datetime)
     - Timestamp of when the comment was created.
   * - modified (datetime)
     - Timestamp of when the comment was last modified.
   * - votes
     - Stores vote information (id, user_id, comment_id, value).

.. list-table:: Classes
   :header-rows: 1

   * - Class Name
     - Description
   * - BaseModel
     - Base class for type hinting common fields like `id`, `created`, and `modified`.
   * - Comment
     - Type hint class representing a comment record.
   * - CommentManager
     - Provides static methods for managing comments using SQLAlchemy Core API.

To use the methods in this module, import `DatabaseActor` from
`litepolis_database_default`. For example:

.. code-block:: py

    from litepolis_database_default import DatabaseActor

    comment_data = DatabaseActor.create_comment({
        "text": "test@example.com",
        "user_id": 1,
        "conversation_id": 1,
    })
"""

from sqlalchemy import (
    ForeignKeyConstraint, Table, Column, Integer, String, DateTime,
    ForeignKey, MetaData, Index, select, insert, update, delete, func, asc, desc
)
from typing import Optional, List, Type, Any, Dict, Generator, Tuple
from datetime import datetime, UTC

from .utils import get_session, engine, metadata

class BaseModel:
    id: int
    created: datetime
    modified: datetime

    def __init__(self, id: int, created: datetime, modified: datetime):
        self.id = id
        self.created = created
        self.modified = modified

comment_table = Table(
    "comments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("created", DateTime(timezone=True), default=datetime.now(UTC)),
    Column("modified", DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC)), # Add onupdate
    Column("text_field", String(255), nullable=False),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("conversation_id", Integer, ForeignKey("conversations.id")),
    Column("parent_comment_id", Integer, ForeignKey("comments.id"), nullable=True),
    Index("ix_comment_created", "created"),
    Index("ix_comment_conversation_id", "conversation_id"),
    Index("ix_comment_user_id", "user_id"),
    starrocks_key_desc='PRIMARY KEY(id)',
    starrocks_distribution_desc='DISTRIBUTED BY HASH(id)',
)

expected_keys = [column.key for column in comment_table.columns]

class Comment(BaseModel): # Keep the Comment class for type hinting and potentially other logic
    text: str
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None
    parent_comment_id: Optional[int] = None
    # Note: Relationships like user, conversation, votes, replies, parent_comment
    # need to be handled manually with separate queries when using Core API

    def __init__(self, id: int, created: datetime, modified: datetime, text: str, user_id: Optional[int] = None, conversation_id: Optional[int] = None, parent_comment_id: Optional[int] = None):
        super().__init__(id=id, created=created, modified=modified)
        self.text_field = text
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.parent_comment_id = parent_comment_id

class CommentManager:
    @staticmethod
    def _row_to_comment(row) -> Optional[Comment]:
        """Converts a SQLAlchemy Row object to a Comment type hint object."""
        if row is None:
            return None
        # Assuming row is a Row object from session.execute(...).first() or similar
        # Access columns by index or name (e.g., row[0] or row.id)
        # The exact structure depends on the select statement
        # Let's assume the select fetches all columns in table order for simplicity
        return Comment(
            id=row.id,
            created=row.created,
            modified=row.modified,
            text=row.text_field,
            user_id=row.user_id,
            conversation_id=row.conversation_id,
            parent_comment_id=row.parent_comment_id
        )

    @staticmethod
    def create_comment(data: Dict[str, Any]):
        """Creates a new Comment record using Core API."""
        if 'text' in data:
            data['text_field'] = data['text']
            del data['text']
        data = {k: v for k, v in data.items() if k in expected_keys}
        stmt = insert(comment_table).values(**data)
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error creating comment: {e}")


    @staticmethod
    def read_comment(comment_id: int) -> Optional[Comment]:
        """Reads a Comment record by ID using Core API."""
        stmt = select(comment_table).where(comment_table.c.id == comment_id)
        with get_session() as session:
            result = session.execute(stmt)
            row = result.first()
            return CommentManager._row_to_comment(row)

    @staticmethod
    def list_comments_by_conversation_id(conversation_id: int, page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "asc") -> List[Comment]:
        """Lists Comment records for a conversation using Core API."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size

        sort_column = comment_table.c.get(order_by, comment_table.c.created)
        sort_func = desc if order_direction.lower() == "desc" else asc
        stmt = (
            select(comment_table)
            .where(comment_table.c.conversation_id == conversation_id)
            .order_by(sort_func(sort_column))
            .offset(offset)
            .limit(page_size)
        )
        comments = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                comment = CommentManager._row_to_comment(row)
                if comment:
                    comments.append(comment)
        return comments


    @staticmethod
    def update_comment(comment_id: int, data: Dict[str, Any]):
        """Updates a Comment record by ID using Core API."""
        if 'text' in data:
            data['text_field'] = data['text']
            del data['text']
        data = {k: v for k, v in data.items() if k in expected_keys + ['modified']}
        if 'modified' not in data: # Ensure 'modified' timestamp is updated
             data['modified'] = datetime.now(UTC)

        row = CommentManager.read_comment(comment_id)
        for k, v in vars(row).items():
            if k not in data:
                data[k] = v
        CommentManager.delete_comment(comment_id)
        CommentManager.create_comment(data)


    @staticmethod
    def delete_comment(comment_id: int):
        """Deletes a Comment record by ID using Core API."""
        stmt = delete(comment_table).where(comment_table.c.id == comment_id)
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error deleting comment {comment_id}: {e}")

    @staticmethod
    def search_comments(query: str) -> List[Comment]:
        """Search comments by text content using Core API."""
        search_term = f"%{query}%"
        stmt = select(comment_table).where(comment_table.c.text_field.like(search_term))
        comments = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 comment = CommentManager._row_to_comment(row)
                 if comment:
                    comments.append(comment)
        return comments

    @staticmethod
    def list_comments_by_user_id(user_id: int, page: int = 1, page_size: int = 10) -> List[Comment]:
        """List comments by user id with pagination using Core API."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        stmt = (
            select(comment_table)
            .where(comment_table.c.user_id == user_id)
            .offset(offset)
            .limit(page_size)
        )
        comments = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 comment = CommentManager._row_to_comment(row)
                 if comment:
                    comments.append(comment)
        return comments

    @staticmethod
    def list_comments_created_in_date_range(start_date: datetime, end_date: datetime) -> List[Comment]:
        """List comments created in date range using Core API."""
        stmt = select(comment_table).where(
            comment_table.c.created >= start_date,
            comment_table.c.created <= end_date
        )
        comments = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 comment = CommentManager._row_to_comment(row)
                 if comment:
                    comments.append(comment)
        return comments

    @staticmethod
    def count_comments_in_conversation(conversation_id: int) -> int:
        """Counts comments in a conversation using Core API."""
        stmt = select(func.count(comment_table.c.id)).where(
            comment_table.c.conversation_id == conversation_id
        )
        with get_session() as session:
            result = session.execute(stmt)
            # scalar() returns the first column of the first row, or None
            count = result.scalar()
            return count if count is not None else 0

    @staticmethod
    def get_comment_with_replies(comment_id: int) -> Optional[Comment]:
        """
        Reads a Comment record by ID using Core API.
        Note: Replies are not automatically loaded with Core API.
        You would need a separate query to fetch replies based on parent_comment_id.
        """
        # This method now just fetches the comment itself.
        # Fetching replies would require another call like:
        # replies_stmt = select(comment_table).where(comment_table.c.parent_comment_id == comment_id)
        # ... execute replies_stmt ...
        return CommentManager.read_comment(comment_id)