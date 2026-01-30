import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from olmoearth_shared.api.common.search_filters import KeywordFilter, SortDirection


class ContainerImageCreate(BaseModel):
    """Request model for creating a new container image."""
    name: str = Field(description="Canonical catalog name for this container image")
    gcp_gar_ref: str = Field(description="Google Cloud Artifact Registry reference")
    rslp_version: str | None = Field(default=None, description="RSLP version this image was built from")


class ContainerImageUpdate(BaseModel):
    id: uuid.UUID = Field(description="Unique identifier for this container image")
    gcp_gar_ref: str | None = Field(default=None, description="Google Cloud Artifact Registry reference")
    rslp_version: str | None = Field(default=None, description="RSLP version this image was built from")


class ContainerImageResponse(BaseModel):
    """Response model for container image data."""
    id: uuid.UUID = Field(description="Unique identifier for this container image")
    name: str = Field(description="Canonical catalog name for this container image")
    gcp_gar_ref: str = Field(description="Google Cloud Artifact Registry reference")
    aws_ecr_ref: str | None = Field(description="AWS Elastic Container Registry reference")
    beaker_ref: str | None = Field(description="Beaker-specific reference")
    rslp_version: str | None = Field(description="RSLP version this image was built from")
    created_at: datetime = Field(description="When this container image was created")
    updated_at: datetime = Field(description="When this container image was last updated")


class ContainerImageSortField(StrEnum):
    """Valid fields for sorting container images in search results."""
    CREATED_AT = "created_at"


class SearchContainerImagesRequest(BaseModel):
    """Request model for searching container images."""
    id: KeywordFilter[uuid.UUID] | None = Field(default=None, description="Unique identifier for this container image")
    name: KeywordFilter[str] | None = Field(default=None, description="Name of the container image")

    # Pagination and sorting
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: ContainerImageSortField = Field(default=ContainerImageSortField.CREATED_AT)
    sort_direction: SortDirection = Field(default=SortDirection.DESC)
