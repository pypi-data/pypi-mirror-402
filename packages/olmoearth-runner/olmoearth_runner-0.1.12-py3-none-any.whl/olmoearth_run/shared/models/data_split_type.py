from enum import StrEnum


class DataSplitType(StrEnum):
    """
    An enumerated type for data splits used in machine learning training.
    """
    TRAIN = "train"
    VAL = "val"
    TEST = "test"
