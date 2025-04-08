from sqlmodel import SQLModel, Field, Relationship, Column, Index
from sqlmodel import select
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC

from .utils import get_session 

class BaseModel(SQLModel):
    id: int = Field(primary_key=True)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))

class Conversation(BaseModel, table=True):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversation_created", "created"),
        Index("ix_conversation_is_archived", "is_archived"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    description: Optional[str] = None
    is_archived: bool = Field(default=False)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))

    comments: List["Comment"] = Relationship(back_populates="conversation")

class ConversationManager:
    @staticmethod
    def create_conversation(data: Dict[str, Any]) -> Conversation:
        """Creates a new Conversation record."""
        with get_session() as session:
            conversation_instance = Conversation(**data)
            session.add(conversation_instance)
            session.commit()
            session.refresh(conversation_instance)
            return conversation_instance

    @staticmethod
    def read_conversation(conversation_id: int) -> Optional[Conversation]:
        """Reads a Conversation record by ID."""
        with get_session() as session:
            return session.get(Conversation, conversation_id)

    @staticmethod
    def list_conversations(page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "desc") -> List[Conversation]:
        """Lists Conversation records with pagination and sorting."""
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
        """Updates a Conversation record by ID."""
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
        """Deletes a Conversation record by ID."""
        with get_session() as session:
            conversation_instance = session.get(Conversation, conversation_id)
            if not conversation_instance:
                return False
            session.delete(conversation_instance)
            session.commit()
            return True
            
    @staticmethod
    def search_conversations(query: str) -> List[Conversation]:
        """Search conversations by title or description."""
        search_term = f"%{query}%"
        with get_session() as session:
            return session.exec(
                select(Conversation).where(
                    Conversation.title.like(search_term) | Conversation.description.like(search_term)
                )
            ).all()
            
    @staticmethod
    def list_conversations_by_archived_status(is_archived: bool) -> List[Conversation]:
        """List conversations by archive status."""
        with get_session() as session:
            return session.exec(
                select(Conversation).where(Conversation.is_archived == is_archived)
            ).all()
            
    @staticmethod
    def list_conversations_created_in_date_range(start_date: datetime, end_date: datetime) -> List[Conversation]:
        """List conversations created in date range."""
        with get_session() as session:
            return session.exec(
                select(Conversation).where(
                    Conversation.created >= start_date, Conversation.created <= end_date
                )
            ).all()

    @staticmethod
    def count_conversations() -> int:
        """Counts all Conversation records."""
        with get_session() as session:
            return session.scalar(select(Conversation).count()) or 0


    @staticmethod
    def archive_conversation(conversation_id: int) -> Optional[Conversation]:
        """Archives a conversation."""
        with get_session() as session:
            conversation_instance = session.get(Conversation, conversation_id)
            if not conversation_instance:
                return None
            conversation_instance.is_archived = True
            session.add(conversation_instance)
            session.commit()
            session.refresh(conversation_instance)
            return conversation_instance