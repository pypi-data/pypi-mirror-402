"""Utility functions for hash-based data split assignment."""

import hashlib

from olmoearth_run.shared.models.data_split_type import DataSplitType
from olmoearth_shared.models.olmoearth_config.labeled_data_prep.data_splitter import SplitProportions


def hash_to_split_assignment(
    input_string: str, proportions: SplitProportions
) -> DataSplitType:
    """Convert a string to a deterministic data split assignment using SHA256 hash.

    This function creates a deterministic assignment by:
    1. Computing SHA256 hash of the input string
    2. Converting the hex digest to an integer
    3. Normalizing to [0, 1) range
    4. Assigning split based on cumulative proportions

    Args:
        input_string: String to hash for deterministic assignment
        proportions: Split proportions for train/val/test

    Returns:
        The assigned data split based on the hash
    """
    # Create deterministic hash from input string
    sha_hash = hashlib.sha256(input_string.encode()).hexdigest()

    # Convert full hash to integer and normalize to [0, 1)
    hash_int = int(sha_hash, 16)
    normalized_hash = hash_int / (2**256)

    # Assign split based on cumulative proportions
    if normalized_hash < proportions.train_prop:
        return DataSplitType.TRAIN
    elif normalized_hash < proportions.train_prop + proportions.val_prop:
        return DataSplitType.VAL
    else:
        return DataSplitType.TEST
