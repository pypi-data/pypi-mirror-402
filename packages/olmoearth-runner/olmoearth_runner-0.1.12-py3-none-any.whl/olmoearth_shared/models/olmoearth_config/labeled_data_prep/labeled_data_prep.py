from pydantic import BaseModel, Field

from olmoearth_shared.models.olmoearth_config.labeled_data_prep.data_splitter import DataSplitter
from olmoearth_shared.models.olmoearth_config.labeled_data_prep.samplers import AnnotationSampler
from olmoearth_shared.models.olmoearth_config.labeled_data_prep.window_preparers import WindowPreparer


class LabeledDataPrep(BaseModel):
    """Controls the preparation of labeled data for training."""
    sampler: AnnotationSampler = Field(description="Controls the sampling of annotated data for training.")
    window_preparer: WindowPreparer = Field(description="Controls the preparation of annotated spatiotemporal geometries into labeled rslearn windows.")
    data_splitter: DataSplitter = Field(description="Controls the splitting of labeled data into training, validation, and test sets.")
