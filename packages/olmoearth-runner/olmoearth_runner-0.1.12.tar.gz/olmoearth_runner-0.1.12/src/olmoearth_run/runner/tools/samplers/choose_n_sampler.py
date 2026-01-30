"""
Sampler that chooses a random subset of annotation tasks.

Useful for debugging workflows end to end with a smaller
dataset.
"""

import random

from olmoearth_run.runner.models.training.labeled_data import AnnotationTask
from olmoearth_run.runner.tools.samplers.sampler_interface import SamplerInterface


class ChooseNSampler(SamplerInterface):
    """Sampler that chooses a random subset of annotation tasks."""

    def __init__(self, n: int):
        self.n = n

    def sample(self, annotation_tasks: list[AnnotationTask]) -> list[AnnotationTask]:
        """Choose a random subset of annotation tasks."""
        return random.sample(annotation_tasks, self.n)
