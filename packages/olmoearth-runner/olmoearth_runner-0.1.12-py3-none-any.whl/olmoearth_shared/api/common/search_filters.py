from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generic, Self, TypeVar

from pydantic import BaseModel, model_validator

T = TypeVar("T")


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class KeywordFilter(BaseModel, Generic[T], extra='forbid'):
    """
    API query model for filtering keyword fields
    """
    eq: T | None = None
    neq: T | None = None
    inc: list[T] | None = None
    ninc: list[T] | None = None

    @model_validator(mode='after')
    def validate_fields(self) -> Self:
        if self.eq and self.neq:
            raise ValueError("Cannot specify both 'eq' and 'neq'")
        return self


class StringFilter(BaseModel, extra='forbid'):
    """
    API query model for filtering text fields
    """
    eq: str | None = None
    neq: str | None = None
    inc: list[str] | None = None
    ninc: list[str] | None = None
    like: str | None = None
    nlike: str | None = None

    @model_validator(mode='after')
    def validate_fields(self) -> Self:
        if self.eq and self.neq:
            raise ValueError("Cannot specify both 'eq' and 'neq'")
        return self


class DatetimeFilter(BaseModel, extra='forbid'):
    """
    API query model for filtering datetime fields
    """
    gte: datetime | None = None
    gt: datetime | None = None
    lte: datetime | None = None
    lt: datetime | None = None
    exists: bool | None = None

    @model_validator(mode='after')
    def validate_fields(self) -> Self:
        if self.gte and self.gt:
            raise ValueError("Cannot specify both 'gte' and 'gt'")
        if self.lte and self.lt:
            raise ValueError("Cannot specify both 'lte' and 'lt'")
        if self.exists is True and (self.gte or self.gt or self.lte or self.lt):
            # It doesn't make sense to ask for a field to exist and also filter on a range, the exists is redundant.
            raise ValueError("Cannot specify both 'exists = True' and a range filter")
        return self


class NumericFilter(BaseModel, extra='forbid'):
    """API query model for filtering numeric fields"""
    eq: float | None = None
    neq: float | None = None
    gte: float | None = None
    gt: float | None = None
    lte: float | None = None
    lt: float | None = None

    @model_validator(mode='after')
    def validate_fields(self) -> Self:
        if self.eq and self.neq:
            raise ValueError("Cannot specify both 'eq' and 'neq'")
        if self.gte and self.gt:
            raise ValueError("Cannot specify both 'gte' and 'gt'")
        if self.lte and self.lt:
            raise ValueError("Cannot specify both 'lte' and 'lt'")
        return self
