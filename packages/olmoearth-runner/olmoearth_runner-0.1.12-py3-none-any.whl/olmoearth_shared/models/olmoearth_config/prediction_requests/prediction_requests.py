from pydantic import BaseModel, Field

from olmoearth_shared.models.olmoearth_config.prediction_requests.partitioners import Partitioners
from olmoearth_shared.models.olmoearth_config.prediction_requests.postprocessors import Postprocessors


class PredictionRequests(BaseModel):
    """Controls the prediction requests for the model."""
    partitioners: Partitioners = Field(description="Controls the partitioning of the input data into smaller units.""")
    postprocessors: Postprocessors = Field(description="Controls the postprocessing of the prediction results and their assembly into final outputs.")
