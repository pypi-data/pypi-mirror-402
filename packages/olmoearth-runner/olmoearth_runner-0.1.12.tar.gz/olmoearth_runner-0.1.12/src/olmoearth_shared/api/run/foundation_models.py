"""Pydantic models for Foundation Model API requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from olmoearth_shared.api.common.search_filters import DatetimeFilter, KeywordFilter, StringFilter


class FoundationModelCreate(BaseModel):
    """Request model for creating a foundation model."""

    name: str = Field(..., description="Unique name for this foundation model")
    embedding_size: int = Field(..., description="The embedding size of the foundation model")
    data_root: str = Field(..., description="GCS path (gs:// format) containing model artifacts")


class FoundationModelResponse(BaseModel):
    """Response model for foundation model data."""

    id: UUID = Field(..., description="Unique identifier for the foundation model")
    name: str = Field(..., description="Unique name for this foundation model")
    embedding_size: int = Field(..., description="The embedding size of the foundation model")
    data_root: str = Field(..., description="GCS path (gs:// format) containing model artifacts")
    created_at: datetime = Field(..., description="Timestamp when the foundation model was created")
    updated_at: datetime = Field(..., description="Timestamp when the foundation model was last updated")


class SearchFoundationModelsRequest(BaseModel):
    """Request model for searching foundation models."""

    id: KeywordFilter[UUID] | None = Field(None, description="Filter by foundation model ID")
    name: StringFilter | None = Field(None, description="Filter by foundation model name")
    data_root: StringFilter | None = Field(None, description="Filter by data root path")
    created_at: DatetimeFilter | None = Field(None, description="Filter by creation date")
    updated_at: DatetimeFilter | None = Field(None, description="Filter by last update date")
    limit: int = Field(100, ge=0, le=1000, description="Maximum number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc or desc)")
