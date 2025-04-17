from litepolis_database_default.Actor import DatabaseActor
import pytest
from typing import Optional
from datetime import datetime, UTC

def test_create_migration_record():
    # Create migration record
    migration = DatabaseActor.create_migration({
        "id": "test-migration-123",
        "hash": "test-hash-123"
    })
    
    assert migration.id == "test-migration-123"
    assert migration.hash == "test-hash-123"
    assert isinstance(migration.executed_at, datetime)

def test_get_migration_record():
    # Create migration record
    migration = DatabaseActor.create_migration({
        "id": "test-migration-get-456",
        "hash": "test-hash-get-456"
    })
    
    # Retrieve migration
    retrieved_migration = DatabaseActor.read_migration(migration.id)
    assert retrieved_migration.id == migration.id
    assert retrieved_migration.hash == migration.hash

def test_delete_migration_record():
    # Create migration record
    migration = DatabaseActor.create_migration({
        "id": "test-migration-del-789",
        "hash": "test-hash-del-789"
    })
    
    # Delete migration
    deleted = DatabaseActor.delete_migration(migration.id)
    assert deleted is True
    
    # Verify deletion
    retrieved_migration = DatabaseActor.read_migration(migration.id)
    assert retrieved_migration is None