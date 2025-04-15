from litepolis_database_default.MigrationRecord import MigrationRecordManager
import pytest
from typing import Optional
from datetime import datetime, UTC

def test_create_migration_record():
    # Create migration record
    MigrationRecordManager.create_migration({
        "id": "test-migration-123",
        "hash": "test-hash-123"
    })
    migration = MigrationRecordManager.read_migration("test-migration-123")
    
    assert migration.id == "test-migration-123"
    assert migration.hash == "test-hash-123"
    assert isinstance(migration.executed_at, datetime)

def test_get_migration_record():
    # Create migration record
    migration_id = "test-migration-get-456"
    migration_hash = "test-hash-get-456"
    MigrationRecordManager.create_migration({
        "id": migration_id,
        "hash": migration_hash
    })
        
    # Retrieve migration
    retrieved_migration = MigrationRecordManager.read_migration(migration_id)
    assert retrieved_migration.id == migration_id
    assert retrieved_migration.hash == migration_hash

def test_delete_migration_record():
    # Create migration record
    MigrationRecordManager.create_migration({
        "id": "test-migration-del-789",
        "hash": "test-hash-del-789"
    })

    migration = MigrationRecordManager.read_migration("test-migration-del-789")
    
    # Delete migration
    deleted = MigrationRecordManager.delete_migration(migration.id)
    assert deleted is None
    
    # Verify deletion
    retrieved_migration = MigrationRecordManager.read_migration(migration.id)
    assert retrieved_migration is None