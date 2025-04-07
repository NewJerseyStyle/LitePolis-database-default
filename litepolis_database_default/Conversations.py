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

class Conversation(BaseModel, table=True):
    __tablename__ = "conversations"
    title: str
    description: str
    is_archived: bool = Field(default=False)
    # Relationships
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
            conversation_instance = session.get(Conversation, conversation_id)
            return conversation_instance

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
    def list_conversations() -> List[Conversation]:
        """Lists all Conversation records."""
        with get_session() as session:
            conversations = session.exec(select(Conversation)).all()
            return conversations

create_db_and_tables()