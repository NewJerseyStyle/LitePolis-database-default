from sqlalchemy import (
    Table, Column, String, DateTime, MetaData, Index,
    select, insert, delete, asc, desc
)
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC

from .utils import get_session, engine, metadata
import hashlib

migration_record_table = Table(
    "migrations",
    metadata,
    Column("id", String(255), primary_key=True),  # Migration filename
    Column("hash", String(1024), nullable=False),  # Content hash
    Column("executed_at", DateTime(timezone=True), default=datetime.now(UTC)),
    Index("ix_migrations_executed_at", "executed_at"),
    starrocks_key_desc='PRIMARY KEY(id)',
    starrocks_distribution_desc='DISTRIBUTED BY HASH(id)',
)


class MigrationRecord: # Keep the MigrationRecord class for type hinting
    def __init__(self, id: str, hash: str, executed_at: datetime):
        self.id = id
        self.hash = hash
        self.executed_at = executed_at

class MigrationRecordManager:
    @staticmethod
    def _row_to_migration_record(row) -> Optional[MigrationRecord]:
        """Converts a SQLAlchemy Row object to a MigrationRecord type hint object."""
        if row is None:
            return None
        return MigrationRecord(
            id=row.id,
            hash=row.hash,
            executed_at=row.executed_at
        )

    @staticmethod
    def create_migration(data: Dict[str, Any]):
        """Creates a new MigrationRecord record using Core API."""
        stmt = insert(migration_record_table).values(**data)
        with get_session() as session:
            try:
                result = session.execute(stmt)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error creating migration record: {e}")

    @staticmethod
    def read_migration(migration_id: str) -> Optional[MigrationRecord]:
        """Reads a MigrationRecord record by ID using Core API."""
        stmt = select(migration_record_table).where(migration_record_table.c.id == migration_id)
        with get_session() as session:
            result = session.execute(stmt)
            row = result.first()
            return MigrationRecordManager._row_to_migration_record(row)

    @staticmethod
    def delete_migration(migration_id: str) -> bool:
        """Deletes a MigrationRecord record by ID using Core API."""
        stmt = delete(migration_record_table).where(migration_record_table.c.id == migration_id)
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
                return None
            except Exception as e:
                session.rollback()
                print(f"Error deleting migration record {migration_id}: {e}")
                return False

    @staticmethod
    def list_executed_migrations(page: int = 1, page_size: int = 10, order_by: str = "executed_at", order_direction: str = "desc") -> List[MigrationRecord]:
        """Lists executed MigrationRecord records with pagination and sorting using Core API."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size

        sort_column = migration_record_table.c.get(order_by, migration_record_table.c.executed_at)
        sort_func = desc if order_direction.lower() == "desc" else asc
        stmt = (
            select(migration_record_table)
            .order_by(sort_func(sort_column))
            .offset(offset)
            .limit(page_size)
        )
        migrations = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                migration = MigrationRecordManager._row_to_migration_record(row)
                if migration:
                    migrations.append(migration)
        return migrations

    @staticmethod
    def get_latest_executed_migration() -> Optional[MigrationRecord]:
        """Returns the latest executed migration record using Core API."""
        stmt = select(migration_record_table).order_by(migration_record_table.c.executed_at.desc()).limit(1)
        with get_session() as session:
            result = session.execute(stmt)
            row = result.first()
            return MigrationRecordManager._row_to_migration_record(row)

    @staticmethod
    def verify_migration_integrity(migration_id: str, file_content: bytes) -> bool:
        """Verifies migration file integrity by comparing hashes using Core API."""
        record = MigrationRecordManager.read_migration(migration_id)
        if not record:
            return False

        current_hash = hashlib.sha256(file_content).hexdigest()
        return record.hash == current_hash