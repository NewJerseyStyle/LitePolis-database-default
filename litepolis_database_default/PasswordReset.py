"""
Password Reset Token model for handling password reset requests.
"""

from sqlalchemy import Index
from sqlmodel import SQLModel, Field, Session, select
from typing import Optional
from datetime import datetime, timezone, timedelta
import secrets

from .utils import get_session


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("ix_pwreset_token", "token"),
        Index("ix_pwreset_email", "email"),
    )
    
    id: Optional[int] = Field(primary_key=True)
    email: str = Field(nullable=False, index=True)
    token: str = Field(nullable=False, unique=True, index=True)
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=24))
    used: bool = Field(default=False)


class PasswordResetTokenManager:
    @staticmethod
    def create_token(email: str) -> PasswordResetToken:
        """Create a new password reset token for an email address."""
        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(email=email, token=token)
        with get_session() as session:
            session.add(reset_token)
            session.commit()
            session.refresh(reset_token)
            return reset_token
    
    @staticmethod
    def get_valid_token(token: str) -> Optional[PasswordResetToken]:
        """Get a valid (not expired, not used) token."""
        now = datetime.now(timezone.utc)
        with get_session() as session:
            return session.exec(
                select(PasswordResetToken)
                .where(PasswordResetToken.token == token)
                .where(PasswordResetToken.used == False)
                .where(PasswordResetToken.expires > now)
            ).first()
    
    @staticmethod
    def mark_used(token_id: int) -> bool:
        """Mark a token as used."""
        with get_session() as session:
            token_obj = session.get(PasswordResetToken, token_id)
            if token_obj:
                token_obj.used = True
                session.add(token_obj)
                session.commit()
                return True
            return False
    
    @staticmethod
    def cleanup_expired() -> int:
        """Remove expired tokens. Returns count of deleted tokens."""
        now = datetime.now(timezone.utc)
        with get_session() as session:
            expired = session.exec(
                select(PasswordResetToken).where(PasswordResetToken.expires < now)
            ).all()
            count = len(expired)
            for token in expired:
                session.delete(token)
            session.commit()
            return count
