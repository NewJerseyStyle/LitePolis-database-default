> ⚠️ This file is drafting for future repository of example database project for StarRocks integration

# Tutorial: Using StarRocks SQLModel Integration

## Overview
This tutorial explains how to use the custom StarRocks integration with SQLModel to create database tables that are compatible with StarRocks' specific requirements and features.

## 1. Basic Setup

First, add in your `pyprojects.toml`:
```yaml
dependencies = [
    "sqlmodel",
    "sqlparse",
    "inflection",
    "starrocks",
]

```


Then, ensure you have the necessary imports:

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from .utils_StarRocks import register_table
```

## 2. Model Definition

First create a normal SQLModel class.

```python
class YourModel(SQLModel, table=True):
    __tablename__ = "your_table_name"
    id: Optional[int] = Field(default=None, primary_key=True)
    # ... other fields ...
```

To make it StarRocks-compatible SQLModel class, use the `@register_table` decorator. Here's the basic pattern:

```python
@register_table(
    distributed_by="HASH(id)",  # Specify distribution key
    properties={                 # Optional StarRocks-specific properties
        "compression": "LZ4",
        "enable_persistent_index": "true",
        # Add other properties as needed
    }
)
class YourModel(SQLModel, table=True):
    __tablename__ = "your_table_name"
    id: Optional[int] = Field(default=None, primary_key=True)
    # ... other fields ...
```

### Key Components:

1. **@register_table Decorator Parameters**:
   - `distributed_by`: Specifies how StarRocks should distribute data (e.g., "HASH(id)")
   - `properties`: Dictionary of StarRocks-specific table properties

2. **Common Properties**:
   - `compression`: Data compression method (e.g., "LZ4")
   - `enable_persistent_index`: Enable/disable persistent indexing
   - `bloom_filter_columns`: Columns to use for bloom filtering

## 3. Real-World Examples

### Example 1: Simple User Model
```python
@register_table(
    distributed_by="HASH(id)",
    properties={
        "compression": "LZ4",
        "bloom_filter_columns": "email"  # Optimize email lookups
    }
)
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(
        unique=True, 
        sa_column_kwargs={"comment": "Unique email address"}
    )
    is_active: bool = Field(default=True)
```

### Example 2: Model with Foreign Keys
```python
@register_table(
    distributed_by="HASH(id)",
    properties={"compression": "LZ4"}
)
class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        default=None, 
        foreign_key="users.id",
        sa_column_kwargs={"comment": "Creator ID"}
    )
    title: str = Field(nullable=False)
```

### Example 3: Migration Record
```python
@register_table(distributed_by="HASH(id)")
class MigrationRecord(SQLModel, table=True):
    __tablename__ = "migrations"
    __table_args__ = (
        Index("ix_migrations_executed_at", "executed_at"),
    )
    id: str = Field(primary_key=True)  # Migration filename
    hash: str = Field(nullable=False)   # Content hash
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
```

## 4. Initialization in Your Application

To use these models in your application, follow this pattern (as shown in Actor.py):

```python
# Import all your models
from .Conversations import ConversationManager
from .Comments import CommentManager
from .Users import UserManager
from .Vote import VoteManager
from .Report import ReportManager
from .MigrationRecord import MigrationRecordManager

from .utils_StarRocks import create_db_and_tables

# Create tables at application startup
create_db_and_tables()

# Then define your manager/actor class
class DatabaseActor(UserManager, ConversationManager, CommentManager, 
                    VoteManager, ReportManager, MigrationRecordManager):
    # Your database interaction logic here
    pass
```

## 5. Best Practices

1. **Column Types**:
   - Primary keys using `Integer` will automatically be converted to `BIGINT`
   - Foreign keys will match their referenced column types
   - String fields should specify `max_length` when possible

2. **Comments and Documentation**:
   - Use `sa_column_kwargs={"comment": "..."}` to add column descriptions
   - Document table purpose using class docstrings

3. **Indexes and Constraints**:
   - Use `__table_args__` for indexes and additional constraints
   - Consider StarRocks-specific optimization features

4. **Properties Configuration**:
   - Use appropriate compression methods based on your data
   - Enable bloom filters for frequently queried columns
   - Configure persistent indexes when needed

## 6. Common Gotchas and Solutions

1. **Auto-incrementing IDs**:
   - Primary key integers are automatically handled as auto-increment
   - No need for explicit AUTO_INCREMENT configuration

2. **String Fields**:
   - Always specify length for VARCHAR fields using `VARCHAR(255)` syntax
   - Without length, fields default to StarRocks' STRING type

3. **Foreign Keys**:
   - Foreign key relationships are automatically configured
   - Types are automatically matched between primary and foreign keys

4. **Table Creation Order**:
   - Tables are created in the correct dependency order automatically
   - No need to manually manage creation sequence

## 7. Verification

After setting up your models, you can verify the table creation by:

1. Checking StarRocks logs for successful creation
2. Querying the table structure in StarRocks
3. Testing basic CRUD operations through your models

This integration handles the complexity of StarRocks' specific requirements while allowing you to write clean, SQLModel-style code. The `create_db_and_tables()` function automatically generates the appropriate DDL statements and executes them in the correct order.
