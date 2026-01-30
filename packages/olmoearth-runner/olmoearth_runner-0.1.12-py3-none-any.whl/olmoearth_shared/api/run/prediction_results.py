import uuid
from datetime import datetime
from enum import StrEnum
from typing import Self

from geojson_pydantic.geometries import Geometry
from pydantic import BaseModel, Field, model_validator

from olmoearth_shared.api.common.api_common_models import ApiOutputModel
from olmoearth_shared.api.common.search_filters import DatetimeFilter, KeywordFilter, NumericFilter, SortDirection, StringFilter
from olmoearth_shared.api.run.inference_results_config import InferenceResultsConfig
from olmoearth_shared.api.run.model_pipelines import ModelPipelineResponse
from olmoearth_shared.api.run.prediction_geometry import PredictionResultCollection, PredictionResultFeature
from olmoearth_shared.api.run.workflow import WorkflowResponse


class PredictionResultFileProperties(BaseModel):
    """Properties for prediction output files."""

    filesize_bytes: int = Field(description="Size of the file in bytes")
    crs_code: str = Field(description="Coordinate Reference System code (e.g., EPSG:4326)")


class PredictionResultSortField(StrEnum):
    """Valid fields for sorting prediction results in search results."""
    START_DATETIME = "start_datetime"
    END_DATETIME = "end_datetime"
    CREATED_AT = "created_at"


class SearchPredictionResultsRequest(BaseModel):
    """Request model for searching prediction results"""
    id: KeywordFilter[uuid.UUID] | None = None
    model_pipeline_id: KeywordFilter[uuid.UUID] | None = None
    workflow_id: KeywordFilter[uuid.UUID] | None = None
    start_datetime: DatetimeFilter | None = None
    end_datetime: DatetimeFilter | None = None
    created_at: DatetimeFilter | None = None
    intersects_geometry: Geometry | None = Field(
        default=None,
        description="finds results whose geometry intersects with this geometry"
    )

    # Pagination and sorting
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: PredictionResultSortField = Field(default=PredictionResultSortField.CREATED_AT)
    sort_direction: SortDirection = Field(default=SortDirection.DESC)


class PredictionResultFileSortField(StrEnum):
    """Valid fields for sorting prediction result files in search results."""
    FILE_NAME = "file_name"
    START_DATETIME = "start_datetime"
    END_DATETIME = "end_datetime"


class SearchPredictionResultFilesRequest(BaseModel):
    """Request model for searching prediction result files"""
    id: KeywordFilter[uuid.UUID] | None = None
    prediction_result_id: KeywordFilter[uuid.UUID] | None = None
    file_name: StringFilter | None = None
    mime_type: KeywordFilter[str] | None = None
    file_path: StringFilter | None = None
    start_datetime: DatetimeFilter | None = None
    end_datetime: DatetimeFilter | None = None
    intersects_geometry: Geometry | None = Field(
        default=None,
        description="Finds files whose geometry intersects with this geometry"
    )

    # Pagination and sorting
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: PredictionResultFileSortField = Field(default=PredictionResultFileSortField.START_DATETIME)
    sort_direction: SortDirection = Field(default=SortDirection.DESC)


class PredictionResultFileResponse(BaseModel):
    """
    Response model for prediction result files.
    We always return this as part of the PredictionResult model below.
    """
    id: uuid.UUID
    prediction_result_id: uuid.UUID
    file_name: str
    mime_type: str
    geometry: Geometry
    file_path: str
    start_datetime: datetime
    end_datetime: datetime
    properties: PredictionResultFileProperties


class PredictionResultResponse(BaseModel):
    """
    Response model for prediction results.
    Include the Model Pipeline, Workflow, and all output files loaded.
    """
    id: uuid.UUID
    model_pipeline: ModelPipelineResponse
    workflow: WorkflowResponse
    geometry: Geometry
    start_datetime: datetime
    end_datetime: datetime
    inference_results_config: InferenceResultsConfig
    created_at: datetime
    output_files: list[PredictionResultFileResponse] = Field(default_factory=list)


