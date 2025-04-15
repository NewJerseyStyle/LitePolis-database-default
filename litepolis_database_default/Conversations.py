"""
This module defines the Conversation type hint and ConversationManager class for interacting
with the 'conversations' table in the database using SQLAlchemy Core API.

The 'conversations' table stores information about conversations, including their title,
description, and archive status. It also includes timestamps for creation and modification.

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
      - One-to-many. (Handled manually with separate queries in Core API)

The ConversationManager class provides static methods for performing CRUD operations
on the 'conversations' table using SQLAlchemy Core API.

To use the methods in this module, import DatabaseActor.  For example::

    from litepolis_database_default import DatabaseActor

    conversation_data = DatabaseActor.create_conversation({
        "title": "New Conversation",
        "description": "A new conversation about a topic.",
    })
"""


from sqlalchemy import (
    Table, Column, Integer, String, DateTime, Boolean, MetaData, Index,
    select, insert, update, delete, func, asc, desc, or_,
    ForeignKey
)
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC, timezone

from .utils import get_session, engine, metadata

class BaseModel:
    def __init__(self, id: int, created: datetime, modified: datetime):
        self.id = id
        self.created = created
        self.modified = modified

conversation_table = Table(
    "conversations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("created", DateTime(timezone=True), default=datetime.now(UTC)),
    Column("modified", DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC)), # Add onupdate
    Column("title", String(255), nullable=False),
    Column("description", String(16000)),
    Column("is_archived", Boolean, default=False),
    Column("user_id", Integer, ForeignKey("users.id")),
    Index("ix_conversation_created", "created"),
    Index("ix_conversation_is_archived", "is_archived"),
    starrocks_key_desc='PRIMARY KEY(id)',
    starrocks_distribution_desc='DISTRIBUTED BY HASH(id)',
)

expected_keys = [column.key for column in conversation_table.columns]

class Conversation(BaseModel): # Keep the Conversation class for type hinting
    def __init__(self, id: int, created: datetime, modified: datetime, title: str, user_id: int, description: Optional[str] = None, is_archived: bool = False):
        super().__init__(id, created, modified)
        self.title = title
        self.description = description
        self.is_archived = is_archived
        self.user_id = user_id
    # Note: Relationships like comments need to be handled manually

class ConversationManager:
    @staticmethod
    def _row_to_conversation(row) -> Optional[Conversation]:
        """Converts a SQLAlchemy Row object to a Conversation type hint object."""
        if row is None:
            return None
        return Conversation(
            id=row.id,
            created=row.created,
            modified=row.modified,
            title=row.title,
            description=row.description,
            is_archived=row.is_archived,
            user_id=row.user_id
        )

    @staticmethod
    def create_conversation(data: Dict[str, Any]) -> Optional[Conversation]:
        """Creates a new Conversation record using Core API."""
        data = {k: v for k, v in data.items() if k in expected_keys}
        stmt = insert(conversation_table).values(**data)
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
                result = ConversationManager.list_conversations(user_id=data["user_id"])
                current_time = datetime.now(UTC)
                candidate_conversation = None
                min_time_diff = None

                if result:
                    for conversation in result:
                        if conversation.title == data['title'] and conversation.description == data.get('description'):
                            created = conversation.created
                            created = created.replace(tzinfo=timezone.utc)
                            time_diff = abs(current_time - created)
                            if candidate_conversation is None or time_diff < min_time_diff:
                                candidate_conversation = conversation
                                min_time_diff = time_diff
                    new_row = candidate_conversation
                    return ConversationManager._row_to_conversation(new_row)
            except Exception as e:
                session.rollback()
                print(f"Error creating conversation: {e}")
                return None

    @staticmethod
    def read_conversation(conversation_id: int) -> Optional[Conversation]:
        """Reads a Conversation record by ID using Core API."""
        stmt = select(conversation_table).where(conversation_table.c.id == conversation_id)
        with get_session() as session:
            result = session.execute(stmt)
            row = result.first()
            return ConversationManager._row_to_conversation(row)

    @staticmethod
    def list_conversations(page: int = 1, page_size: int = 10,
                           order_by: str = "created",
                           order_direction: str = "desc",
                           user_id: Optional[int] = None) -> List[Conversation]:
        """Lists Conversation records with pagination, sorting, and optional user ID filtering using Core API."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size

        sort_column = conversation_table.c.get(order_by, conversation_table.c.created)
        sort_func = desc if order_direction.lower() == "desc" else asc
        stmt = select(conversation_table)

        if user_id is not None:
            stmt = stmt.where(conversation_table.c.user_id == user_id)

        stmt = stmt.order_by(sort_func(sort_column)).offset(offset).limit(page_size)

        conversations = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                conversation = ConversationManager._row_to_conversation(row)
                if conversation:
                    conversations.append(conversation)
        return conversations

    @staticmethod
    def update_conversation(conversation_id: int, data: Dict[str, Any]) -> Optional[Conversation]:
        """Updates a Conversation record by ID using Core API."""
        if 'modified' not in data: # Ensure 'modified' timestamp is updated
             data['modified'] = datetime.now(UTC)
        row = ConversationManager.read_conversation(conversation_id)
        for k, v in vars(row).items():
            if k not in data:
                data[k] = v
        ConversationManager.delete_conversation(conversation_id)
        return ConversationManager.create_conversation(data)

    @staticmethod
    def delete_conversation(conversation_id: int):
        """Deletes a Conversation record by ID using Core API."""
        stmt = delete(conversation_table).where(conversation_table.c.id == conversation_id)
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error deleting conversation {conversation_id}: {e}")

    @staticmethod
    def search_conversations(query: str) -> List[Conversation]:
        """Search conversations by title or description using Core API."""
        search_term = f"%{query}%"
        stmt = select(conversation_table).where(
            or_(
                conversation_table.c.title.like(search_term),
                conversation_table.c.description.like(search_term)
            )
        )
        conversations = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 conversation = ConversationManager._row_to_conversation(row)
                 if conversation:
                    conversations.append(conversation)
        return conversations

    @staticmethod
    def list_conversations_by_archived_status(is_archived: bool) -> List[Conversation]:
        """List conversations by archive status using Core API."""
        stmt = select(conversation_table).where(conversation_table.c.is_archived == is_archived)
        conversations = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 conversation = ConversationManager._row_to_conversation(row)
                 if conversation:
                    conversations.append(conversation)
        return conversations

    @staticmethod
    def list_conversations_created_in_date_range(start_date: datetime, end_date: datetime) -> List[Conversation]:
        """List conversations created in date range using Core API."""
        stmt = select(conversation_table).where(
            conversation_table.c.created >= start_date,
            conversation_table.c.created <= end_date
        )
        conversations = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 conversation = ConversationManager._row_to_conversation(row)
                 if conversation:
                    conversations.append(conversation)
        return conversations

    @staticmethod
    def count_conversations() -> int:
        """Counts all Conversation records using Core API."""
        stmt = select(func.count(conversation_table.c.id))
        with get_session() as session:
            result = session.execute(stmt)
            count = result.scalar()
            return count if count is not None else 0


    @staticmethod
    def archive_conversation(conversation_id: int):
        """Archives a conversation using Core API."""
        update_data = {
            "is_archived": True,
            "modified": datetime.now(UTC)
        }
        stmt = (
            update(conversation_table)
            .where(conversation_table.c.id == conversation_id)
            .values(**update_data)
        )
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error archiving conversation {conversation_id}: {e}")