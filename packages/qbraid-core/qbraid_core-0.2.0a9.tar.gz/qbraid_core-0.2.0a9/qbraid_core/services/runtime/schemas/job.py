# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Pydantic schemas for job API requests and responses.
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator

from qbraid_core.decimal import Credits

from .enums import ExperimentType, JobStatus


class TimeStamps(BaseModel):
    """Model for capturing time-related information in an experiment."""

    createdAt: datetime
    endedAt: Optional[datetime] = None
    executionDuration: Optional[int] = Field(
        default=None, ge=0, description="Execution time in milliseconds"
    )

    @field_validator("createdAt", "endedAt", mode="before")
    @classmethod
    def parse_datetimes(cls, value: Union[str, datetime, None]) -> Optional[datetime]:
        """Parse datetime values from strings or datetime objects."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            # Handle 'Z' suffix for Python 3.9/3.10 compatibility
            # Python 3.11+ supports 'Z' directly in fromisoformat, but older versions don't
            if sys.version_info < (3, 11) and isinstance(value, str) and value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"Unable to parse timestamp: {value}") from exc

    @model_validator(mode="after")
    def set_execution_duration(self):
        """Calculate execution duration if not provided but start and end times are available."""
        if self.executionDuration is None and self.createdAt and self.endedAt:
            duration = (self.endedAt - self.createdAt).total_seconds() * 1000
            self.executionDuration = int(duration)  # pylint: disable=invalid-name
        return self


class Program(BaseModel):
    """Schema for quantum program"""

    format: Literal[
        "qasm2",
        "qasm3",
        "qir.bc",
        "qir.ll",
        "analog",
        "pulser.sequence",
        "quil",
        "ionq.circuit.v0",
        "problem",
    ] = Field(..., description="Program format")
    data: Any = Field(..., description="Program data")


class JobBase(BaseModel):
    """Schema for job base model"""

    name: Optional[str] = Field(None, description="Job name")
    shots: int = Field(..., gt=0, description="Number of shots to execute")
    deviceQrn: str = Field(..., description="qBraid device resource name")
    tags: dict[str, Union[str, int, bool]] = Field(default_factory=dict, description="Job tags")
    runtimeOptions: dict[str, Any] = Field(default_factory=dict, description="Runtime options")


class JobRequest(JobBase):
    """Schema for job submission request body"""

    program: Program


class RuntimeJob(JobBase):
    """Schema for runtime job model"""

    jobQrn: str = Field(..., description="qBraid job resource name")
    batchJobQrn: Optional[str] = Field(None, description="Batch job resource name")
    vendor: Literal["aws", "azure", "ibm", "ionq", "qbraid"] = Field(..., description="Vendor name")
    provider: Literal[
        "aqt",
        "aws",
        "azure",
        "equal1",
        "ibm",
        "iqm",
        "ionq",
        "nec",
        "oqc",
        "pasqal",
        "quantinuum",
        "quera",
        "rigetti",
        "qbraid",
    ] = Field(..., description="Provider name")
    status: JobStatus = Field(..., description="Job status")
    statusMsg: Optional[str] = Field(None, description="Job status message")
    experimentType: ExperimentType = Field(..., description="Experiment type")
    queuePosition: Optional[int] = Field(None, ge=0, description="Job queue position")
    timeStamps: Optional[TimeStamps] = Field(None, description="Job time stamps")
    cost: Optional[Credits] = Field(None, description="Job cost in credits")
    estimatedCost: Credits = Field(..., ge=0, description="Job estimated cost in credits")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Job metadata")

    @field_validator("vendor", "provider", mode="before")
    @classmethod
    def normalize_to_lowercase(cls, value: Any) -> str:
        """Normalize vendor and provider to lowercase for API compatibility.

        Handles both string values and nested objects like:
        {"_id": "...", "provider": "AWS"}
        """
        if isinstance(value, dict):
            # API returns provider as nested object: {"_id": "...", "provider": "AWS"}
            # Extract the actual provider name
            value = value.get("provider") or value.get("vendor") or value.get("name", "")
        if isinstance(value, str):
            return value.lower()
        return value

    @field_serializer("estimatedCost", "cost")
    def serialize_credits(self, value: Optional[Credits]) -> Optional[float]:
        """Serialize Credits to float for JSON response."""
        if value is None:
            return None
        return float(value)

    @field_serializer("experimentType")
    def serialize_experiment_type(self, value: ExperimentType) -> str:
        """Serialize ExperimentType enum to its string value."""
        return value.value

    @field_serializer("status")
    def serialize_status(self, value: JobStatus) -> str:
        """Serialize JobStatus enum to its string value."""
        return value.value
