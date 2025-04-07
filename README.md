# LitePolis Database Default

This is the default database module that compatible with Polis.

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
```

3. Basic usage:
```python
from litepolis_database_default import DatabaseActor

db = DatabaseActor()
user = db.create_user("test@example.com", "secure-token")
conv = db.create_conversation("Welcome", "New user introduction")
```

## Data Model

### Core Tables

#### Users (`users`)
```mermaid
erDiagram
    users {
        int id PK
        string email
        string auth_token
        bool is_admin
        datetime created
        datetime modified
    }
```

#### Conversations (`conversations`)
```mermaid
erDiagram
    conversations {
        int id PK
        string title
        string description
        bool is_archived
        datetime created
        datetime modified
    }
```

#### Comments (`comments`)
```mermaid
erDiagram
    comments {
        int id PK
        string text
        int user_id FK
        int conversation_id FK
        int parent_comment_id FK
        datetime created
        datetime modified
    }
```

## API Reference

### DatabaseActor

#### User Management
```python
def create_user(email: str, auth_token: str, is_admin=False) -> User:
    """Create new user account
    Args:
        email: Unique email address
        auth_token: Authentication secret
        is_admin: Grant admin privileges
    Returns:
        User: Created user object
    """

def get_user(user_id: int) -> Optional[User]:
    """Retrieve user by ID
    Args:
        user_id: Primary key
    Returns:
        User if found, None otherwise
    """
```

#### Conversation Management
```python
def create_conversation(title: str, description: str) -> Conversation:
    """Start new discussion thread
    Args:
        title: Short description
        description: Full context
    Returns:
        Created conversation
    """

def archive_conversation(conversation_id: int) -> bool:
    """Mark conversation as archived
    Args:
        conversation_id: ID to archive
    Returns:
        True if successful
    """
```

## License
MIT Licensed. See LICENSE for details.
