# LitePolis Database Default

This is the default database module that compatible with [Polis](https://github.com/CivicTechTO/polis/).

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

user = DatabaseActor.create_user({
    "email": "test@example.com",
    "auth_token": "auth_token",
})

conv = DatabaseActor.create_conversation({
    "title": "Test Conversation",
    "description": "This is a test conversation."
})
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

## License
MIT Licensed. See [LICENSE](LICENSE) for details.
