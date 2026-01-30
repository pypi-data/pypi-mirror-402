"""Custom exceptions for OlmoEarth Runner."""


class PartitioningError(Exception):
    """Raised when partitioning fails or produces invalid results."""
    pass


class NoPartitionsCreatedError(PartitioningError):
    """Raised when partitioning creates zero partitions."""
    pass


class NoWindowsCreatedError(PartitioningError):
    """Raised when partitioning creates zero windows."""
    pass
