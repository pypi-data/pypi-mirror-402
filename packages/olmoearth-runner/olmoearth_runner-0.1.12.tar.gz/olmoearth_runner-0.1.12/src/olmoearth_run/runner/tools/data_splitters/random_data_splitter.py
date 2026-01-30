import random

from olmoearth_run.runner.tools.data_splitters.data_splitter_interface import (
    DataSplitterInterface,
)
from olmoearth_run.shared.models.data_split_type import DataSplitType
from olmoearth_run.runner.models.training.labeled_data import LabeledWindow
from olmoearth_shared.models.olmoearth_config.labeled_data_prep.data_splitter import SplitProportions


class RandomDataSplitter(DataSplitterInterface):
    """Data splitter that randomly assigns splits based on specified proportions."""

    def __init__(
        self,
        train_prop: float,
        val_prop: float,
        test_prop: float,
        seed: int | None = None,
    ):
        """
        Initialize random data splitter with proportions for each split.

        Args:
            train_prop: Proportion of data for training (0.0 to 1.0)
            val_prop: Proportion of data for validation (0.0 to 1.0)
            test_prop: Proportion of data for testing (0.0 to 1.0)
            seed: Optional random seed for reproducible splits

        Raises:
            ValueError: If proportions are negative or don't sum to 1.0
        """
        self.split_proportions = SplitProportions(train_prop=train_prop, val_prop=val_prop, test_prop=test_prop)

        # Set up random state
        self.random = random.Random(seed)

    def choose_split_for_window(self, labeled_window: LabeledWindow) -> DataSplitType:
        """
        Randomly choose a data split based on configured proportions.

        This implementation ignores all window context properties and makes a purely
        random assignment based on the proportions specified at initialization.

        Args:
            window_context: Ignored (all properties ignored for random assignment)

        Returns:
            Randomly assigned data split
        """
        # Generate random number and assign split based on cumulative proportions
        rand_val = self.random.random()

        if rand_val < self.split_proportions.train_prop:
            return DataSplitType.TRAIN
        elif (
            rand_val
            < self.split_proportions.train_prop + self.split_proportions.val_prop
        ):
            return DataSplitType.VAL
        else:
            return DataSplitType.TEST
