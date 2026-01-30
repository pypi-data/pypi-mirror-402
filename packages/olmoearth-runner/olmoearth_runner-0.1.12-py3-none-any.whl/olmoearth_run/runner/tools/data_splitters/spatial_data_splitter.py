"""Splitter for assigning splits based on spatial grid cell location."""

from olmoearth_run.runner.models.training.labeled_data import LabeledWindow
from olmoearth_run.runner.tools.data_splitters.data_splitter_interface import (
    DataSplitterInterface,
)
from olmoearth_run.runner.tools.data_splitters.hash_assignment import (
    hash_to_split_assignment,
)
from olmoearth_run.shared.models.data_split_type import DataSplitType
from olmoearth_shared.models.olmoearth_config.labeled_data_prep.data_splitter import SplitProportions


class SpatialDataSplitter(DataSplitterInterface):
    """Data splitter that assigns splits based on spatial grid cell location.

    This splitter ensures that all windows within the same grid cell receive
    the same split assignment, maintaining geographic coherence while respecting
    the specified proportions across the entire dataset. Grid cells are created
    using the specified grid_size parameter in UTM coordinates.
    """

    def __init__(
        self, train_prop: float, val_prop: float, test_prop: float, grid_size: int
    ):
        """Initialize spatial data splitter with proportions for each split.

        Args:
            train_prop: Proportion of data for training (0.0 to 1.0)
            val_prop: Proportion of data for validation (0.0 to 1.0)
            test_prop: Proportion of data for testing (0.0 to 1.0)
            grid_size: Size of the grid cells in pixels

        Raises:
            ValueError: If proportions are negative or don't sum to 1.0
        """
        self.split_proportions = SplitProportions(train_prop=train_prop, val_prop=val_prop, test_prop=test_prop)
        self.grid_size = grid_size

    def choose_split_for_window(self, labeled_window: LabeledWindow) -> DataSplitType:
        """Choose a data split based on the grid cell containing the window's centroid.

        All windows within the same grid cell will receive the same split assignment.
        The split is determined by hashing the grid cell coordinates and using the hash
        to assign splits according to the configured proportions.

        Args:
            labeled_window: Complete labeled window with spatial, temporal and label information

        Returns:
            The assigned data split (train/val/test) based on the grid cell
        """
        grid_cell = (labeled_window.bounds[0] // self.grid_size, labeled_window.bounds[1] // self.grid_size)
        grid_cell_id = f"{labeled_window.projection.crs}_{grid_cell[0]}_{grid_cell[1]}"
        return hash_to_split_assignment(grid_cell_id, self.split_proportions)
