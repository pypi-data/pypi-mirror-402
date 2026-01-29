# OfSelf Python SDK

Official Python SDK for the [OfSelf API](https://api.ofself.ai) - Personal data sovereignty platform.

[![PyPI version](https://badge.fury.io/py/ofself.svg)](https://badge.fury.io/py/ofself)
[![Python versions](https://img.shields.io/pypi/pyversions/ofself.svg)](https://pypi.org/project/ofself/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install ofself
```

## Quick Start

```python
from ofself import OfSelfClient
from ofself.exceptions import NotFoundError, PermissionDenied

# Initialize the client with your API key
client = OfSelfClient(api_key="your-api-key")

# Create a node for a user
node = client.nodes.create(
    user_id="user-123",
    title="Meeting Notes",
    value="Discussed project timeline and milestones.",
    node_type="note",
    tag_ids=["tag-work"]
)
print(f"Created node: {node['id']}")

# List nodes
nodes = client.nodes.list(
    user_id="user-123",
    node_type="note",
    per_page=10
)
print(f"Found {nodes['total']} notes")

# Handle errors gracefully
try:
    node = client.nodes.get(user_id="user-123", node_id="invalid-id")
except NotFoundError:
    print("Node not found")
except PermissionDenied:
    print("User hasn't granted access")
```

## Features

- **Full API coverage**: Nodes, tags, files, relationships, proposals, and more
- **Type hints**: Full typing support with IDE autocomplete
- **Error handling**: Custom exceptions for different error types
- **Automatic retries**: Built-in retry logic for transient failures
- **Context manager**: Clean resource management

## API Resources

### Nodes

```python
# Create a node
node = client.nodes.create(
    user_id="user-123",
    title="My Note",
    value="Note content",
    node_type="note",
    node_metadata={"source": "sdk"},
    tag_ids=["tag-1", "tag-2"]
)

# List nodes with filters
nodes = client.nodes.list(
    user_id="user-123",
    node_type="note",
    tag_ids=["tag-work"],
    search="meeting",
    page=1,
    per_page=50
)

# Get a specific node
node = client.nodes.get(user_id="user-123", node_id="node-456")

# Update a node
node = client.nodes.update(
    user_id="user-123",
    node_id="node-456",
    title="Updated Title",
    value="Updated content"
)

# Delete a node
client.nodes.delete(user_id="user-123", node_id="node-456")

# Add/remove tags
client.nodes.add_tag(user_id="user-123", node_id="node-456", tag_id="tag-work")
client.nodes.remove_tag(user_id="user-123", node_id="node-456", tag_id="tag-old")
```

### Tags

```python
# Create a tag
tag = client.tags.create(
    user_id="user-123",
    name="Work",
    color="#4A90D9"
)

# List tags
tags = client.tags.list(user_id="user-123")

# Get nodes with a tag
nodes = client.tags.get_nodes(user_id="user-123", tag_id="tag-work")

# Get files with a tag
files = client.tags.get_files(user_id="user-123", tag_id="tag-work")
```

### Files

```python
# Upload a file
file = client.files.upload(
    user_id="user-123",
    file="/path/to/document.pdf",
    tag_ids=["tag-documents"]
)

# Upload from file object
with open("document.pdf", "rb") as f:
    file = client.files.upload(
        user_id="user-123",
        file=f,
        filename="my-document.pdf"
    )

# List files
files = client.files.list(
    user_id="user-123",
    content_type="application/pdf"
)

# Download file content
content = client.files.download(user_id="user-123", file_id="file-456")
with open("downloaded.pdf", "wb") as f:
    f.write(content)

# Delete a file
client.files.delete(user_id="user-123", file_id="file-456")
```

### Relationships

```python
# Create a relationship
rel = client.relationships.create(
    user_id="user-123",
    source_node_id="node-a",
    target_node_id="node-b",
    relationship_type="references",
    weight=0.8
)

# List relationships
rels = client.relationships.list(
    user_id="user-123",
    node_id="node-a"  # Get all relationships involving this node
)

# Delete a relationship
client.relationships.delete(user_id="user-123", relationship_id="rel-123")
```

### Proposals

Third-party apps propose changes; users approve or reject.

```python
# Create a proposal to add nodes
proposal = client.proposals.create(
    user_id="user-123",
    title="Extract Entities from Chunk 0",
    type="CREATE_NODE",
    canonical_data={
        "entities": [
            {
                "title": "Imported Note",
                "value": "Content from external app",
                "node_type": "note",
                "tags": ["imported"]
            }
        ]
    },
    raw_data={"source": "my-app", "original_id": "ext-123"}
)

# List pending proposals
proposals = client.proposals.list(
    user_id="user-123",
    status="pending"
)

# Approve a proposal
result = client.proposals.approve(
    user_id="user-123",
    proposal_id="prop-456"
)

# Reject a proposal
client.proposals.reject(
    user_id="user-123",
    proposal_id="prop-789",
    reason="Duplicate data"
)
```

### Exposure Profiles

Control what data is shared with apps.

```python
# Create an exposure profile
profile = client.exposure_profiles.create(
    user_id="user-123",
    name="Work Data Only",
    description="Share only work-related nodes",
    scope={
        "node_types": ["note", "document"],
        "tag_ids": ["tag-work"],
        "permissions": ["read"],
        "exclude_tag_ids": ["tag-private"]
    }
)

# List profiles
profiles = client.exposure_profiles.list(user_id="user-123")
```

### Sharing

```python
# Share data with a third-party app
share = client.sharing.create(
    user_id="user-123",
    third_party_id="app-456",
    exposure_profile_id="profile-789"
)

# List outgoing shares
shares = client.sharing.list_outgoing(user_id="user-123")

# Revoke a share
client.sharing.revoke(user_id="user-123", share_id="share-abc")
```

## Error Handling

The SDK raises specific exceptions for different error types:

```python
from ofself.exceptions import (
    OfSelfError,           # Base exception
    AuthenticationError,   # Invalid/missing API key (401)
    PermissionDenied,      # Access denied (403)
    NotFoundError,         # Resource not found (404)
    ValidationError,       # Invalid request data (400/422)
    RateLimitError,        # Rate limit exceeded (429)
    ServerError,           # Server error (5xx)
    ConnectionError,       # Network issues
)

try:
    node = client.nodes.get(user_id="user-123", node_id="invalid")
except NotFoundError as e:
    print(f"Not found: {e.message}")
    print(f"Status code: {e.status_code}")
except PermissionDenied as e:
    print("User hasn't granted access to this node")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except OfSelfError as e:
    print(f"API error: {e}")
```

## Configuration

```python
# Custom configuration
client = OfSelfClient(
    api_key="your-api-key",
    base_url="https://api.ofself.ai/api/v1",  # Default
    timeout=30.0,  # Request timeout in seconds
)

# Use as context manager for automatic cleanup
with OfSelfClient(api_key="your-api-key") as client:
    nodes = client.nodes.list(user_id="user-123")
```

## Development

```bash
# Clone the repository
git clone https://github.com/ofself/ofself-sdk-python.git
cd ofself-sdk-python

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black src/ tests/
isort src/ tests/
mypy src/

# Run all checks
pytest && black --check src/ && mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [API Documentation](https://docs.ofself.ai)
- [GitHub Repository](https://github.com/ofself/ofself-sdk-python)
- [PyPI Package](https://pypi.org/project/ofself/)
- [Changelog](https://github.com/ofself/ofself-sdk-python/blob/main/CHANGELOG.md)


