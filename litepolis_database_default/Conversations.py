"""
This module defines the Conversation model and ConversationManager class for interacting with the 'conversations' table in the database.

The 'conversations' table stores information about conversations, including their title, description, and archive status.
It also includes timestamps for creation and modification.

.. list-table:: Table Schema
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - id
     - INTEGER
     - Unique identifier for the conversation.
   * - title
     - VARCHAR
     - Title of the conversation.
   * - description
     - VARCHAR
     - Description of the conversation.
   * - is_archived
     - BOOLEAN
     - Indicates whether the conversation is archived.
   * - created
     - DATETIME
     - Timestamp indicating when the conversation was created.
   * - modified
     - DATETIME
     - Timestamp indicating when the conversation was last modified.

.. list-table:: Relationships

    * - Comment
      - One-to-many.

The ConversationManager class provides static methods for performing CRUD (Create, Read, Update, Delete) operations
on the 'conversations' table.

To use the methods in this module, import DatabaseActor.  For example::

    from litepolis_database_default import DatabaseActor

    conversation = DatabaseActor.create_conversation({
        "title": "New Conversation",
        "description": "A new conversation about a topic.",
    })
"""


from sqlalchemy import func, DDL, text
from sqlmodel import SQLModel, Field, Relationship, Column, Index
from sqlmodel import select, DateTime
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC

from .utils import get_session, is_starrocks_engine

from .utils_StarRocks import register_table

@register_table(distributed_by="HASH(id)")
class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversation_created", "created"),
        Index("ix_conversation_is_archived", "is_archived"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    title: str = Field(nullable=False)
    description: Optional[str] = None
    is_archived: bool = Field(default=False)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))

    comments: List["Comment"] = Relationship(back_populates="conversation")
    user: Optional["User"] = Relationship(back_populates="conversation",
                                          sa_relationship_kwargs={
                                            "foreign_keys": "Conversation.user_id"})


