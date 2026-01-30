"""
Interface for samplers that filter and sample annotation tasks.

Samplers operate on the complete set of annotation tasks and can apply
strategies that require a holistic view of the dataset, such as:
- Class balancing
- Geographic sampling
- Temporal sampling
- Quality filtering
- Size-based filtering
"""

from abc import ABC, abstractmethod

from olmoearth_run.runner.models.training.labeled_data import AnnotationTask


class SamplerInterface(ABC):
    """Interface for samplers that filter and sample annotation tasks."""

    @abstractmethod
    def sample(self, annotation_tasks: list[AnnotationTask]) -> list[AnnotationTask]:
        """
        Apply sampling/filtering strategies to annotation tasks.

        Args:
            annotation_tasks: Complete list of annotation tasks to sample from

        Returns:
            Filtered/sampled list of annotation tasks
        """
        pass
