# coach-app-baml-client

BAML-generated Pydantic models and client for coach-app boundary contracts.

## Installation

```bash
pip install coach-app-baml-client
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Usage

```python
from coach_app_baml_client.types import (
    ChatRequest,
    ChatResponse,
    EventEnvelope,
    EventType,
    MessageRole,
    ScheduledMessage,
    MessageStatus,
)

# Create a chat request
request = ChatRequest(
    message="Hello",
    conversationId="conv-123",
    conversationHistory=[],
)

# Parse an event envelope
envelope = EventEnvelope(
    type=EventType.MESSAGE_RECEIVED,
    meta=EventMeta(
        timestamp="2024-01-01T00:00:00Z",
        contractsVersion="1.0.0",
    ),
    payload={"content": "Hello"},
)
```

## Generated Code

The `baml_client/` directory contains BAML-generated code. Do not edit these files directly.

To regenerate:

```bash
# From repo root
baml-cli generate
```

## Version

This package version corresponds to the contracts version. Both Python and TypeScript packages are released together with the same version number.
