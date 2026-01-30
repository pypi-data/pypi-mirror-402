"""Request and response models."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RequestStatus(StrEnum):
    """Status of a request to a service."""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Request(BaseModel):
    """A request to a deployed service."""

    id: UUID
    service_id: UUID
    sticky_key_value: str | None = Field(
        default=None,
        description="Extracted sticky key value for routing",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Request payload passed to the handler",
    )
    status: RequestStatus = RequestStatus.PENDING
    worker_id: UUID | None = None
    result_url: str | None = Field(
        default=None,
        description="S3 URL of the result for large responses",
    )
    result: dict[str, Any] | None = Field(
        default=None,
        description="Inline result for small responses",
    )
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}

    @property
    def duration_ms(self) -> int | None:
        """Calculate request duration in milliseconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None


class Response(BaseModel):
    """Response from a service handler."""

    request_id: UUID
    status: RequestStatus
    result: dict[str, Any] | None = None
    result_url: str | None = None
    error: str | None = None
    duration_ms: int | None = None


class InvokeRequest(BaseModel):
    """Request to invoke a service."""

    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Payload to pass to the handler",
    )
    sync: bool = Field(
        default=False,
        description="Wait for response (up to timeout)",
    )
    timeout_seconds: int | None = Field(
        default=None,
        description="Override default timeout",
    )


class InvokeResponse(BaseModel):
    """Response from invoking a service."""

    request_id: UUID
    status: RequestStatus
    result: dict[str, Any] | None = None
    result_url: str | None = None
    error: str | None = None
