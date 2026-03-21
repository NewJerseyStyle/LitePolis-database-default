"""
Zinvite model and ZinviteManager for managing conversation invite codes.

Zinvites (zinvite) are short codes that allow users to join conversations.
The zinvite code serves as the external conversation_id in the Polis API.

.. list-table:: Table Schema
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - zid
     - INTEGER
     - Foreign key to conversation
   * - zinvite
     - VARCHAR
     - Unique invite code (primary key)
   * - created
     - DATETIME
     - When invite was created

To use this module::

    from litepolis_database_default import DatabaseActor

    zinvite = DatabaseActor.create_zinvite({
        "zid": 1,
        "zinvite": "abc123def"
    })
"""

from sqlalchemy import DDL, ForeignKeyConstraint, Index
from sqlmodel import SQLModel, Field, Column, select
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import secrets
import string

from .utils import get_session, is_starrocks_engine
from .utils_StarRocks import register_table


def generate_zinvite_code(length: int = 12) -> str:
    """Generate a random invite code that starts with a digit.
    
    The Polis frontend router requires conversation IDs to start with a digit,
    matching the pattern: /^[0-9][0-9A-Za-z]+$/
    """
    alphabet = string.ascii_letters + string.digits
    # First character must be a digit for Polis frontend compatibility
    first_char = secrets.choice(string.digits)
    # Remaining characters can be letters or digits
    remaining = ''.join(secrets.choice(alphabet) for _ in range(length - 1))
    return first_char + remaining


@register_table(distributed_by="HASH(zinvite)")
class Zinvite(SQLModel, table=True):
    __tablename__ = "zinvites"
    __table_args__ = (
        Index("ix_zinvite_zid", "zid"),
        ForeignKeyConstraint(['zid'], ['conversations.id'], name='fk_zinvite_zid'),
    )

    zid: int = Field(nullable=False)
    zinvite: str = Field(nullable=False, unique=True, primary_key=True)
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ZinviteManager:
    @staticmethod
    def create_zinvite(data: Dict[str, Any]) -> Zinvite:
        """Creates a new Zinvite record.

        Args:
            data: Must include 'zid'. If 'zinvite' not provided, generates one.

        Returns:
            The created Zinvite instance.

        Example:
            from litepolis_database_default import DatabaseActor
            zinvite = DatabaseActor.create_zinvite({"zid": 1})
        """
        if "zinvite" not in data:
            data["zinvite"] = generate_zinvite_code()

        with get_session() as session:
            zinvite = Zinvite(**data)
            session.add(zinvite)
            session.commit()
            if is_starrocks_engine():
                return session.exec(
                    select(Zinvite).where(Zinvite.zinvite == data["zinvite"])
                ).first()
            session.refresh(zinvite)
            return zinvite

    @staticmethod
    def read_zinvite(zinvite: str) -> Optional[Zinvite]:
        """Reads a Zinvite by code."""
        with get_session() as session:
            return session.exec(
                select(Zinvite).where(Zinvite.zinvite == zinvite)
            ).first()

    @staticmethod
    def get_zinvite_by_zid(zid: int) -> Optional[Zinvite]:
        """Gets zinvite for a conversation."""
        with get_session() as session:
            return session.exec(
                select(Zinvite).where(Zinvite.zid == zid)
            ).first()

    @staticmethod
    def get_or_create_zinvite(zid: int) -> Zinvite:
        """Gets existing zinvite or creates new one for conversation."""
        zinvite = ZinviteManager.get_zinvite_by_zid(zid)
        if zinvite:
            return zinvite
        return ZinviteManager.create_zinvite({"zid": zid})

    @staticmethod
    def get_zid_by_zinvite(zinvite_code: str) -> Optional[int]:
        """Gets zid from zinvite code."""
        zinvite = ZinviteManager.read_zinvite(zinvite_code)
        return zinvite.zid if zinvite else None

    @staticmethod
    def delete_zinvite(zinvite: str) -> bool:
        """Deletes a Zinvite record."""
        with get_session() as session:
            zinvite_obj = session.exec(
                select(Zinvite).where(Zinvite.zinvite == zinvite)
            ).first()
            if not zinvite_obj:
                return False
            session.delete(zinvite_obj)
            session.commit()
            return True

    @staticmethod
    def delete_zinvites_by_zid(zid: int) -> int:
        """Deletes all zinvites for a conversation. Returns count deleted."""
        with get_session() as session:
            zinvites = session.exec(
                select(Zinvite).where(Zinvite.zid == zid)
            ).all()
            count = len(zinvites)
            for z in zinvites:
                session.delete(z)
            session.commit()
            return count
