"""Alert-related models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .common import AlertStatus, BaseModelConfig, Severity


class AlertEvent(BaseModelConfig):
    """An event associated with an alert."""

    event_id: str = Field(alias="eventId")
    log_type: str = Field(alias="logType")
    event_time: datetime | None = Field(default=None, alias="eventTime")
    data: dict[str, Any] = Field(default_factory=dict)


class AlertComment(BaseModelConfig):
    """A comment on an alert."""

    id: str
    body: str
    author: str
    created_at: datetime = Field(alias="createdAt")


class AlertDelivery(BaseModelConfig):
    """Alert delivery information."""

    output_id: str = Field(alias="outputId")
    output_type: str = Field(alias="outputType")
    dispatched_at: datetime | None = Field(default=None, alias="dispatchedAt")
    success: bool = True
    error_message: str | None = Field(default=None, alias="errorMessage")


class Alert(BaseModelConfig):
    """Represents a Panther alert."""

    id: str
    title: str
    description: str | None = None
    severity: Severity
    status: AlertStatus
    detection_id: str = Field(alias="detectionId")
    detection_type: str = Field(alias="detectionType")
    log_types: list[str] = Field(default_factory=list, alias="logTypes")

    # Timestamps
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
    first_event_at: datetime | None = Field(default=None, alias="firstEventAt")
    last_event_at: datetime | None = Field(default=None, alias="lastEventAt")

    # Assignment
    assignee_id: str | None = Field(default=None, alias="assigneeId")
    assignee_name: str | None = Field(default=None, alias="assigneeName")

    # Counts
    event_count: int = Field(default=0, alias="eventCount")

    # Related data
    runbook: str | None = None
    reference: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Destinations
    delivery_responses: list[AlertDelivery] = Field(
        default_factory=list, alias="deliveryResponses"
    )


class AlertSummary(BaseModelConfig):
    """Summary view of an alert for list operations."""

    id: str
    title: str
    severity: Severity
    status: AlertStatus
    detection_id: str = Field(alias="detectionId")
    created_at: datetime = Field(alias="createdAt")
    event_count: int = Field(default=0, alias="eventCount")


class AlertUpdate(BaseModelConfig):
    """Model for updating an alert."""

    status: AlertStatus | None = None
    assignee_id: str | None = Field(default=None, alias="assigneeId")


class AlertListParams(BaseModelConfig):
    """Parameters for listing alerts."""

    status: AlertStatus | str | None = None
    severity: Severity | str | None = None
    detection_id: str | None = Field(default=None, alias="detectionId")
    assignee_id: str | None = Field(default=None, alias="assigneeId")
    log_types: list[str] | None = Field(default=None, alias="logTypes")
    created_after: datetime | None = Field(default=None, alias="createdAfter")
    created_before: datetime | None = Field(default=None, alias="createdBefore")
    name_contains: str | None = Field(default=None, alias="nameContains")
    page_size: int = Field(default=50, alias="pageSize")
    cursor: str | None = None
