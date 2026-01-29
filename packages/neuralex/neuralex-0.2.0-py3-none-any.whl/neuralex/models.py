"""Data models for NeuraLex API requests and responses."""

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class EmbeddingInputData(BaseModel):
    """Input data for embedding generation - text is required, embedding is optional."""

    text: str = Field(..., description="Text to embed (required)")
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Pre-computed embedding vector (optional, for BYOE mode)",
    )


class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""

    inputs: List[EmbeddingInputData] = Field(
        min_length=1,
        max_length=100,
        description="List of embedding inputs (max 100)",
    )
    model: Optional[str] = Field(
        default="public",
        description="Model name to use for embeddings",
    )
    language: str = Field(
        default="english",
        description="Language for lexeme extraction (only 'english' is supported)",
    )
    semantic_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        alias="semanticWeight",
        description="Balance between term-based (0.0) and semantic (1.0)",
    )

    model_config = {"populate_by_name": True}


class Usage(BaseModel):
    """Token usage information."""

    total_tokens: int = Field(alias="totalTokens")

    model_config = {"populate_by_name": True}


class EmbeddingData(BaseModel):
    """Individual embedding data."""

    text: str
    embedding: List[float]
    usage: Usage


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation."""

    payload: List[EmbeddingData]
    model: str
    total_usage: Usage = Field(alias="totalUsage")

    model_config = {"populate_by_name": True}
