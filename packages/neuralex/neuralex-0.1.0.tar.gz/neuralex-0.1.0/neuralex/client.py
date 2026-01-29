"""NeuraLex API client implementation."""

import httpx
from typing import List, Optional, Union
from .models import EmbeddingRequest, EmbeddingResponse
from .exceptions import AuthenticationError, RateLimitError, APIError, NeuraLexError


class NeuraLexClient:
    """Client for interacting with the NeuraLex Embedding API.

    Args:
        api_key: Your NeuraLex API key (starts with 'nlx_')
        base_url: Base URL for the API (default: https://api.neuralex.ca)
        timeout: Request timeout in seconds (default: 30)

    Example:
        >>> client = NeuraLexClient(api_key="nlx_your_api_key")
        >>> response = client.embed(["Hello, world!"])
        >>> print(response.payload[0].embedding[:5])
        [0.123, -0.456, 0.789, ...]
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.neuralex.ca",
        timeout: float = 30.0,
    ):
        if not api_key:
            raise AuthenticationError("API key is required")

        if not api_key.startswith("nlx_"):
            raise AuthenticationError("Invalid API key format (should start with 'nlx_')")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client connection."""
        self._client.close()

    def embed(
        self,
        inputs: Union[str, List[str]],
        model: Optional[str] = "public",
        language: str = "english",
        semantic_weight: float = 0.5,
    ) -> EmbeddingResponse:
        """Generate embeddings for the provided input text(s).

        Args:
            inputs: Text string or list of text strings to embed (max 100)
            model: Model name (default: "public")
            language: Language for lexeme extraction (default: "english")
            semantic_weight: Balance between term-based (0.0) and semantic (1.0)

        Returns:
            EmbeddingResponse containing embeddings and usage information

        Raises:
            AuthenticationError: Invalid or missing API key
            RateLimitError: Rate limit exceeded
            APIError: API returned an error response
            NeuraLexError: Other errors

        Example:
            >>> response = client.embed("Hello, world!")
            >>> embedding = response.payload[0].embedding
            >>> print(f"Dimensions: {len(embedding)}")
            Dimensions: 1024
        """
        # Normalize inputs to list
        if isinstance(inputs, str):
            inputs = [inputs]

        # Validate inputs
        if not inputs:
            raise ValueError("At least one input is required")
        if len(inputs) > 100:
            raise ValueError("Maximum 100 inputs allowed per request")

        # Create request
        request = EmbeddingRequest(
            inputs=inputs,
            model=model,
            language=language,
            semantic_weight=semantic_weight,
        )

        # Make API call
        try:
            response = self._client.post(
                f"{self.base_url}/api/v1/embed",
                json=request.model_dump(by_alias=True),
            )

            # Handle error responses
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise APIError(
                    error_data.get("message", "API request failed"),
                    response.status_code,
                    error_data,
                )

            response.raise_for_status()

            # Parse and return response
            return EmbeddingResponse.model_validate(response.json())

        except httpx.TimeoutException as e:
            raise NeuraLexError(f"Request timed out after {self.timeout}s") from e
        except httpx.RequestError as e:
            raise NeuraLexError(f"Request failed: {str(e)}") from e


class AsyncNeuraLexClient:
    """Async client for interacting with the NeuraLex Embedding API.

    Args:
        api_key: Your NeuraLex API key (starts with 'nlx_')
        base_url: Base URL for the API (default: https://api.neuralex.ca)
        timeout: Request timeout in seconds (default: 30)

    Example:
        >>> async with AsyncNeuraLexClient(api_key="nlx_your_api_key") as client:
        ...     response = await client.embed(["Hello, world!"])
        ...     print(response.payload[0].embedding[:5])
        [0.123, -0.456, 0.789, ...]
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.neuralex.ca",
        timeout: float = 30.0,
    ):
        if not api_key:
            raise AuthenticationError("API key is required")

        if not api_key.startswith("nlx_"):
            raise AuthenticationError("Invalid API key format (should start with 'nlx_')")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client connection."""
        await self._client.aclose()

    async def embed(
        self,
        inputs: Union[str, List[str]],
        model: Optional[str] = "public",
        language: str = "english",
        semantic_weight: float = 0.5,
    ) -> EmbeddingResponse:
        """Generate embeddings for the provided input text(s).

        Args:
            inputs: Text string or list of text strings to embed (max 100)
            model: Model name (default: "public")
            language: Language for lexeme extraction (default: "english")
            semantic_weight: Balance between term-based (0.0) and semantic (1.0)

        Returns:
            EmbeddingResponse containing embeddings and usage information

        Raises:
            AuthenticationError: Invalid or missing API key
            RateLimitError: Rate limit exceeded
            APIError: API returned an error response
            NeuraLexError: Other errors

        Example:
            >>> response = await client.embed("Hello, world!")
            >>> embedding = response.payload[0].embedding
            >>> print(f"Dimensions: {len(embedding)}")
            Dimensions: 1024
        """
        # Normalize inputs to list
        if isinstance(inputs, str):
            inputs = [inputs]

        # Validate inputs
        if not inputs:
            raise ValueError("At least one input is required")
        if len(inputs) > 100:
            raise ValueError("Maximum 100 inputs allowed per request")

        # Create request
        request = EmbeddingRequest(
            inputs=inputs,
            model=model,
            language=language,
            semantic_weight=semantic_weight,
        )

        # Make API call
        try:
            response = await self._client.post(
                f"{self.base_url}/api/v1/embed",
                json=request.model_dump(by_alias=True),
            )

            # Handle error responses
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise APIError(
                    error_data.get("message", "API request failed"),
                    response.status_code,
                    error_data,
                )

            response.raise_for_status()

            # Parse and return response
            return EmbeddingResponse.model_validate(response.json())

        except httpx.TimeoutException as e:
            raise NeuraLexError(f"Request timed out after {self.timeout}s") from e
        except httpx.RequestError as e:
            raise NeuraLexError(f"Request failed: {str(e)}") from e
