from datetime import datetime
from enum import StrEnum
from typing import Any, TypeVar

from pydantic import BaseModel, Field


class WorkflowStepStatus(StrEnum):
    """
        Enumeration of possible statuses for a workflow step,
    aligned with high-level
        Temporal execution states and application-specific logic.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep(BaseModel):
    """Represents a single step in a workflow execution graph."""

    id: str = Field(default="")
    name: str = Field(default="", description="The name of the workflow step")
    status: WorkflowStepStatus = Field(default=WorkflowStepStatus.PENDING)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: datetime | None = None
    children: list["WorkflowStep"] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class Visibility(BaseModel):
    steps: WorkflowStep = Field(default_factory=WorkflowStep, description="The steps in the workflow execution graph")
    trace_id: str = Field(
        default="", description="The trace ID for the workflow execution, used for tracing and debugging"
    )
    group_id: str = Field(
        default="", description="The session ID for the workflow execution, used for session management"
    )


TInput = TypeVar("TInput")
TResult = TypeVar("TResult")


class WorkflowProgress[TInput, TResult](BaseModel):
    """Standardized model for reporting workflow progress."""

    status_timeline: dict[str, WorkflowStepStatus] = Field(
        default_factory=dict, description="Timeline of workflow steps and their statuses (step_name, status)."
    )
    input: TInput | None = Field(default=None, description="The input with which the workflow was started.")
    result: TResult | None = Field(default=None, description="The final result of the workflow, if completed.")
    intermediate_results: dict[str, Any] = Field(
        default_factory=dict,
        description="A dictionary to hold any intermediate or supplementary data generated during execution.",
    )
