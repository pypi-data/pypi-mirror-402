# NeuraLex Python Client

Official Python client library for the [NeuraLex](https://neuralex.ca) API.

## Installation

```bash
pip install neuralex
```

## Quick Start

```python
from neuralex import NeuraLexClient

# Initialize client with your API key
client = NeuraLexClient(api_key="nlx_your_api_key")

# Generate embeddings
response = client.embed("Hello, world!")

# Access the embedding vector
embedding = response.payload[0].embedding
print(f"Dimensions: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")
```

## Features

- ✅ Simple and intuitive API
- ✅ Synchronous and asynchronous support
- ✅ Type hints and Pydantic models
- ✅ Automatic error handling
- ✅ Configurable semantic/term-based balance
- ✅ Batch embedding support (up to 100 inputs)
- ✅ BYOE (Bring Your Own Embedding) mode support

## Usage

### Basic Usage

```python
from neuralex import NeuraLexClient

client = NeuraLexClient(api_key="nlx_your_api_key")

# Single text
response = client.embed("Machine learning is fascinating")
embedding = response.payload[0].embedding
```

### Batch Embeddings

```python
# Multiple texts
texts = [
    "First document",
    "Second document",
    "Third document"
]
response = client.embed(texts)

for item in response.payload:
    print(f"Text: {item.text}")
    print(f"Embedding dimensions: {len(item.embedding)}")
    print(f"Tokens used: {item.usage.total_tokens}")
```

### Adjusting Semantic Weight

The `semantic_weight` parameter controls the balance between term-based and semantic embeddings:
- `0.0` = Pure term-based (exact keyword matching)
- `1.0` = Pure semantic (meaning-based)
- `0.5` = Balanced (default)

```python
# More term-focused (better for keyword search)
response = client.embed(
    "Python programming",
    semantic_weight=0.3
)

# More semantic-focused (better for meaning-based search)
response = client.embed(
    "Python programming",
    semantic_weight=0.8
)
```

### Using Context Manager

```python
# Automatically handles connection cleanup
with NeuraLexClient(api_key="nlx_your_api_key") as client:
    response = client.embed("Hello, world!")
    print(response.payload[0].embedding[:5])
```

### Async Usage

```python
import asyncio
from neuralex import AsyncNeuraLexClient

async def main():
    async with AsyncNeuraLexClient(api_key="nlx_your_api_key") as client:
        response = await client.embed(["Text 1", "Text 2", "Text 3"])
        for item in response.payload:
            print(f"{item.text}: {len(item.embedding)} dimensions")

asyncio.run(main())
```

### BYOE (Bring Your Own Embedding) Mode

When the embed service is configured with `BYOE=true`, you can provide your own
pre-computed embeddings instead of generating them server-side:

```python
from neuralex import NeuraLexClient, EmbeddingInputData

client = NeuraLexClient(api_key="nlx_your_api_key")

# Create inputs with optional pre-computed embeddings
inputs = [
    # Provide your own embedding (must match server dimensions, typically 1024)
    EmbeddingInputData(text="hello world", embedding=[0.1] * 1024),
    # Or let the server compute the embedding
    EmbeddingInputData(text="server-computed text"),
]

response = client.embed(inputs)
```

**Note:** BYOE mode must be enabled on the server (`BYOE=true`). If BYOE is disabled,
providing embeddings will result in an error.

## Error Handling

```python
from neuralex import NeuraLexClient, AuthenticationError, RateLimitError, APIError

client = NeuraLexClient(api_key="nlx_your_api_key")

try:
    response = client.embed("Hello, world!")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded, please wait")
except APIError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## API Reference

### `NeuraLexClient`

Main client class for synchronous API calls.

**Methods:**

- `embed(inputs, model="public", language="english", semantic_weight=0.5)` - Generate embeddings

**Parameters:**

- `inputs` (str | List[str] | EmbeddingInputData | List[EmbeddingInputData]): Text or list of texts/EmbeddingInputData to embed (max 100)
- `model` (str, optional): Model name (default: "public")
- `language` (str, optional): Language for lexeme extraction (default: "english")
- `semantic_weight` (float, optional): Balance between term (0.0) and semantic (1.0) (default: 0.5)

**Returns:** `EmbeddingResponse` object

### `AsyncNeuraLexClient`

Async client class for asynchronous API calls. Same interface as `NeuraLexClient` but all methods are async.

### Models

#### `EmbeddingInputData`

- `text` (str): Text to embed (required)
- `embedding` (List[float] | None): Pre-computed embedding vector (optional, for BYOE mode)

#### `EmbeddingResponse`

- `payload` (List[EmbeddingData]): List of embedding results
- `model` (str): Model name used
- `total_usage` (Usage): Total token usage across all inputs

#### `EmbeddingData`

- `text` (str): Original input text
- `embedding` (List[float]): Vector embedding
- `usage` (Usage): Token usage for this input

#### `Usage`

- `total_tokens` (int): Total tokens processed

## Getting an API Key

1. Sign up at [app.neuralex.ca](https://app.neuralex.ca)
2. Generate a new API key
3. Keep your API key secure and never commit it to version control

## License

MIT License - see LICENSE file for details
