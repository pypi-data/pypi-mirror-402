# Kita Python SDK

The official Python SDK for the Kita Document Processing API.

## Installation

```bash
pip install kita-sdk
```

Or install from source:

```bash
cd sdk/python
pip install -e .
```

## Quick Start

```python
from kita import KitaClient

# Initialize client with your API key
client = KitaClient(api_key="kita_prod_...")

# Process a single document
result = client.process("statement.pdf", "bank_statement")

# Access parsed data
print(result.metadata)
print(result.transactions)
```

## Configuration

### API Key

Get your API key from https://api.usekita.com/api-keys.html

You can provide the API key in three ways:

```python
# 1. Pass directly to client
client = KitaClient(api_key="kita_prod_...")

# 2. Set environment variable
# export KITA_API_KEY=kita_prod_...
client = KitaClient()

# 3. Use .env file (with python-dotenv)
from dotenv import load_dotenv
load_dotenv()
client = KitaClient()
```

### Base URL

The SDK defaults to production (`https://api.usekita.com`). For local development:

```python
# Override with parameter
client = KitaClient(api_key="...", base_url="http://localhost:8080")

# Or set environment variable
# export KITA_API_URL=http://localhost:8080
```

## Usage

### Process Single Document

```python
from kita import KitaClient

client = KitaClient(api_key="kita_prod_...")

# Process and wait for result
result = client.process("document.pdf", "bank_statement")

# Access the data
print(result.metadata)           # Account info, dates, etc.
print(result.transactions)       # List of transactions
print(result.signals)            # Financial signals
print(result.raw)                # Full raw response
```

### Document Types

Supported document types (case-insensitive):

| Type | Description |
|------|-------------|
| `bank_statement` | Bank account statements |
| `passbook` | Savings passbooks |
| `payslip` | Salary/pay stubs |
| `bill` | Utility bills |
| `audited_financial_statement` | Annual reports, AFS |
| `other_document` | Other document types |

```python
# All these work
result = client.process("doc.pdf", "bank_statement")
result = client.process("doc.pdf", "BANK_STATEMENT")
result = client.process("doc.pdf", "Bank Statement")
```

### Async Processing

```python
# Don't wait for completion
result = client.process("large_doc.pdf", "bank_statement", wait=False)
print(result.raw)  # Contains documentId

# Check status later
doc = client.get_document(document_id)
print(doc.status)  # pending, processing, completed, failed
```

### Batch Processing

Process all documents in a folder:

```python
batch = client.batch_process("/path/to/folder", "payslip")

# Wait for all to complete
batch.wait()

# Get results
for result in batch.results():
    print(result.metadata)
    print(result.transactions)

# Check progress
print(batch.progress)  # {'total': 10, 'completed': 8, 'failed': 1, 'pending': 1}
```

Options:

```python
batch = client.batch_process(
    "/folder",
    "bank_statement",
    extensions=['.pdf', '.png', '.jpg'],  # File types to process
    recursive=True,                        # Search subdirectories
    wait=True                              # Wait for completion
)
```

### Error Handling

```python
from kita import (
    KitaClient,
    KitaError,
    KitaAPIError,
    KitaAuthenticationError,
    KitaRateLimitError
)

client = KitaClient(api_key="kita_prod_...")

try:
    result = client.process("document.pdf", "payslip")
except KitaAuthenticationError:
    print("Invalid API key")
except KitaRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except KitaAPIError as e:
    print(f"API Error {e.status_code}: {e.message}")
except KitaError as e:
    print(f"SDK Error: {e}")
```

### List Documents

```python
docs = client.list_documents(
    limit=50,
    offset=0,
    status='completed',
    document_type='bank_statement'
)
print(docs['documents'])
```

### Convenience Function

For quick one-off processing:

```python
from kita import process

# Uses KITA_API_KEY environment variable
result = process("document.pdf", "bank_statement")
```

## API Reference

### KitaClient

```python
client = KitaClient(
    api_key: str = None,      # API key (or set KITA_API_KEY env var)
    base_url: str = None,     # API URL (default: https://api.usekita.com)
    timeout: int = 60         # Request timeout in seconds
)
```

### Methods

#### `process(file_path, document_type, ...)`

Process a single document.

```python
result = client.process(
    file_path: str,           # Path to document
    document_type: str,       # Type of document
    wait: bool = True,        # Wait for completion
    poll_interval: int = 2,   # Seconds between status checks
    timeout: int = 600,       # Max wait time in seconds
    password: str = None      # PDF password if encrypted
)
```

Returns: `DocumentResult`

#### `batch_process(folder_path, document_type, ...)`

Process multiple documents from a folder.

```python
batch = client.batch_process(
    folder_path: str,         # Path to folder
    document_type: str,       # Type of documents
    wait: bool = False,       # Wait for completion
    extensions: list = None,  # File extensions (default: ['.pdf', '.png', '.jpg', '.jpeg'])
    recursive: bool = False   # Search subdirectories
)
```

Returns: `Batch`

#### `get_document(document_id)`

Get a processed document by ID.

Returns: `DocumentResult`

#### `list_documents(limit, offset, status, document_type)`

List processed documents.

Returns: `dict` with `documents` list

### DocumentResult

```python
result.status          # 'completed', 'failed', etc.
result.document_type   # 'bank_statement', etc.
result.metadata        # Dict with account info, dates, etc.
result.transactions    # List of transactions
result.signals         # Financial signals
result.raw             # Full raw response dict
result.to_dict()       # Convert to dictionary
```

### Batch

```python
batch.id               # Batch ID
batch.status()         # Get current status
batch.wait()           # Wait for completion
batch.results()        # Iterator of DocumentResult objects
batch.completed        # Boolean - is batch done?
batch.progress         # Dict with total/completed/failed/pending counts
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KITA_API_KEY` | API key | (required) |
| `KITA_API_URL` | API base URL | `https://api.usekita.com` |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black kita/
```

## License

MIT License

## Support

- Documentation: https://docs.usekita.com
- Email: support@usekita.com
