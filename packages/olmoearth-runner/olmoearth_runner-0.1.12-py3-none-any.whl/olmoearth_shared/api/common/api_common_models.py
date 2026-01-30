from enum import StrEnum
from typing import Generic, TypeAlias, TypeVar
from uuid import UUID

from httpx import Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from typing_extensions import deprecated

T = TypeVar("T")


class Metadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total: int | None = Field(default=None)


class ApiErrorCode(StrEnum):
    NOT_FOUND_ERROR = "not_found_error"
    PERMISSION_ERROR = "permission_error"
    SERVER_ERROR = "server_error"
    UNAUTHORIZED_ERROR = "unauthorized_error"
    VALIDATION_ERROR = "validation_error"
    NOT_IMPLEMENTED_ERROR = "not_implemented_error"


class ApiOutputError(BaseModel):
    code: ApiErrorCode
    message: str


class ApiOutputModel(BaseModel, Generic[T]):
    records: list[T] | None = Field(default=None)
    meta: Metadata | None = Field(default=None)
    errors: list[ApiOutputError] | None = Field(default=None)

    @classmethod
    def from_http_response(cls: type['ApiOutputModel[T]'], response: Response) -> 'ApiOutputModel[T]':
        """
        Helper method to parse an HTTP response into this class
        Handles errors by raising an exception that includes those errors.
        """
        url = response.request.url
        try:
            output = cls(**response.json())
        except ValidationError as e:
            # raise Exception(f"Failed to parse response from {url}: {response.text[0:1000]}") from e  # Revert to me
            raise Exception(f"Failed to parse response from {url}: {response.text}") from e
        except Exception as e:
            raise Exception(f"Unexpected error handling response from {url}: {response.text[0:1000]}") from e

        if not response.is_success:
            message = f"Received HTTP/{response.status_code} from {url} - {response.text}"
            raise ApiError(message, output, response.status_code)
        return output

    @classmethod
    def from_pydantic_validation_error(cls: type['ApiOutputModel[T]'], e: ValidationError) -> 'ApiOutputModel[T]':
        """
        Helper method to create an ApiOutputModel from a Pydantic ValidationError
        """
        errors = [
            ApiOutputError(code=ApiErrorCode.VALIDATION_ERROR,
                           message=f"Validation Error for {e.title}: {err['msg']} "
                                   f"[type={err['type']}, input_value={err['input']}, location={err['loc']}]")
            for err in e.errors()
        ]
        return cls(errors=errors)


@deprecated("Use ApiOutputModel[DeleteResource] instead")
class DeleteResource(BaseModel):
    """
    A response from a delete request
    """
    id: UUID
    deleted: bool


class ApiDeletionStatus(StrEnum):
    DELETED = "deleted"
    """Immediate deletion."""

    DELETION_QUEUED = "deletion_queued"
    """Queued for deletion."""

    REMOVED = "removed"
    """Removed as child of a parent record without deletion."""


class DeletionRead(BaseModel, Generic[T]):
    record: T = Field(..., description="The record targeted for deletion")
    status: ApiDeletionStatus = Field(
        ...,
        description=(
            "Indicates whether record was deleted immediately, queued for deletion, "
            "or removed as child of a parent without deletion."
        ),
    )


ApiDeletionModel: TypeAlias = ApiOutputModel[DeletionRead[T]]


class ApiError(Exception, Generic[T]):
    """
    An exception that can include the errors that were returned by an ApiOutputModel
    """

    errors: list[ApiOutputError]

    def __init__(self, message: str, api_output: ApiOutputModel[T], http_status_code: int) -> None:
        super().__init__(message)
        self.errors = api_output.errors or []
        self.http_status_code = http_status_code
