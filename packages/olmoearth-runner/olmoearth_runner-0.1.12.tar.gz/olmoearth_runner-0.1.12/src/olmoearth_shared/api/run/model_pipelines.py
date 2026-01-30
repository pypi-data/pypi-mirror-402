from datetime import datetime
from enum import Enum
from uuid import UUID

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from olmoearth_shared.api.common.search_filters import DatetimeFilter, KeywordFilter, SortDirection, StringFilter
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig

# TODO: update all of these to match the new DB Models (esp data_root)
#  https://github.com/allenai/earth-system-run/issues/150


class ModelStageResponse(BaseModel):
    """ Model used when returning a Model Stage in an API response."""
    id: UUID
    stage_name: str
    stage_index: int
    data_root: str
    checkpoint_file: str | None = None
    dataset_config_file: str
    model_config_file: str
    olmoearth_run_config_file: str
    foundation_model_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    pipeline_id: UUID


class ModelPipelineResponse(BaseModel):
    """ Model used when returning a Model Pipeline in an API response."""
    id: UUID
    name: str
    container_image_id: UUID
    container_image: str  # For backwards compatibility with UI
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_stages: list[ModelStageResponse] = Field(default_factory=list)


class LegacyModelStageConfig(BaseModel):
    dataset_config_json: str
    model_config_yaml: str
    olmoearth_run_config_yaml: str

    @field_validator("model_config_yaml")
    @classmethod
    def validate_model_config_yaml(cls, v: str) -> str:
        # TODO(chrisw): I think this is going away; so I'm not going to copy it.
        # RslearnTemplateVars.validate_yaml(v)
        return v

    @field_validator('olmoearth_run_config_yaml')
    @classmethod
    def validate_olmoearth_run_config_yaml(cls, v: str) -> str:
        """Validate that olmoearth_run_config_yaml contains valid YAML syntax."""
        if not v.strip():
            raise ValueError("olmoearth_run_config_yaml cannot be empty")

        try:
            yaml.safe_load(v)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in olmoearth_run_config_yaml: {e}") from e

        # TODO: Add structural validation of YAML contents?

        return v


class ModelStageCreate(BaseModel):
    stage_name: str
    checkpoint_file_path: str | None = None
    legacy_config: LegacyModelStageConfig | None = Field(default=None, description="Legacy model stage config, mutually exclusive with olmoearth_config and olmoearth_config_id")
    olmoearth_config: OlmoEarthConfig | None = Field(default=None, description="OlmoEarth config, mutually exclusive with legacy_config and olmoearth_config_id")
    olmoearth_config_id: UUID | None = Field(default=None, description="ID of an existing OlmoEarth config in the olmoearth_configs table, mutually exclusive with legacy_config and olmoearth_config")
    foundation_model_id: UUID | None = None

    @model_validator(mode="after")
    def validate_config_mutex(self) -> "ModelStageCreate":
        """Validate that exactly one of legacy_config, olmoearth_config, or olmoearth_config_id is set."""
        has_legacy = self.legacy_config is not None
        has_unified = self.olmoearth_config is not None
        has_id = self.olmoearth_config_id is not None

        if has_legacy ^ has_unified ^ has_id:
            return self

        raise ValueError("Must specify exactly one of legacy_config, olmoearth_config, or olmoearth_config_id")



class ModelPipelineCreate(BaseModel):
    name: str
    container_image_id: UUID
    model_stages: list[ModelStageCreate]
    created_by_workflow_id: UUID | None = None

    @field_validator('model_stages')
    @classmethod
    def validate_model_stages_not_empty(cls, v: list[ModelStageCreate]) -> list[ModelStageCreate]:
        if not v or len(v) == 0:
            raise ValueError('model_stages must contain at least one stage')
        return v


class ModelStageUpdate(BaseModel):
    checkpoint_file_path: str | None = None


class ModelPipelineUpdate(BaseModel):
    """Model for updating a Model Pipeline's container image."""
    container_image_id: UUID


class ModelPipelineSortField(str, Enum):
    """Valid fields for sorting model pipelines in search results."""
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DELETED_AT = "deleted_at"


class SearchModelPipelinesRequest(BaseModel):
    """Request model for searching model pipelines"""
    id: KeywordFilter[UUID] | None = None
    name: StringFilter | None = None
    container_image_id: KeywordFilter[UUID] | None = None
    container_image: StringFilter | None = None
    created_by_workflow_id: KeywordFilter[UUID] | None = None
    created_at: DatetimeFilter | None = None
    updated_at: DatetimeFilter | None = None
    # By default, we hide deleted models from search results.
    deleted_at: DatetimeFilter | None = Field(default=DatetimeFilter(exists=False))

    # Pagination and sorting
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: ModelPipelineSortField = Field(default=ModelPipelineSortField.CREATED_AT)
    sort_direction: SortDirection = Field(default=SortDirection.DESC)
