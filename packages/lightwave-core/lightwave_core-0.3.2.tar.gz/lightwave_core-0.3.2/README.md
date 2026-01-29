# lightwave-core

Shared Django utilities for LightWave Media projects.

## Installation

```bash
# Local development (from workspace root)
uv pip install -e packages/lightwave-core

# With billing support (Stripe)
uv pip install -e "packages/lightwave-core[billing]"

# In a project's requirements.txt
-e file:../../packages/lightwave-core
```

## Modules

### Storage (`lightwave.storage`)

CDN and S3 storage backends for static files and media.

```python
from lightwave.storage import StaticStorage, PublicMediaStorage, PrivateMediaStorage

# In settings.py
STORAGES = {
    "staticfiles": {"BACKEND": "lightwave.storage.StaticStorage"},
    "default": {"BACKEND": "lightwave.storage.PublicMediaStorage"},
}

# Configure static file prefix per project
LIGHTWAVE_STATIC_PREFIX = "static/my-project"
```

### Utils (`lightwave.utils`)

Common utilities including BaseModel, timezone helpers, slug generation.

```python
from lightwave.utils import BaseModel, get_common_timezones, get_next_unique_slug

class MyModel(BaseModel):
    # Automatically has created_at and updated_at fields
    name = models.CharField(max_length=100)
```

### Auth (`lightwave.auth`)

Base user model and authentication helpers.

```python
from lightwave.auth import BaseCustomUser, validate_profile_picture

class CustomUser(BaseCustomUser):
    # Inherits avatar, language, timezone, gravatar support
    # Add project-specific fields
    stripe_customer = models.ForeignKey(...)
```

### Chat (`lightwave.chat`)

Base models for AI chat sessions.

```python
from lightwave.chat import BaseChatSession, BaseChatMessage, ChatTypes, MessageTypes

class Chat(BaseChatSession):
    agent_type = models.CharField(...)

class ChatMessage(BaseChatMessage):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
```

## Development

### Setup

1. Install dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```
   This ensures code is automatically formatted and checked before each commit.

### Running Tests

```bash
uv run pytest
```

## Optional Dependencies

- `billing`: Stripe utilities via dj-stripe (`uv pip install lightwave-core[billing]`)
- `dev`: Testing utilities (`uv pip install lightwave-core[dev]`)
