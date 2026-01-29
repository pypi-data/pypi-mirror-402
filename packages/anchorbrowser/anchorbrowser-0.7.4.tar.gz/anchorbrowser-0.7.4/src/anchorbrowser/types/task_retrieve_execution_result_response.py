# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["TaskRetrieveExecutionResultResponse", "Data"]


class Data(BaseModel):
    id: str
    """Unique identifier for the execution result"""

    start_time: datetime = FieldInfo(alias="startTime")
    """Execution start time"""

    status: Literal["success", "failure", "timeout", "cancelled"]
    """Execution status"""

    task_version_id: str = FieldInfo(alias="taskVersionId")
    """Task version identifier"""

    version: str
    """Version that was executed"""

    error_message: Optional[str] = FieldInfo(alias="errorMessage", default=None)
    """Error message if execution failed"""

    execution_time: Optional[float] = FieldInfo(alias="executionTime", default=None)
    """Execution duration in milliseconds"""

    output: Optional[str] = None
    """Task execution output"""


class TaskRetrieveExecutionResultResponse(BaseModel):
    data: Optional[Data] = None
