SENTINEL2_L2A = "sentinel2_l2a"

# rslearn's task classes (SegmentationTask, ClassificationTask, etc.) all hardcode
# raw_inputs["targets"] in their process_inputs methods. When using SingleTaskModel,
# the input key must be "targets". When using MultiTask, input_mapping remaps to "targets".
TARGET = "targets"

# rslearn transforms use "target" as a special prefix for image_selectors,
# independent of the input key name. Format: "target/{field}" for SingleTask.
TARGET_SELECTOR_PREFIX = "target"

OLMOEARTH_SENTINEL2_L2A_BANDS = ["B02", "B03", "B04", "B08", "B05", "B06", "B07", "B8A", "B11", "B12", "B01", "B09"]

# OlmoEarth models are trained on Sentinel-2 data at 10m/pixel resolution
OLMOEARTH_ENCODER_RESOLUTION_METERS = 10.0
OLMOEARTH_MODULE_SELECTOR: list[str | int] = ["model", "encoder", 0]

LABEL_LAYER_NAME = "labels"
OUTPUT_LAYER_NAME = "output"

STAC_EO_CLOUD_COVER = "eo:cloud_cover"

DATA_SPLIT_KEY = "split"
DEFAULT_GROUP_NAME = "default"
