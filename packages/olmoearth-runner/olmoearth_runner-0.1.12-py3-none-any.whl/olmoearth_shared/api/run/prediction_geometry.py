from datetime import datetime

from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import Geometry
from pydantic import BaseModel, ConfigDict, Field


class PredictionRequestProperties(BaseModel):
    """
    Model representing the properties object on the features in a FeatureCollection
    """
    # We specifically want to allow and continue to propagate any custom properties that the client sends us.
    # so that they show up in the prediction results.
    model_config = ConfigDict(extra="allow")

    oe_start_time: datetime = Field(description="The beginning of the temporal component")
    oe_end_time: datetime = Field(description="The end of the temporal component")


PredictionRequestFeature = Feature[Geometry, PredictionRequestProperties]
PredictionRequestCollection = FeatureCollection[PredictionRequestFeature]


class PredictionResultProperties(BaseModel):
    """
    Model representing the properties object on the features in a FeatureCollection
    """
    model_config = ConfigDict(extra="allow")

    oe_start_time: datetime | None = Field(default=None, description="The beginning of the temporal component")
    oe_end_time: datetime | None = Field(default=None, description="The end of the temporal component")

    # These fields will be filled in by the Prediction Results Storage module.
    oe_prediction_result_id: str | None = None
    oe_prediction_result_file_id: str | None = None
    oe_created_at: datetime | None = None


PredictionResultFeature = Feature[Geometry, PredictionResultProperties]

PredictionResultCollection = FeatureCollection[PredictionResultFeature]
