# Burki Python SDK

Official Python SDK for the [Burki Voice AI Platform](https://burki.dev).

## Installation

```bash
pip install burki
```

## Quick Start

```python
from burki import BurkiClient

# Initialize the client
client = BurkiClient(api_key="your-api-key")

# List all assistants
assistants = client.assistants.list()
for assistant in assistants:
    print(f"{assistant.id}: {assistant.name}")

# Create a new assistant
assistant = client.assistants.create(
    name="Support Bot",
    description="Customer support assistant",
    llm_settings={
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "system_prompt": "You are a helpful customer support agent."
    },
    tts_settings={
        "provider": "elevenlabs",
        "voice_id": "rachel"
    }
)
```

## Features

### Assistants

```python
# List assistants
assistants = client.assistants.list()

# Get a specific assistant
assistant = client.assistants.get(assistant_id=123)

# Create an assistant
assistant = client.assistants.create(
    name="My Bot",
    llm_settings={"model": "gpt-4o-mini"}
)

# Update an assistant
assistant = client.assistants.update(
    assistant_id=123,
    name="Updated Bot"
)

# Delete an assistant
client.assistants.delete(assistant_id=123)
```

### Calls

```python
# List calls with filters
calls = client.calls.list(
    status="completed",
    date_from="2026-01-01",
    limit=50
)

# Get call details
call = client.calls.get(call_id=123)

# Get call transcripts
transcripts = client.calls.get_transcripts(call_id=123)

# Get call recordings
recordings = client.calls.get_recordings(call_id=123)

# Get call metrics
metrics = client.calls.get_metrics(call_id=123)

# Terminate an ongoing call
client.calls.terminate(call_sid="CA123...")
```

### Phone Numbers

```python
# Search available numbers
numbers = client.phone_numbers.search(
    country="US",
    area_code="415"
)

# Purchase a number
number = client.phone_numbers.purchase(
    phone_number="+14155551234",
    provider="twilio"
)

# Assign to an assistant
client.phone_numbers.assign(
    phone_number_id=123,
    assistant_id=456
)

# Release a number
client.phone_numbers.release(phone_number_id=123)
```

### Documents (RAG)

```python
# Upload a document
document = client.documents.upload(
    assistant_id=123,
    file_path="knowledge.pdf"
)

# List documents
documents = client.documents.list(assistant_id=123)

# Check processing status
status = client.documents.get_status(document_id=456)

# Delete a document
client.documents.delete(document_id=456)
```

### Tools

```python
# List tools
tools = client.tools.list()

# Create an HTTP tool
tool = client.tools.create(
    name="check_inventory",
    tool_type="http",
    description="Check product inventory",
    config={
        "method": "GET",
        "url": "https://api.example.com/inventory",
        "headers": {"Authorization": "Bearer {{API_KEY}}"}
    }
)

# Assign tool to assistant
client.tools.assign(tool_id=123, assistant_id=456)

# Discover AWS Lambda functions
lambdas = client.tools.discover_lambda(region="us-east-1")
```

### SMS

```python
# Send an SMS
message = client.sms.send(
    to="+14155551234",
    from_number="+14155559999",
    body="Hello from Burki!"
)

# Get conversations
conversations = client.sms.get_conversations(assistant_id=123)
```

### Campaigns

```python
# Create a campaign
campaign = client.campaigns.create(
    name="Outreach Campaign",
    assistant_id=123,
    contacts=[
        {"phone_number": "+14155551234", "name": "John"},
        {"phone_number": "+14155555678", "name": "Jane"}
    ]
)

# Start the campaign
client.campaigns.start(campaign_id=456)

# Get campaign progress
progress = client.campaigns.get(campaign_id=456)
```

### Real-time Streaming (WebSocket)

```python
import asyncio
from burki import BurkiClient

async def stream_transcripts():
    client = BurkiClient(api_key="your-api-key")
    
    # Stream live transcripts during a call
    async with client.realtime.live_transcript(call_sid="CA123...") as stream:
        async for event in stream:
            print(f"[{event.speaker}]: {event.content}")

asyncio.run(stream_transcripts())
```

```python
async def monitor_campaign():
    client = BurkiClient(api_key="your-api-key")
    
    # Stream campaign progress updates
    async with client.realtime.campaign_progress(campaign_id=123) as stream:
        async for update in stream:
            print(f"Progress: {update.completed}/{update.total}")

asyncio.run(monitor_campaign())
```

## Configuration

### Custom Base URL

```python
client = BurkiClient(
    api_key="your-api-key",
    base_url="https://custom.burki.dev"
)
```

### Timeout Settings

```python
client = BurkiClient(
    api_key="your-api-key",
    timeout=30.0  # seconds
)
```

### Async Usage

The SDK supports both sync and async usage:

```python
# Sync
assistants = client.assistants.list()

# Async
assistants = await client.assistants.list_async()
```

## Error Handling

```python
from burki import BurkiClient
from burki.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError
)

client = BurkiClient(api_key="your-api-key")

try:
    assistant = client.assistants.get(assistant_id=999)
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Assistant not found")
except ValidationError as e:
    print(f"Validation error: {e.message}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ServerError:
    print("Server error occurred")
```

## License

MIT License
