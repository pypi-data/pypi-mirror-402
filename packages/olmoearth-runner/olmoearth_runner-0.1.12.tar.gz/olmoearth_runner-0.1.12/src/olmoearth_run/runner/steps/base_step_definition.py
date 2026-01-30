import logging
from abc import ABC, abstractmethod
from typing import Generic

from olmoearth_run.shared.models.api.task_args import (
    TaskArgsType,
)
from olmoearth_run.shared.models.api.task_results import (
    TaskResultsType,
)

logger = logging.getLogger(__name__)

class BaseStepDefinition(ABC, Generic[TaskArgsType, TaskResultsType]):

    @abstractmethod
    def run(self, task_args: TaskArgsType) -> TaskResultsType:
        """A StepDefinition is executed by calling this function"""
        ...

    def on_task_error(self, task_args: TaskArgsType, exc: Exception) -> None:
        """
        This function can be used to do anything on an error after the Task status is updated but before the Task stops.
        """
        pass
