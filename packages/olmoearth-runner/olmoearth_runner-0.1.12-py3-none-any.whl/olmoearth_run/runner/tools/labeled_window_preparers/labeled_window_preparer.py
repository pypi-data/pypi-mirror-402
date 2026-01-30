from abc import ABC, abstractmethod
from typing import Generic

from olmoearth_run.runner.models.training.labeled_data import (
    AnnotationTask,
    TrainingWindowLabels,
    LabeledSTGeometry,
    LabeledWindow,
    RasterLabel,
)


class LabeledWindowPreparer(ABC, Generic[TrainingWindowLabels]):
    """Abstract base class for preparing labeled windows with generic label type."""

    @abstractmethod
    def prepare_labeled_windows(
        self,
        annotation_task: AnnotationTask,
    ) -> list[LabeledWindow[TrainingWindowLabels]]:
        """
        Prepare labeled windows from a single annotation task.

        The implementation should:
        1. Process the AnnotationTask to extract task context and annotations
        2. Transform annotation features into one or more training windows with labels
        3. Create one or more LabeledWindow objects with window properties and labels

        Args:
            annotation_task: Single AnnotationTask object containing task context and annotations

        Returns:
            List of LabeledWindow objects (can be 1 or more per task)
        """
        pass


class RasterLabelsWindowPreparer(LabeledWindowPreparer[list[RasterLabel]]):
    """Window preparer that produces raster (ndarray) labels."""

    @abstractmethod
    def prepare_labeled_windows(
        self,
        annotation_task: AnnotationTask,
    ) -> list[LabeledWindow[list[RasterLabel]]]:
        """Prepare labeled windows with raster labels."""
        pass


class VectorLabelsWindowPreparer(LabeledWindowPreparer[list[LabeledSTGeometry]]):
    """Window preparer that produces vector (LabeledSTGeometry list) labels."""

    @abstractmethod
    def prepare_labeled_windows(
        self,
        annotation_task: AnnotationTask,
    ) -> list[LabeledWindow[list[LabeledSTGeometry]]]:
        """Prepare labeled windows with vector labels."""
        pass