class PropertyFilter(BaseModel):
    """
    When searching for GeoJSON features, this model allows the client to search on an arbitrary property
    in the GeoJSON feature's properties.
    """
    property_name: str = Field(description="name of field in geojson properties to search (e.g., 'name')")
    keyword_filter: KeywordFilter[str] | None = None
    string_filter: StringFilter | None = None
    numeric_filter: NumericFilter | None = None
    datetime_filter: DatetimeFilter | None = None

    @model_validator(mode='after')
    def has_exactly_one_filter(self) -> Self:
        filters = [self.keyword_filter, self.string_filter, self.numeric_filter, self.datetime_filter]
        if sum(f is not None for f in filters) != 1:
            raise ValueError("Exactly one filter must be provided")
        return self


class FeatureSortField(StrEnum):
    """Valid fields for sorting features in search results."""
    OE_CREATED_AT = "oe_created_at"
    OE_START_TIME = "oe_start_time"
    OE_END_TIME = "oe_end_time"


class SearchFeaturesRequest(BaseModel):
    """Request model for searching GeoJSON features stored in Elasticsearch."""

    id: KeywordFilter[str] | None = None
    intersects_geometry: Geometry | None = Field(
        default=None,
        description="Find features whose geometry intersects with this geometry"
    )

    # Known property filters (for convenience)
    oe_prediction_result_id: KeywordFilter[uuid.UUID] | None = None
    oe_prediction_result_file_id: KeywordFilter[uuid.UUID] | None = None
    oe_start_time: DatetimeFilter | None = None
    oe_end_time: DatetimeFilter | None = None
    oe_created_at: DatetimeFilter | None = None

    # Dynamic property filters for arbitrary properties
    property_filters: list[PropertyFilter] = Field(
        default_factory=list,
        description="Additional filters for arbitrary properties in the feature"
    )

    # Pagination and sorting
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: FeatureSortField = FeatureSortField.OE_CREATED_AT
    sort_direction: SortDirection = SortDirection.DESC


# We can respond with either a standard ApiOutputModel or a Geojson Feature Collection
SearchFeaturesResponse = ApiOutputModel[PredictionResultFeature] | PredictionResultCollection


class PixelCoordinates(BaseModel):
    """Coordinate information for a pixel value query."""
    lat: float = Field(description="Latitude of the input point (WGS84)")
    lon: float = Field(description="Longitude of the input point (WGS84)")
    row: int = Field(description="Row index of the pixel in the raster")
    col: int = Field(description="Column index of the pixel in the raster")


class BandClassification(BaseModel):
    """Classification metadata for a band value."""
    label: str = Field(description="Human-readable label for the classification value")
    color: tuple[int, int, int, int] = Field(description="RGBA color values (0-255)")


class BandRegression(BaseModel):
    """Regression metadata for a band value."""
    min_value: float = Field(description="Minimum possible value for this field")
    max_value: float = Field(description="Maximum possible value for this field")
    colormap_name: str = Field(description="Name of the colormap used for visualization")


class BandValue(BaseModel):
    """Value and metadata for a single band at a pixel location."""
    band_index: int = Field(description="1-based band index in the raster")
    property_name: str = Field(description="Property name from inference results config")
    raw_value: float | int = Field(description="Raw pixel value from the raster")
    classification: BandClassification | None = Field(default=None, description="Classification metadata if applicable")
    regression: BandRegression | None = Field(default=None, description="Regression metadata if applicable")


class PixelValueRecord(BaseModel):
    """Complete pixel value information for a single prediction result file."""
    coordinates: PixelCoordinates = Field(description="Coordinate information")
    prediction_result_file: PredictionResultFileResponse = Field(description="File that provided this data")
    bands: list[BandValue] = Field(description="Band values and metadata")
