import logging

from geojson_pydantic import FeatureCollection
from pydantic import BaseModel, Field
from upath import UPath

from olmoearth_shared.api.run.prediction_geometry import PredictionRequestCollection, PredictionRequestFeature, \
    PredictionResultCollection
from olmoearth_shared.tools.gcs_tools import copy_gcs_file

logger = logging.getLogger(__name__)

GROUP_PREFIX = "group"

PREDICTION_REQUEST_GEOMETRY_FILE_NAME = "prediction_request_geometry.geojson"
PREDICTION_REQUEST_ALL_GEOMETRIES_FILE_NAME = "all_geometries.geojson"
PREDICTION_RESULT_VECTOR_FILE_NAME = "result.geojson"
PREDICTION_RESULT_RASTER_DIR = "results_raster"

PARTITIONS_DIR = "partitions"
PARTITION_GEOMETRY_FILE_NAME = "request.geojson"
PARTITION_WINDOWS_GEOMETRY_FILE_NAME = "windows.geojson"
PARTITION_PREDICTION_RESULT_VECTOR_FILE_NAME = "result.geojson"

PARTITION_PREDICTION_RESULT_RASTER_DIR = "results_raster"

WINDOW_REQUEST_FEATURE_FILE_NAME = "request.geojson"
WINDOW_RESULT_VECTOR_FILE_NAME = "result.geojson"

WINDOW_OUTPUT_LAYER_NAME = "output"
WINDOW_OUTPUT_BAND_NAME = "output"

WINDOW_OUTPUT_GEOJSON_FILE_NAME = "data.geojson"
WINDOW_OUTPUT_GEOTIFF_FILE_NAME = "geotiff.tif"



