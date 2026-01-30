from enum import StrEnum


class WorkflowType(StrEnum):
    """
    List of all Workflow types that can be created.
    **note**: this is an Enum in the database; changing this requires a migration. You cannot remove once added.
    """

    DATASET_BUILD = "DATASET_BUILD"
    DATASET_BUILD_FROM_WINDOWS = "DATASET_BUILD_FROM_WINDOWS"
    PREDICTION = "PREDICTION"
    FINE_TUNING = "FINE_TUNING"
