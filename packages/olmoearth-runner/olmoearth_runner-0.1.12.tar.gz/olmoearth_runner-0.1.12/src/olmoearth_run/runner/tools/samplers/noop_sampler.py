"""
No-op sampler that passes through all annotation tasks unchanged.

This is the default sampler when no sampling configuration is provided.
"""

from olmoearth_run.runner.models.training.labeled_data import AnnotationTask
from olmoearth_run.runner.tools.samplers.sampler_interface import SamplerInterface


class NoopSampler(SamplerInterface):
    """
    No-op sampler that returns all annotation tasks unchanged.

    This sampler performs no filtering or sampling operations and is used
    as the default when no sampler configuration is provided in the OlmoEarthRun config.
    """

    def sample(self, annotation_tasks: list[AnnotationTask]) -> list[AnnotationTask]:
        """
        Return all annotation tasks unchanged.

        Args:
            annotation_tasks: List of annotation tasks

        Returns:
            The same list of annotation tasks unchanged
        """
        return annotation_tasks
