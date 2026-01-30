# RAG Agent SDK for Python

A comprehensive Python SDK for interacting with RAG Agent API services.

## Installation

```bash
pip install rag-agent-sdk
```

## Quick Start (3 Lines)

```python
from rag_agent_sdk import SyncRagAgentClient

client = SyncRagAgentClient(api_key="your-key")  # Or use RAG_AGENT_API_KEY env var
response = client.query.query("dataset-id", "What is RAG?")
print(response.response)
```

## Async Quick Start

```python
import asyncio
from rag_agent_sdk import RagAgentClient

async def main():
    # Initialize client (reads from environment variables if not specified)
    async with RagAgentClient(api_key="your-api-key") as client:
        
        # Create a dataset
        dataset = await client.datasets.create(
            name="my-knowledge-base",
            description="My first knowledge base"
        )
        print(f"Created dataset: {dataset.dataset_uuid}")
        
        # Upload a document
        result = await client.documents.upload(
            dataset_id=dataset.dataset_uuid,
            file="./documents/handbook.pdf"
        )
        print(f"Upload status: {result.status}")
        
        # Query the dataset
        response = await client.query.query(
            dataset_id=dataset.dataset_uuid,
            query="What is this document about?",
            mode="mix"
        )
        print(f"Answer: {response.response}")

asyncio.run(main())
```

## Authentication

The SDK supports multiple authentication methods:

### API Key Authentication
```python
client = RagAgentClient(
    base_url="http://localhost:9621",
    api_key="your-api-key"
)
```

### JWT Token Authentication
```python
client = RagAgentClient(
    base_url="http://localhost:9621",
    jwt_token="your-jwt-token"
)
```

### Supabase Authentication
```python
client = RagAgentClient(
    base_url="http://localhost:9621",
    supabase_url="https://xxx.supabase.co",
    supabase_anon_key="your-anon-key",
    supabase_access_token="user-access-token"
)
```

### Username/Password Authentication
```python
client = RagAgentClient(
    base_url="http://localhost:9621",
    username="admin",
    password="password"
)
```

## Features

### Dataset Management
```python
# List datasets
datasets = await client.datasets.list(page=1, page_size=20)

# Get dataset by ID
dataset = await client.datasets.get("dataset-uuid")

# Update dataset
updated = await client.datasets.update(
    dataset_id="dataset-uuid",
    description="Updated description"
)

# Delete dataset
await client.datasets.delete("dataset-uuid")
```

### Document Processing
```python
# Upload file
result = await client.documents.upload(
    dataset_id="dataset-uuid",
    file="./doc.pdf"
)

# Insert text
result = await client.documents.insert_text(
    dataset_id="dataset-uuid",
    text="Your text content here",
    source="manual-input"
)

# Batch insert
result = await client.documents.insert_batch(
    dataset_id="dataset-uuid",
    texts=["Text 1", "Text 2", "Text 3"],
    sources=["source1", "source2", "source3"]
)

# List documents
docs = await client.documents.list(dataset_id="dataset-uuid")

# Delete document
await client.documents.delete(dataset_id="dataset-uuid", doc_id="doc-id")
```

### RAG Queries
```python
# Basic query
response = await client.query.query(
    dataset_id="dataset-uuid",
    query="What is the main topic?",
    mode="mix"  # local, global, hybrid, naive, mix, bypass
)

# Streaming query
async for chunk in client.query.query_stream(
    dataset_id="dataset-uuid",
    query="Explain the concept in detail"
):
    print(chunk, end="", flush=True)

# Cross-dataset query
response = await client.query.cross_dataset_query(
    query="Compare the topics",
    dataset_ids=["uuid1", "uuid2"],
    enable_rerank=True
)

# Get context only (without LLM response)
context = await client.query.get_context(
    dataset_id="dataset-uuid",
    query="Find relevant information"
)
print(f"Entities: {context.entities}")
print(f"Chunks: {context.chunks}")
```

### Knowledge Graph
```python
# Get knowledge graph
graph = await client.graph.get_knowledge_graph(
    dataset_id="dataset-uuid",
    label="Person",
    max_depth=2,
    max_nodes=100
)

# Get all labels
labels = await client.graph.get_labels(dataset_id="dataset-uuid")

# Check entity exists
exists = await client.graph.check_entity_exists(
    dataset_id="dataset-uuid",
    entity_name="John Doe"
)

# Edit entity
await client.graph.edit_entity(
    dataset_id="dataset-uuid",
    entity_name="John Doe",
    updated_data={"description": "Updated description"},
    allow_rename=False
)
```

## Error Handling

```python
from rag_agent_sdk import (
    RagAgentError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    DatasetNotFoundError,
    ValidationError,
)

try:
    dataset = await client.datasets.get("non-existent-id")
except DatasetNotFoundError as e:
    print(f"Dataset not found: {e.dataset_id}")
except AuthenticationError:
    print("Authentication failed - check your credentials")
except AuthorizationError:
    print("Permission denied")
except RagAgentError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
```

## Sync vs Async Clients

```python
# Async client (recommended for production)
from rag_agent_sdk import RagAgentClient

async with RagAgentClient(api_key="your-key") as client:
    response = await client.query.query("dataset-id", "query")

# Sync client (for simple scripts)
from rag_agent_sdk import SyncRagAgentClient

with SyncRagAgentClient(api_key="your-key") as client:
    response = client.query.query("dataset-id", "query")
```

## Environment Variables

The SDK automatically reads configuration from environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `RAG_AGENT_BASE_URL` | Server URL | `http://localhost:9621` |
| `RAG_AGENT_API_KEY` | API key | - |
| `RAG_AGENT_JWT_TOKEN` | JWT token | - |
| `RAG_AGENT_TIMEOUT` | Timeout (seconds) | `30` |
| `RAG_AGENT_MAX_RETRIES` | Max retries | `3` |
| `RAG_AGENT_DEBUG` | Enable debug logging | `false` |

```python
# Uses environment variables automatically
from rag_agent_sdk import SyncRagAgentClient

client = SyncRagAgentClient()  # No parameters needed!
```

## Logging & Debugging

```python
from rag_agent_sdk import configure_logging

# Enable debug logging
configure_logging(level="DEBUG")

# Or enable debug mode on client
client = SyncRagAgentClient(debug=True)
```

## Mock Client for Testing

```python
from rag_agent_sdk import MockRagAgentClient

# Use mock client in tests (no real server needed)
client = MockRagAgentClient()

# Set custom responses
client.query.set_response("What is RAG?", "RAG is Retrieval-Augmented Generation...")

# Use like normal client
dataset = await client.datasets.create(name="test-kb")
response = await client.query.query(dataset.dataset_uuid, "What is RAG?")
assert "Retrieval-Augmented" in response.response
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | `localhost:9621` | RAG Agent server URL |
| `api_key` | str | None | API key for authentication |
| `jwt_token` | str | None | JWT token for authentication |
| `timeout` | float | 30.0 | Request timeout in seconds |
| `max_retries` | int | 3 | Maximum retry attempts |
| `debug` | bool | False | Enable debug logging |

## License

MIT License
