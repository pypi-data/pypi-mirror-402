from enum import Enum


class DataType(str, Enum):
    """Data type discriminator values"""
    RASTER = "raster"
    VECTOR = "vector"
