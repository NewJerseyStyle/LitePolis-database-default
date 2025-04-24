# LitePolis Database Default

This is the default database module that compatible with [Polis](https://github.com/CivicTechTO/polis/). It provides a unified interface for interacting with the database, aggregating operations from various manager classes for Users, Conversations, Comments, and Votes.

## Quick Start

1. Install the module:
```bash
litepolis-cli add-deps litepolis-database-default
```

2. Configure database connection:
```yaml
# ~/.litepolis/litepolis.config
[litepolis_database_default]
database_url: "postgresql://user:pass@localhost:5432/litepolis"
# database_url: "starrocks://<User>:<Password>@<Host>:<Port>/<Catalog>.<Database>"
```

3. Basic usage:
```python
from litepolis_database_default import DatabaseActor

# Create a user
user = DatabaseActor.create_user({
    "email": "test@example.com",
    "auth_token": "auth_token",
})

# Create a conversation
conv = DatabaseActor.create_conversation({
    "title": "Test Conversation",
    "description": "This is a test conversation."
})

# Create a comment
comment = DatabaseActor.create_comment({
    "text_field": "This is a test comment.",
    "user_id": user.id,
    "conversation_id": conv.id,
})

# Create a vote
vote = DatabaseActor.create_vote({
    "value": 1,
    "user_id": user.id,
    "comment_id": comment.id
})
```

## API Reference

For detailed API documentation, including all available methods and their parameters, please refer to the generated documentation: [API references](https://newjerseystyle.github.io/LitePolis-database-default/apis.html)

## Detailed Usage Examples

The `DatabaseActor` class provides a unified interface to interact with different database entities. Below are examples for common operations:

### Users

| Column     | Type    | Description                               |
|------------|---------|-------------------------------------------|
| id         | INTEGER | Unique identifier for the user.           |
| email      | VARCHAR | User’s email address. Must be unique.     |
| auth_token | VARCHAR | Authentication token for the user.        |
| is_admin   | BOOLEAN | Indicates whether the user is an administrator. |
| created    | DATETIME| Timestamp indicating when the user was created. |
| modified   | DATETIME| Timestamp indicating when the user was last modified. |

```python
from litepolis_database_default import DatabaseActor
from datetime import datetime

# Create a user
user = DatabaseActor.create_user({
    "email": "test@example.com",
    "auth_token": "auth_token",
})

# Read a user by ID
user = DatabaseActor.read_user(user_id=1)

# Read a user by email
user = DatabaseActor.read_user_by_email(email="test@example.com")

# List users with pagination
users = DatabaseActor.list_users(page=1, page_size=10)

# Update a user
user = DatabaseActor.update_user(user_id=1, data={"email": "new_email@example.com"})

# Delete a user
success = DatabaseActor.delete_user(user_id=1)

# Search users by email
users = DatabaseActor.search_users_by_email(query="example.com")

# List users by admin status
users = DatabaseActor.list_users_by_admin_status(is_admin=True)

# List users created in a date range
start = datetime(2023, 1, 1)
end = datetime(2023, 1, 31)
users = DatabaseActor.list_users_created_in_date_range(start_date=start, end_date=end)

# Count users
count = DatabaseActor.count_users()
```

### Conversations

| Column      | Type    | Description                               |
|-------------|---------|-------------------------------------------|
| id          | INTEGER | Unique identifier for the conversation.   |
| user_id     | INTEGER | Foreign key referencing the user who created the conversation. |
| title       | VARCHAR | Title of the conversation.                |
| description | VARCHAR | Description of the conversation.          |
| is_archived | BOOLEAN | Indicates whether the conversation is archived. |
| created     | DATETIME| Timestamp indicating when the conversation was created. |
| modified    | DATETIME| Timestamp indicating when the conversation was last modified. |

```python
from litepolis_database_default import DatabaseActor
from datetime import datetime

# Create a conversation
conversation = DatabaseActor.create_conversation({
    "title": "New Conversation",
    "description": "A new conversation about a topic.",
    "user_id": 1 # Optional: Link to a user
})

# Read a conversation by ID
conversation = DatabaseActor.read_conversation(conversation_id=1)

# List conversations with pagination and ordering
conversations = DatabaseActor.list_conversations(page=1, page_size=10, order_by="title", order_direction="asc")

# Update a conversation
updated_conversation = DatabaseActor.update_conversation(conversation_id=1, data={"title": "Updated Title"})

# Delete a conversation
success = DatabaseActor.delete_conversation(conversation_id=1)

# Search conversations
conversations = DatabaseActor.search_conversations(query="search term")

# List conversations by archived status
conversations = DatabaseActor.list_conversations_by_archived_status(is_archived=True)

# List conversations created in a date range
start = datetime(2023, 1, 1)
end = datetime(2023, 1, 31)
conversations = DatabaseActor.list_conversations_created_in_date_range(start_date=start, end_date=end)

# Count conversations
count = DatabaseActor.count_conversations()

# Archive a conversation
archived_conversation = DatabaseActor.archive_conversation(conversation_id=1)
```

### Comments

| Column          | Type    | Description                               |
|-----------------|---------|-------------------------------------------|
| id              | INTEGER | Primary key for the comment.              |
| text_field      | VARCHAR | The content of the comment.               |
| user_id         | INTEGER | Foreign key referencing the user who created the comment. |
| conversation_id | INTEGER | Foreign key referencing the conversation the comment belongs to. |
| parent_comment_id| INTEGER | Foreign key referencing the parent comment (for replies). |
| created         | DATETIME| Timestamp of when the comment was created. |
| modified        | DATETIME| Timestamp of when the comment was last modified. |

```python
from litepolis_database_default import DatabaseActor
from datetime import datetime

# Create a comment
comment = DatabaseActor.create_comment({
    "text_field": "This is a comment.",
    "user_id": 1,
    "conversation_id": 1,
    # "parent_comment_id": 2 # Optional: for replies
})

# Read a comment by ID
comment = DatabaseActor.read_comment(comment_id=1)

# List comments by conversation ID
comments = DatabaseActor.list_comments_by_conversation_id(conversation_id=1, page=1, page_size=10, order_by="created", order_direction="asc")

# Update a comment
updated_comment = DatabaseActor.update_comment(comment_id=1, data={"text_field": "Updated comment text."})

# Delete a comment
success = DatabaseActor.delete_comment(comment_id=1)

# Search comments
comments = DatabaseActor.search_comments(query="search term")

# List comments by user ID
comments = DatabaseActor.list_comments_by_user_id(user_id=1, page=1, page_size=10)

# List comments created in a date range
start = datetime(2023, 1, 1)
end = datetime(2023, 1, 31)
comments = DatabaseActor.list_comments_created_in_date_range(start_date=start, end_date=end)

# Count comments in a conversation
count = DatabaseActor.count_comments_in_conversation(conversation_id=1)

# Get a comment with its replies
comment = DatabaseActor.get_comment_with_replies(comment_id=1)
```

### Votes

| Column     | Type    | Description                               |
|------------|---------|-------------------------------------------|
| id         | INTEGER | Primary key for the vote.                 |
| user_id    | INTEGER | Foreign key referencing the user who created the vote. |
| comment_id | INTEGER | Foreign key referencing the comment being voted on. |
| value      | INTEGER | The value of the vote.                    |
| created    | DATETIME| Timestamp of when the vote was created.   |
| modified   | DATETIME| Timestamp of when the vote was last modified. |

```python
from litepolis_database_default import DatabaseActor
from datetime import datetime

# Create a new vote
vote = DatabaseActor.create_vote({
    "value": 1, # e.g., 1 for upvote, -1 for downvote
    "user_id": 1,
    "comment_id": 1
})

# Read a vote by ID
vote = DatabaseActor.read_vote(vote_id=1)

# Get a vote by user and comment
vote = DatabaseActor.get_vote_by_user_comment(user_id=1, comment_id=1)

# List votes by comment ID with pagination and ordering
votes = DatabaseActor.list_votes_by_comment_id(comment_id=1, page=1, page_size=10, order_by="created", order_direction="asc")

# Update a vote
updated_vote = DatabaseActor.update_vote(vote_id=1, data={"value": -1})

# Delete a vote
success = DatabaseActor.delete_vote(vote_id=1)

# List votes by user ID with pagination
votes = DatabaseActor.list_votes_by_user_id(user_id=1, page=1, page_size=10)

# List votes created in a date range
start = datetime(2023, 1, 1)
end = datetime(2023, 1, 31)
votes = DatabaseActor.list_votes_created_in_date_range(start_date=start, end_date=end)

# Count votes for a comment
count = DatabaseActor.count_votes_for_comment(comment_id=1)

# Get vote value distribution for a comment
distribution = DatabaseActor.get_vote_value_distribution_for_comment(comment_id=1)
```

## StarRocks Integration

This module includes custom integration with StarRocks using SQLModel. This allows defining database tables that are compatible with StarRocks' specific requirements and features, such as distribution keys and properties.

To leverage this integration, use the `@register_table` decorator on your SQLModel classes:

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, UTC
from .utils_StarRocks import register_table
from sqlalchemy import Index # Import Index for table_args

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

Key aspects of the StarRocks integration:
-   `@register_table` decorator: Used to specify StarRocks-specific DDL hints like `distributed_by` and `properties`.
-   `distributed_by`: Defines the distribution strategy for the table (e.g., `HASH(column)`).
-   `properties`: A dictionary for setting StarRocks table properties like `compression`, `enable_persistent_index`, `bloom_filter_columns`, etc.
-   Automatic DDL Generation: The `create_db_and_tables()` function (used internally by `DatabaseActor` initialization) generates the appropriate StarRocks DDL based on the registered models and their hints.
-   Handling of SQLModel features: The integration handles standard SQLModel features like primary keys, foreign keys, and indexes, translating them into StarRocks-compatible DDL where necessary.

For more details on the StarRocks integration, refer to the `utils_StarRocks.py` module and the API documentation.

## License
MIT Licensed. See [LICENSE](LICENSE) for details.
