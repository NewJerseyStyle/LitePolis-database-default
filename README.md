# LitePolis Database Default - SQLModel PoC StarRocks

Before running the script, admin must initialize the StarRocks with correct permission setup using this SQL:
```sql
CREATE DATABASE litepolis_default;

CREATE USER 'litepolis'@'%' IDENTIFIED BY 'securePass123!';  
GRANT ALL ON DATABASE litepolis_default TO 'litepolis'@'%';

CREATE ROLE table_operator;  
GRANT ALL ON ALL TABLES IN DATABASE litepolis_default TO ROLE table_operator;

GRANT table_operator TO USER 'litepolis'@'%';  
SET DEFAULT ROLE table_operator TO 'litepolis'@'%';  

SET GLOBAL activate_all_roles_on_login = TRUE;
```

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

More usage in [Project Page](https://newjerseystyle.github.io/LitePolis-database-default)

## License
MIT Licensed. See [LICENSE](LICENSE) for details.
