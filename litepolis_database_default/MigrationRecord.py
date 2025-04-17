from sqlalchemy import DDL, text
from sqlmodel import SQLModel, Field, Column, Index
from sqlmodel import select
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC

from .utils import (connect_db, get_session, is_starrocks_engine,
                    wait_for_alter_completion)
import hashlib

class MigrationRecord(SQLModel, table=True):
    __tablename__ = "migrations"
    __table_args__ = (
        Index("ix_migrations_executed_at", "executed_at"),
    )
    id: str = Field(primary_key=True)  # Migration filename
    hash: str = Field(nullable=False)  # Content hash
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

def create_starrocks_table_migrations():
    """Create migrations table optimized for StarRocks"""
    if not is_starrocks_engine():
        return

    engine = connect_db()

    ddl = """
    CREATE TABLE IF NOT EXISTS migrations (
        id VARCHAR(255) NOT NULL COMMENT 'Migration filename',
        hash VARCHAR(64) NOT NULL COMMENT 'Content hash',
        executed_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Execution timestamp'
    )
    PRIMARY KEY(id)
    DISTRIBUTED BY HASH(id)
    PROPERTIES (
        "enable_persistent_index" = "true",
        "compression" = "LZ4"
    )
    """

    index_ddl = """
    ALTER TABLE migrations 
    ADD INDEX idx_executed (executed_at) USING BITMAP COMMENT 'Execution time index'
    """

    with engine.connect() as conn:
        # Skip if table exists
        if conn.execute(text("SHOW TABLES LIKE 'migrations'")).scalar():
            return

        # Create table
        conn.execute(DDL(ddl))
        wait_for_alter_completion(conn, "migrations")
        
        # Add index
        try:
            conn.execute(DDL(index_ddl))
        except Exception as e:
            print(f"Error creating index: {e}")

        wait_for_alter_completion(conn, "migrations")
        print("Created StarRocks-optimized 'migrations' table")

# Attach to SQLModel's metadata
create_starrocks_table_migrations()


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