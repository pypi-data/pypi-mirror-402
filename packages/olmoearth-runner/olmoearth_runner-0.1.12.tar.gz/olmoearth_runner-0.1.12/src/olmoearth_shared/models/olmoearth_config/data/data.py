from pydantic import BaseModel

from olmoearth_shared.models.olmoearth_config.data.modalities import Modalities
from olmoearth_shared.models.olmoearth_config.data.output import Output
from olmoearth_shared.models.olmoearth_config.data.temporality import Temporality


class Data(BaseModel):
    temporality: Temporality
    modalities: Modalities
    output: Output | None
