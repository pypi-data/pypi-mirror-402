from enum import StrEnum


class Status(StrEnum):
    """
    A simple readable status enum used for Workflows, Steps, and Tasks
    **note** : This is an enum in the database; changing this will require a migration.
    """

    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"


FINISHED_STATUSES = [Status.COMPLETED, Status.COMPLETED_WITH_ERRORS, Status.CANCELLED, Status.FAILED]
UNFINISHED_STATUSES = [Status.PENDING, Status.RUNNING]
UNHEALTHY_TERMINAL_STATUSES = [Status.FAILED, Status.CANCELLED]
