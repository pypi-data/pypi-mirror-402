from pydantic import BaseModel, Field

from olmoearth_shared.api.run.prediction_results import SearchFeaturesRequest, SearchPredictionResultFilesRequest


class DistributionItem(BaseModel):
    """Item in a distribution - can represent either a discrete class or a binned range."""
    value: int | str | float = Field(description="The class value or bin identifier")
    label: str = Field(description="Human-readable label")
    count: int = Field(description="Number of pixels/features in this class/bin", ge=0)
    percentage: float = Field(description="Percentage of total (0-100)", ge=0.0, le=100.0)
    rgb_color: tuple[int, int, int] | None = Field(
        default=None,
        description="RGB color for visualization (only for classification)"
    )


class RasterAnalyticsRequest(BaseModel):
    """
    Request for analytics over raster prediction results.
    Supports both classification and regression analytics.

    Example (classification):
        {
            "filters": {"intersects_geometry": {...}},
            "field_name": "land_cover"
        }

    Example (regression):
        {
            "filters": {"intersects_geometry": {...}},
            "field_name": "temperature",
            "num_bins": 20
        }
    """
    filters: SearchPredictionResultFilesRequest = Field(
        description="Filters to select raster data for analytics"
    )
    field_name: str = Field(
        description="Field name for analytics (automatically determined if classification or regression)"
    )
    num_bins: int = Field(
        default=10,
        ge=2,
        le=100,
        description="Number of bins for regression histograms (ignored for classification)"
    )


class VectorAnalyticsRequest(BaseModel):
    """
    Request for analytics over vector prediction results.
    Supports both classification and regression analytics.

    Example (classification):
        {
            "filters": {"intersects_geometry": {...}},
            "field_name": "land_cover"
        }

    Example (regression):
        {
            "filters": {"intersects_geometry": {...}},
            "field_name": "temperature",
            "num_bins": 20
        }
    """
    filters: SearchFeaturesRequest = Field(
        description="Feature-level filters to select vector data for analytics"
    )
    field_name: str = Field(
        description="Property name for analytics (automatically determined if classification or regression)"
    )
    num_bins: int = Field(
        default=10,
        ge=2,
        le=100,
        description="Number of bins for regression histograms (ignored for classification)"
    )


class PredictionResultsAnalytics(BaseModel):
    """Analytics response containing distribution metrics."""
    distribution: list[DistributionItem] = Field(
        description="Distribution of values - discrete classes for classification, histogram bins for regression"
    )
    total_count: int = Field(
        description="Total number of pixels/features analyzed",
        ge=0
    )
