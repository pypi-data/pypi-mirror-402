# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union
from typing_extensions import Literal, TypeAlias

from .._models import BaseModel

__all__ = [
    "ToolGetPerformWebTaskStatusResponse",
    "Data",
    "DataPerformWebTaskStatusSuccessResponseData",
    "DataPerformWebTaskStatusRunningResponseData",
    "DataPerformWebTaskStatusFailedResponseData",
]


class DataPerformWebTaskStatusSuccessResponseData(BaseModel):
    result: object
    """The outcome or answer produced by the autonomous task."""

    status: Literal["COMPLETED"]
    """The workflow has completed successfully."""


class DataPerformWebTaskStatusRunningResponseData(BaseModel):
    status: Literal["RUNNING"]
    """The workflow is currently running."""


class DataPerformWebTaskStatusFailedResponseData(BaseModel):
    error: str
    """Error message describing why the workflow failed."""

    status: Literal["FAILED"]
    """The workflow has failed."""


Data: TypeAlias = Union[
    DataPerformWebTaskStatusSuccessResponseData,
    DataPerformWebTaskStatusRunningResponseData,
    DataPerformWebTaskStatusFailedResponseData,
]


class ToolGetPerformWebTaskStatusResponse(BaseModel):
    data: Data
