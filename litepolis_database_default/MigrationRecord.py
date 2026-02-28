from sqlalchemy import DDL, text
from sqlmodel import SQLModel, Field, Column, Index
from sqlmodel import select
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, timezone

from .utils import get_session, is_starrocks_engine
import hashlib

from .utils_StarRocks import register_table

@register_table(distributed_by="HASH(id)")
class MigrationRecord(SQLModel, table=True):
    __tablename__ = "migrations"
    __table_args__ = (
        Index("ix_migrations_executed_at", "executed_at"),
    )
    id: str = Field(primary_key=True)  # Migration filename
    hash: str = Field(nullable=False)  # Content hash
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MigrationRecordManager:
    @staticmethod
    def create_migration(data: Dict[str, Any]) -> MigrationRecord:
        """Creates a new MigrationRecord record."""
        with get_session() as session:
            migration_record_instance = MigrationRecord(**data)
            session.add(migration_record_instance)
            session.commit()
            if is_starrocks_engine():
                return session.exec(
                    select(MigrationRecord).where(
                        MigrationRecord.hash == data["hash"])
                ).first()
            session.refresh(migration_record_instance)
            return migration_record_instance

    @staticmethod
    def read_migration(migration_id: str) -> Optional[MigrationRecord]:
        """Reads a MigrationRecord record by ID."""
        with get_session() as session:
            return session.get(MigrationRecord, migration_id)

    @staticmethod
    def delete_migration(migration_id: str) -> bool:
        """Deletes a MigrationRecord record by ID."""
        with get_session() as session:
            migration_record_instance = session.get(MigrationRecord, migration_id)
            if not migration_record_instance:
                return False
            session.delete(migration_record_instance)
            session.commit()
            return True

    @staticmethod
    def list_executed_migrations(page: int = 1, page_size: int = 10, order_by: str = "executed_at", order_direction: str = "desc") -> List[MigrationRecord]:
        """Lists executed MigrationRecord records with pagination and sorting."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        order_column = getattr(MigrationRecord, order_by, MigrationRecord.executed_at)  # Default to executed_at
        direction = "desc" if order_direction.lower() == "desc" else "asc"
        sort_order = order_column.desc() if direction == "desc" else order_column.asc()


        with get_session() as session:
            return session.exec(
                select(MigrationRecord)
                .order_by(sort_order)
                .offset(offset)
                .limit(page_size)
            ).all()
            
    @staticmethod
    def get_latest_executed_migration() -> Optional[MigrationRecord]:
        """Returns the latest executed migration record."""
        with get_session() as session:
            return session.exec(
                select(MigrationRecord).order_by(MigrationRecord.executed_at.desc()).limit(1)
            ).first()
            
    @staticmethod
    def verify_migration_integrity(migration_id: str, file_content: bytes) -> bool:
        """Verifies migration file integrity by comparing hashes."""
        record = MigrationRecordManager.read_migration(migration_id)
        if not record:
            return False
        
        current_hash = hashlib.sha256(file_content).hexdigest()
        return record.hash == current_hash