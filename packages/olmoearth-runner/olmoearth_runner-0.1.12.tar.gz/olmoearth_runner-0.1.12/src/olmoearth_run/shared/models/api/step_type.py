from enum import StrEnum


class StepType(StrEnum):
    """
    An enumerated type of all known steps in the OlmoEarthRun system.
    Different Workflows might implement these steps in different ways.
    """
    FINE_TUNE = "FINE_TUNE"
    PREPARE_LABELED_WINDOWS = "PREPARE_LABELED_WINDOWS"
    CREATE_PARTITIONS = "CREATE_PARTITIONS"
    DATASET_BUILD = "DATASET_BUILD"
    DATASET_BUILD_FROM_WINDOWS = "DATASET_BUILD_FROM_WINDOWS"
    RUN_INFERENCE = "RUN_INFERENCE"
    POSTPROCESS_PARTITION = "POSTPROCESS_PARTITION"
    COMBINE_PARTITIONS = "COMBINE_PARTITIONS"
