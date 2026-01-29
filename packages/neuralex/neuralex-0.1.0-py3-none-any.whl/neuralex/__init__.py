"""NeuraLex Python Client Library

Official Python client for the NeuraLex Embedding API.
"""

from .client import NeuraLexClient, AsyncNeuraLexClient
from .models import EmbeddingRequest, EmbeddingResponse, EmbeddingData, Usage
from .exceptions import NeuraLexError, AuthenticationError, RateLimitError, APIError

__version__ = "0.1.0"
__all__ = [
    "NeuraLexClient",
    "AsyncNeuraLexClient",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "EmbeddingData",
    "Usage",
    "NeuraLexError",
    "AuthenticationError",
    "RateLimitError",
    "APIError",
]
