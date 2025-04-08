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

More usage in [Project Page](https://newjerseystyle.github.io/LitePolis-database-default)

## License
MIT Licensed. See [LICENSE](LICENSE) for details.
