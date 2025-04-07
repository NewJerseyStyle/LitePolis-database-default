from typing import Dict, Any, Optional, List
from sqlmodel import SQLModel, Field
from datetime import datetime, UTC

# Removed BaseManager import
from .utils import create_db_and_tables, get_session # Import get_session
from sqlmodel import Session, select # Import Session and select

class MigrationRecord(SQLModel, table=True):
    __tablename__ = "migrations"
    id: str = Field(primary_key=True)  # Migration filename
    hash: str  # Content hash
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class MigrationRecordManager:
    @staticmethod
    def create_migration(data: Dict[str, Any]) -> MigrationRecord:
        """Creates a new MigrationRecord record."""
        with get_session() as session:
            migration_record_instance = MigrationRecord(**data)
            session.add(migration_record_instance)
            session.commit()
            session.refresh(migration_record_instance)
            return migration_record_instance

    @staticmethod
    def read_migration(migration_record_id: str) -> Optional[MigrationRecord]:
        """Reads a MigrationRecord record by ID (migration ID is a string)."""
        with get_session() as session:
            migration_record_instance = session.get(MigrationRecord, migration_record_id)
            return migration_record_instance

    @staticmethod
    def delete_migration(migration_record_id: str) -> bool:
        """Deletes a MigrationRecord record by ID."""
        with get_session() as session:
            migration_record_instance = session.get(MigrationRecord, migration_record_id)
            if not migration_record_instance:
                return False
            session.delete(migration_record_instance)
            session.commit()
            return True

    @staticmethod
    def list_migrations() -> List[MigrationRecord]:
        """Lists all MigrationRecord records."""
        with get_session() as session:
            migration_record_instances = session.exec(select(MigrationRecord)).all()
            return migration_record_instances

create_db_and_tables()