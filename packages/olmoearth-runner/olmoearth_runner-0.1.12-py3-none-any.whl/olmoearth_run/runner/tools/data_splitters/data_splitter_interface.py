from olmoearth_run.runner.models.training.labeled_data import LabeledWindow
from olmoearth_run.shared.models.data_split_type import DataSplitType


class DataSplitterInterface:
    """Interface for assigning train/val/test splits to windows."""

    def choose_split_for_window(self, labeled_window: LabeledWindow) -> DataSplitType:
        """
        Choose a data split based on labeled window.

        Args:
            labeled_window: Complete labeled window with spatial, temporal and label information

        Returns:
            The assigned data split (train/val/test)
        """
        raise NotImplementedError
