"""
This module defines the database schema for comments, including the `Comment` model
and related functionalities for managing comments.

The database schema includes tables for users, conversations, comments, and votes,
with relationships defined between them. The `Comment` table stores information
about individual comments, including the text, user, conversation, parent comment,
and votes.

The `CommentManager` class provides methods for creating, reading, updating, and
deleting comments.

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
     - Base class for all database models, providing common fields like `id`, `created`, and `modified`.
   * - Comment
     - SQLModel class representing the `comments` table.
   * - CommentManager
     - Provides static methods for managing comments.

To use the methods in this module, import `DatabaseActor` from
`litepolis_database_default`. For example:

.. code-block:: py

    from litepolis_database_default import DatabaseActor

    comment = DatabaseActor.create_comment({
        "text": "test@example.com",
        "user_id": 1,
        "conversation_id": 1,
    })
"""

from sqlalchemy import inspect, DDL
from sqlalchemy import ForeignKeyConstraint
from sqlmodel import SQLModel, Field, Relationship, Column, Index, ForeignKey
from sqlmodel import select
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC

from .utils import get_session, is_starrocks_engine

from .utils_StarRocks import register_table

@register_table(distributed_by="HASH(id)")
class Comment(SQLModel, table=True):
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comment_created", "created"),
        Index("ix_comment_conversation_id", "conversation_id"),
        Index("ix_comment_user_id", "user_id"),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_comment_user_id'),
        ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name='fk_comment_conversation_id')
    )


    id: int = Field(primary_key=True)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))
    text_field: str = Field(nullable=False)
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
        """Creates a new Comment record.

        Args:
            data (Dict[str, Any]): A dictionary containing the data for the new Comment.

        Returns:
            Comment: The newly created Comment instance.

        Example:
            .. code-block:: py

                from litepolis_database_default import DatabaseActor

                comment = DatabaseActor.create_comment({
                    "text": "This is a comment.",
                    "user_id": 1,
                    "conversation_id": 1
                })
        """
        with get_session() as session:
            comment_instance = Comment(**data)
            session.add(comment_instance)
            session.commit()
            if is_starrocks_engine():
                return session.exec(
                    select(Comment).where(
                        Comment.user_id == data["user_id"],
                        Comment.conversation_id == data["conversation_id"],
                        Comment.text_field == data["text_field"]
                    )
                ).first()
            session.refresh(comment_instance)
            return comment_instance

    @staticmethod
    def read_comment(comment_id: int) -> Optional[Comment]:
        """Reads a Comment record by ID.

        Args:
            comment_id (int): The ID of the Comment to read.

        Returns:
            Optional[Comment]: The Comment instance if found, otherwise None.

        Example:
            .. code-block:: py

                from litepolis_database_default import DatabaseActor

                comment = DatabaseActor.read_comment(comment_id=1)
        """
        with get_session() as session:
            return session.get(Comment, comment_id)

    @staticmethod
    def list_comments_by_conversation_id(conversation_id: int, page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "asc") -> List[Comment]:
        """Lists Comment records for a conversation with pagination and sorting.

        Args:
            conversation_id (int): The ID of the conversation to list comments for.
            page (int): The page number to retrieve (default: 1).
            page_size (int): The number of comments per page (default: 10).
            order_by (str): The field to order the comments by (default: "created").
            order_direction (str): The direction to order the comments in ("asc" or "desc", default: "asc").

        Returns:
            List[Comment]: A list of Comment instances for the given conversation, page, and sorting.

        Example:
            .. code-block:: py

                from litepolis_database_default import DatabaseActor

                comments = DatabaseActor.list_comments_by_conversation_id(conversation_id=1, page=1, page_size=10, order_by="created", order_direction="asc")
        """
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
        """Updates a Comment record by ID.

        Args:
            comment_id (int): The ID of the Comment to update.
            data (Dict[str, Any]): A dictionary containing the data to update.

        Returns:
            Optional[Comment]: The updated Comment instance if found, otherwise None.

        Example:
            .. code-block:: py

                from litepolis_database_default import DatabaseActor

                updated_comment = DatabaseActor.update_comment(comment_id=1, data={"text": "Updated comment text."})
        """
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
        """Deletes a Comment record by ID.

        Args:
            comment_id (int): The ID of the Comment to delete.

        Returns:
            bool: True if the Comment was successfully deleted, False otherwise.

        Example:
            .. code-block:: py

                from litepolis_database_default import DatabaseActor

                success = DatabaseActor.delete_comment(comment_id=1)
        """
        with get_session() as session:
            comment_instance = session.get(Comment, comment_id)
            if not comment_instance:
                return False
            session.delete(comment_instance)
            session.commit()
            return True
            
    @staticmethod
    def search_comments(query: str) -> List[Comment]:
        """Search comments by text content.

        Args:
            query (str): The search query.

        Returns:
            List[Comment]: A list of Comment instances matching the search query.

        Example:
            .. code-block:: py

                from litepolis_database_default import DatabaseActor

                comments = DatabaseActor.search_comments(query="search term")
        """
        search_term = f"%{query}%"
        with get_session() as session:
            return session.exec(
                select(Comment).where(Comment.text_field.like(search_term))
            ).all()
            
    @staticmethod
    def list_comments_by_user_id(user_id: int, page: int = 1, page_size: int = 10) -> List[Comment]:
        """List comments by user id with pagination.

        Args:
            user_id (int): The ID of the user to list comments for.
            page (int): The page number to retrieve (default: 1).
            page_size (int): The number of comments per page (default: 10).

        Returns:
            List[Comment]: A list of Comment instances for the given user and page.

        Example:
            .. code-block:: py

                from litepolis_database_default import DatabaseActor

                comments = DatabaseActor.list_comments_by_user_id(user_id=1, page=1, page_size=10)
        """
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
        """List comments created in date range.

        Args:
            start_date (datetime): The start date of the range.
            end_date (datetime): The end date of the range.

        Returns:
            List[Comment]: A list of Comment instances created within the given date range.

        Example:
            .. code-block:: py

                from litepolis_database_default import DatabaseActor

                start = datetime(2023, 1, 1)
                end = datetime(2023, 1, 31)
                comments = DatabaseActor.list_comments_created_in_date_range(start_date=start, end_date=end)
        """
        with get_session() as session:
            return session.exec(
                select(Comment).where(
                    Comment.created >= start_date, Comment.created <= end_date
                )
            ).all()
            
    @staticmethod
    def count_comments_in_conversation(conversation_id: int) -> int:
        """Counts comments in a conversation.

        Args:
            conversation_id (int): The ID of the conversation to count comments in.

        Returns:
            int: The number of comments in the given conversation.

        Example:
            .. code-block:: py

                from litepolis_database_default import DatabaseActor

                count = DatabaseActor.count_comments_in_conversation(conversation_id=1)
        """
        with get_session() as session:
            return session.scalar(
                select(Comment).where(Comment.conversation_id == conversation_id).count()
            ) or 0
            
    @staticmethod
    def get_comment_with_replies(comment_id: int) -> Optional[Comment]:
        """Reads a Comment record by ID with replies.

        Args:
            comment_id (int): The ID of the Comment to read.

        Returns:
            Optional[Comment]: The Comment instance if found, otherwise None. Replies are loaded via relationship.

        Example:
            .. code-block:: py

                from litepolis_database_default import DatabaseActor

                comment = DatabaseActor.get_comment_with_replies(comment_id=1)
        """
        with get_session() as session:
            return session.get(Comment, comment_id) # Replies are loaded via relationship