class ConversationManager:
    @staticmethod
    def create_conversation(data: Dict[str, Any]) -> Conversation:
        """Creates a new Conversation record.

        Args:
            data (Dict[str, Any]): A dictionary containing the data for the new Conversation.

        Returns:
            Conversation: The newly created Conversation instance.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                conversation = DatabaseActor.create_conversation({
                    "title": "New Conversation",
                    "description": "A new conversation about a topic.",
                })
        """
        with get_session() as session:
            conversation_instance = Conversation(**data)
            session.add(conversation_instance)
            session.commit()
            if is_starrocks_engine():
                return session.exec(
                    select(Conversation).where(
                        Conversation.user_id == data["user_id"],
                        Conversation.title == data["title"],
                        Conversation.description == data["description"]
                    )
                ).first()
            session.refresh(conversation_instance)
            return conversation_instance

    @staticmethod
    def read_conversation(conversation_id: int) -> Optional[Conversation]:
        """Reads a Conversation record by ID.

        Args:
            conversation_id (int): The ID of the Conversation to read.

        Returns:
            Optional[Conversation]: The Conversation instance if found, otherwise None.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                conversation = DatabaseActor.read_conversation(conversation_id=1)
        """
        with get_session() as session:
            return session.get(Conversation, conversation_id)

    @staticmethod
    def list_conversations(page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "desc") -> List[Conversation]:
        """Lists Conversation records with pagination and sorting.

        Args:
            page (int): The page number to retrieve (default: 1).
            page_size (int): The number of records per page (default: 10).
            order_by (str): The field to order the results by (default: "created").
            order_direction (str): The direction to order the results in ("asc" or "desc", default: "desc").

        Returns:
            List[Conversation]: A list of Conversation instances.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                conversations = DatabaseActor.list_conversations(page=1, page_size=10, order_by="title", order_direction="asc")
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        order_column = getattr(Conversation, order_by, Conversation.created)  # Default to created
        direction = "desc" if order_direction.lower() == "desc" else "asc"
        sort_order = order_column.desc() if direction == "desc" else order_column.asc()


        with get_session() as session:
            return session.exec(
                select(Conversation)
                .order_by(sort_order)
                .offset(offset)
                .limit(page_size)
            ).all()


    @staticmethod
    def update_conversation(conversation_id: int, data: Dict[str, Any]) -> Optional[Conversation]:
        """Updates a Conversation record by ID.

        Args:
            conversation_id (int): The ID of the Conversation to update.
            data (Dict[str, Any]): A dictionary containing the data to update.

        Returns:
            Optional[Conversation]: The updated Conversation instance if found, otherwise None.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                updated_conversation = DatabaseActor.update_conversation(conversation_id=1, data={"title": "Updated Title"})
        """
        with get_session() as session:
            conversation_instance = session.get(Conversation, conversation_id)
            if not conversation_instance:
                return None
            for key, value in data.items():
                setattr(conversation_instance, key, value)
            session.add(conversation_instance)
            session.commit()
            session.refresh(conversation_instance)
            return conversation_instance

    @staticmethod
    def delete_conversation(conversation_id: int) -> bool:
        """Deletes a Conversation record by ID.

        Args:
            conversation_id (int): The ID of the Conversation to delete.

        Returns:
            bool: True if the Conversation was successfully deleted, False otherwise.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                success = DatabaseActor.delete_conversation(conversation_id=1)
        """
        with get_session() as session:
            conversation_instance = session.get(Conversation, conversation_id)
            if not conversation_instance:
                return False
            session.delete(conversation_instance)
            session.commit()
            return True
            
    @staticmethod
    def search_conversations(query: str) -> List[Conversation]:
        """Search conversations by title or description.

        Args:
            query (str): The search query.

        Returns:
            List[Conversation]: A list of Conversation instances that match the search query.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                conversations = DatabaseActor.search_conversations(query="search term")
        """
        search_term = f"%{query}%"
        with get_session() as session:
            return session.exec(
                select(Conversation).where(
                    Conversation.title.like(search_term) | Conversation.description.like(search_term)
                )
            ).all()
            
    @staticmethod
    def list_conversations_by_archived_status(is_archived: bool) -> List[Conversation]:
        """List conversations by archive status.

        Args:
            is_archived (bool): The archive status to filter by.

        Returns:
            List[Conversation]: A list of Conversation instances with the specified archive status.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                conversations = DatabaseActor.list_conversations_by_archived_status(is_archived=True)
        """
        with get_session() as session:
            return session.exec(
                select(Conversation).where(Conversation.is_archived == is_archived)
            ).all()
            
    @staticmethod
    def list_conversations_created_in_date_range(start_date: datetime, end_date: datetime) -> List[Conversation]:
        """List conversations created in date range.

        Args:
            start_date (datetime): The start date of the range.
            end_date (datetime): The end date of the range.

        Returns:
            List[Conversation]: A list of Conversation instances created within the specified date range.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor
                from datetime import datetime

                start = datetime(2023, 1, 1)
                end = datetime(2023, 1, 31)
                conversations = DatabaseActor.list_conversations_created_in_date_range(start_date=start, end_date=end)
        """
        with get_session() as session:
            return session.exec(
                select(Conversation).where(
                    Conversation.created >= start_date, Conversation.created <= end_date
                )
            ).all()

    @staticmethod
    def count_conversations() -> int:
        """Counts all Conversation records.

        Returns:
            int: The total number of Conversation records.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                count = DatabaseActor.count_conversations()
        """
        with get_session() as session:
            return session.scalar(select(Conversation).count()) or 0


    @staticmethod
    def archive_conversation(conversation_id: int) -> Optional[Conversation]:
        """Archives a conversation.

        Args:
            conversation_id (int): The ID of the Conversation to archive.

        Returns:
            Optional[Conversation]: The archived Conversation instance if found, otherwise None.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                archived_conversation = DatabaseActor.archive_conversation(conversation_id=1)
        """
        with get_session() as session:
            conversation_instance = session.get(Conversation, conversation_id)
            if not conversation_instance:
                return None
            conversation_instance.is_archived = True
            session.add(conversation_instance)
            session.commit()
            session.refresh(conversation_instance)
            return conversation_instance