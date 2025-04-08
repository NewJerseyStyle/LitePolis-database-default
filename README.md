# LitePolis Database Module

Polis-compatible database layer with PostgreSQL and SQLModel implementation.

## Quick Start

### Installation
```bash
litepolis-cli add-deps litepolis-database-default
```

### Configuration
```yaml
# config.yaml
database:
  url: "postgresql://user:pass@localhost:5432/litepolis"
  # Optional:
  pool_size: 5
  timeout: 30
```

## Core API Usage

### Initialize
```python
from litepolis_database_default import DatabaseActor
db = DatabaseActor()
```

### User Management
```python
# Create user
user = db.create_user("email@example.com", "auth_token")

# Retrieve user
found_user = db.get_user(user.id)  # or db.get_user_by_email(email)
```

### Conversations
```python
# Start conversation
conv = db.start_conversation("Title", "Description")

# Post comment
comment = db.add_comment(conv.id, user.id, "Comment text")
```

## Data Schema

### Users (`users`)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    auth_token TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT false,
    created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Conversations (`conversations`)
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    is_archived BOOLEAN DEFAULT false,
    created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Error Handling

Common exceptions:
- `UserExistsError`: When creating duplicate users
- `NotFoundError`: When entities don't exist
- `IntegrityError`: Database constraint violations

```python
try:
    db.create_user("exists@example.com", "token")
except UserExistsError:
    # Handle duplicate user
```

## Testing

Run tests:
```bash
pytest tests/
```

Test configuration includes:
- Transaction-per-test rollback
- Test database isolation
- Fixture helpers

## Development

### Requirements
- Python 3.10+
- PostgreSQL 14+

### Project Structure
```
litepolis_database_default/
├── __init__.py       # Public interface
├── Actor.py          # DatabaseActor implementation  
├── models/           # SQLModel definitions
└── managers/         # Business logic layer
```

## License
MIT License