class PredictionScratchSpace(BaseModel):
    root_path: str = Field(description="The root directory of the scratch space")

    @classmethod
    def get_group(cls, partition_id: str) -> str:
        """Returns the name of the RSLearn group based on the partition ID"""
        return f"{GROUP_PREFIX}_{partition_id}"

    # Partition-related methods ###############################################
    @property
    def partitions_dir(self) -> str:
        """Path containing partition data"""
        return f"{self.root_path}/{PARTITIONS_DIR}"

    def get_partitions(self) -> list[str]:
        """Lists all partition IDs in the partitions directory"""
        partitions_path = UPath(self.partitions_dir)
        logger.info(f"Partitions directory: {partitions_path}")
        if not partitions_path.exists():
            logger.warning(f"Partitions directory does not exist: {partitions_path}")
            return []

        return [p.name for p in partitions_path.iterdir() if p.is_dir()]

    def get_partition_dir(self, partition_id: str) -> str:
        """Returns the directory for a specific partition ID"""
        return f"{self.partitions_dir}/{partition_id}"

    def get_partition_geometry_path(self, partition_id: str) -> str:
        """Returns the path to the partition-level geometry file"""
        return f"{self.get_partition_dir(partition_id)}/{PARTITION_GEOMETRY_FILE_NAME}"

    def get_partition_geometry(self, partition_id: str) -> PredictionRequestCollection:
        """Retrieves the partition-level geometry"""
        text = UPath(self.get_partition_geometry_path(partition_id)).read_text()
        return PredictionRequestCollection.model_validate_json(text)

    def write_partition_geometry(self, partition_id: str, geometry: PredictionRequestCollection) -> None:
        """Saves the partition-level geometry"""
        partition_dir = self.get_partition_dir(partition_id)
        logger.debug(f"Writing partition-level geometry geometry: {geometry} for partition {partition_id} to {partition_dir}")
        UPath(partition_dir).mkdir(parents=True, exist_ok=True)
        with UPath(self.get_partition_geometry_path(partition_id)).open("w") as file:
            file.write(geometry.model_dump_json(indent=2))

    def get_partition_result_vector_path(self, partition_id: str) -> UPath:
        """Returns the path to the partition-level prediction result PredictionRequestCollection file"""
        return UPath(self.get_partition_dir(partition_id)) / PARTITION_PREDICTION_RESULT_VECTOR_FILE_NAME

    def write_partition_result_vector(self, partition_id: str, collection: PredictionResultCollection) -> None:
        """Saves the partition-level prediction result PredictionResultCollection to a file."""
        with self.get_partition_result_vector_path(partition_id).open("w") as file:
            file.write(collection.model_dump_json(indent=2))

    def get_partition_result_raster_dir(self, partition_id: str) -> UPath:
        """Returns the directory where raster results for a partition are stored"""
        return UPath(self.get_partition_dir(partition_id)) / PARTITION_PREDICTION_RESULT_RASTER_DIR

    # Prediction request geometry methods #####################################
    @property
    def prediction_request_geometry_path(self) -> str:
        """Path to the prediction request geometry file, which is the GeoJSON that covers the entire prediction request"""
        return f"{self.root_path}/{PREDICTION_REQUEST_GEOMETRY_FILE_NAME}"

    @property
    def all_prediction_request_geometries_geojson(self) -> str:
        """Path to the prediction request geometry file, which is the GeoJSON that covers the entire prediction request"""
        return f"{self.root_path}/{PREDICTION_REQUEST_ALL_GEOMETRIES_FILE_NAME}"

    def get_prediction_request_geometry(self) -> PredictionRequestCollection:
        """Retrieves the original geometry submitted by the client that covers the entire prediction request"""
        text = UPath(self.prediction_request_geometry_path).read_text()
        return PredictionRequestCollection.model_validate_json(text)

    def write_prediction_request_geometry(self, geometry_gcs_path: str) -> None:
        """Saves the original geometry submitted by the client that covers the entire prediction request"""
        copy_gcs_file(geometry_gcs_path, self.prediction_request_geometry_path)

    def write_all_prediction_request_geometries_geojson(self, all_geometries: FeatureCollection) -> None:
        """Saves the combined collection of all geometries to a single GeoJSON file for visualization"""
        with UPath(self.all_prediction_request_geometries_geojson).open("w") as file:
            file.write(all_geometries.model_dump_json(indent=2))

    # Window-related methods ##################################################
    @staticmethod
    def get_window_request_feature_path(window_root: UPath) -> UPath:
        """Get the path to the file containing window's PredictionRequestFeature"""
        return UPath(f"{window_root}/{WINDOW_REQUEST_FEATURE_FILE_NAME}")

    def get_window_request_feature(self, window_root: UPath) -> PredictionRequestFeature:
        """Retrieves the window's PredictionRequestFeature from the window directory"""
        request_feature_json = self.get_window_request_feature_path(window_root).read_text()
        return PredictionRequestFeature.model_validate_json(request_feature_json)

    def write_window_request_feature(self, window_root: UPath, feature: PredictionRequestFeature) -> None:
        """Saves the PredictionRequestFeature file to the window directory"""
        logger.debug(f"Writing window request feature: {feature} to window {window_root}")
        with self.get_window_request_feature_path(window_root).open("w") as file:
            file.write(feature.model_dump_json(indent=2))

    @staticmethod
    def get_window_output_geojson_path(window_output_path: UPath) -> UPath:
        """
        RSLearn writes results to a data.geojson file in the window layer called "output".
        This behavior is defined by the configuration of the RslearnWriter callback in RunInferenceStepDefinition.
        """
        return window_output_path / WINDOW_OUTPUT_GEOJSON_FILE_NAME

    def get_window_prediction_result_collection(self, window_output_path: UPath) -> PredictionResultCollection | None:
        """
        Returns the per-window output GeoJSON generated by RunInferenceStepDefinition.
        If nothing was generated for this window, nothing is returned.
        """
        if not self.get_window_output_geojson_path(window_output_path).exists():
            return None
        output_json = self.get_window_output_geojson_path(window_output_path).read_text()
        return PredictionResultCollection.model_validate_json(output_json)

    @staticmethod
    def get_window_prediction_result_geotiff_path(window_output_path: UPath) -> UPath:
        """Returns the path to the GeoTIFF file generated for this window."""
        return window_output_path / WINDOW_OUTPUT_BAND_NAME / WINDOW_OUTPUT_GEOTIFF_FILE_NAME

    @staticmethod
    def get_window_result_vector_path(window_root: UPath) -> UPath:
        """
        For models that return vector-based results, this is the path that contains the complete result GeoJSON.
        The file is generated by combining elements from the request GeoJSON with elements from the output GeoJSON.

        The window result is the smallest complete element of the results of a prediction workflow.
        """
        return UPath(f"{window_root}/{WINDOW_RESULT_VECTOR_FILE_NAME}")

    def write_window_result_vector(self, window_root: UPath, window_result: PredictionResultCollection) -> None:
        """Saves the complete result vector for a window, which is the combination of the request and output GeoJSON"""
        logger.debug(f"Writing window result vector: {window_result} to window {self.get_window_result_vector_path(window_root)}")
        with self.get_window_result_vector_path(window_root).open("w") as file:
            file.write(window_result.model_dump_json(indent=2))

    # Prediction result vector methods ########################################
    @property
    def prediction_result_vector_path(self) -> str:
        """Path to the prediction result vector file, which is the complete result of the prediction request"""
        return f"{self.root_path}/results/{PREDICTION_RESULT_VECTOR_FILE_NAME}"

    def write_prediction_result_vector(self, prediction_result: PredictionResultCollection) -> None:
        """Saves the prediction result vector file, which is the complete result of the prediction request"""
        logger.debug(f"Writing prediction result vector to {self.prediction_result_vector_path}")
        UPath(self.prediction_result_vector_path).parent.mkdir(parents=True, exist_ok=True)
        with UPath(self.prediction_result_vector_path).open("w") as file:
            file.write(prediction_result.model_dump_json(indent=2))

    @property
    def prediction_result_raster_dir(self) -> str:
        """Path to the directory where raster results are stored"""
        return f"{self.root_path}/results/{PREDICTION_RESULT_RASTER_DIR}"
