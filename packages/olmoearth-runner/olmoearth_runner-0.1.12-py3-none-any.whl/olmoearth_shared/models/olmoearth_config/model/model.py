from pydantic import BaseModel, Field

from olmoearth_shared.models.olmoearth_config.model.encoders import Encoder
from olmoearth_shared.models.olmoearth_config.model.tasks import ModelTask


class Model(BaseModel):
    encoder: Encoder = Field(description="The encoder to use for the model. This produces embeddings from preprocessed modality data for use as input to task heads.")
    tasks: dict[str, ModelTask] = Field(description="The tasks to perform with the embeddings produced by the encoder layer. Each task will produce predictions for the original inputs.")
