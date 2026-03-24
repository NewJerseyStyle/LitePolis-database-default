"""
Einvite model and EinviteManager for managing email invites.

Einivtes are single-use invite codes sent via email that allow users
to register or join specific conversations.

.. list-table:: Table Schema
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - einvite
     - VARCHAR
     - Unique invite code (primary key)
   * - email
     - VARCHAR
     - Email address invite was sent to
   * - created
     - DATETIME
     - When invite was created

To use this module::

    from litepolis_database_default import DatabaseActor

    einvite = DatabaseActor.create_einvite({
        "email": "user@example.com"
    })
"""

from sqlalchemy import Index
from sqlmodel import SQLModel, Field, select
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import secrets
import string

from .utils import get_session, is_starrocks_engine
from .utils_StarRocks import register_table


def generate_einvite_code(length: int = 16) -> str:
    """Generate a random email invite code."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@register_table(distributed_by="HASH(einvite)")
class Einvite(SQLModel, table=True):
    __tablename__ = "einvites"
    __table_args__ = (
        Index("ix_einvite_email", "email"),
    )

    einvite: str = Field(nullable=False, primary_key=True)
    email: str = Field(nullable=False)
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EinviteManager:
    @staticmethod
    def create_einvite(data: Dict[str, Any]) -> Einvite:
        """Creates a new Einvite record.

        Args:
            data: Must include 'email'. If 'einvite' not provided, generates one.

        Returns:
            The created Einvite instance.

        Example:
            from litepolis_database_default import DatabaseActor
            einvite = DatabaseActor.create_einvite({"email": "user@example.com"})
        """
        if "einvite" not in data:
            data["einvite"] = generate_einvite_code()

        with get_session() as session:
            einvite = Einvite(**data)
            session.add(einvite)
            session.commit()
            if is_starrocks_engine():
                return session.exec(
                    select(Einvite).where(Einvite.einvite == data["einvite"])
                ).first()
            session.refresh(einvite)
            return einvite

    @staticmethod
    def read_einvite(einvite: str) -> Optional[Einvite]:
        """Reads an Einvite by code."""
        with get_session() as session:
            return session.exec(
                select(Einvite).where(Einvite.einvite == einvite)
            ).first()

    @staticmethod
    def get_einvite_by_email(email: str) -> Optional[Einvite]:
        """Gets latest einvite for an email."""
        with get_session() as session:
            return session.exec(
                select(Einvite)
                .where(Einvite.email == email)
                .order_by(Einvite.created.desc())
            ).first()

    @staticmethod
    def delete_einvite(einvite: str) -> bool:
        """Deletes an Einvite record (after use)."""
        with get_session() as session:
            einvite_obj = session.exec(
                select(Einvite).where(Einvite.einvite == einvite)
            ).first()
            if not einvite_obj:
                return False
            session.delete(einvite_obj)
            session.commit()
            return True

    @staticmethod
    def delete_einvites_by_email(email: str) -> int:
        """Deletes all einvites for an email. Returns count deleted."""
        with get_session() as session:
            einvites = session.exec(
                select(Einvite).where(Einvite.email == email)
            ).all()
            count = len(einvites)
            for e in einvites:
                session.delete(e)
            session.commit()
            return count

    @staticmethod
    def validate_einvite(einvite_code: str, email: str) -> bool:
        """Validates an einvite code matches the email."""
        einvite = EinviteManager.read_einvite(einvite_code)
        if not einvite:
            return False
        return einvite.email == email
