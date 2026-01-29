# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Pydantic schemas for device API responses.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, field_serializer

from qbraid_core.decimal import Credits

from .enums import DeviceStatus, ExperimentType


class DevicePricing(BaseModel):
    """Represents pricing information for a quantum device."""

    model_config = ConfigDict(frozen=True)

    perTask: Credits
    perShot: Credits
    perMinute: Credits

    @field_serializer("perTask", "perShot", "perMinute")
    def serialize_credits(self, value: Credits) -> float:
        """Serialize Credits objects to float for JSON response."""
        return float(value)

    def calculate_cost(
        self,
        num_tasks: int,
        num_minutes: Optional[Union[int, float]] = None,
        num_shots: Optional[int] = None,
    ) -> Credits:
        """Calculate the total cost for a job based on pricing.

        Args:
            num_tasks (int): Number of tasks to execute.
            num_minutes (int | float | None): Number of minutes the job will run
            num_shots (int | None): Number of shots the job will execute.

        Returns:
            Total cost in credits

        Raises:
            ValueError: If both num_minutes and num_shots are None,
                or if any value is negative.
        """
        if num_tasks < 0:
            raise ValueError("num_tasks must be greater than or equal to 0")

        if num_minutes is None and num_shots is None:
            raise ValueError("At least one of num_minutes or num_shots must be provided")

        if num_minutes is not None and num_minutes < 0:
            raise ValueError("num_minutes must be greater than or equal to 0")

        if num_shots is not None and num_shots < 0:
            raise ValueError("num_shots must be greater than or equal to 0")

        num_minutes = num_minutes or 0
        num_shots = num_shots or 0

        # Use Decimal arithmetic to avoid floating point precision errors
        # Convert inputs to Decimal for consistent arithmetic
        num_tasks_decimal = Decimal(str(num_tasks))
        num_shots_decimal = Decimal(str(num_shots))
        num_minutes_decimal = Decimal(str(num_minutes))

        # Credits is a subclass of Decimal, so we can do Decimal arithmetic directly
        total_cost = (
            (num_tasks_decimal * Decimal(self.perTask))
            + (num_shots_decimal * Decimal(self.perShot))
            + (num_minutes_decimal * Decimal(self.perMinute))
        )
        return Credits(total_cost)


class RuntimeDevice(BaseModel):
    """Schema for device response"""

    name: str
    qrn: str
    vendor: Literal["aws", "azure", "ibm", "ionq", "qbraid"]
    deviceType: Literal["SIMULATOR", "QPU"]
    runInputTypes: list[str]
    status: DeviceStatus
    statusMsg: Optional[str] = None
    nextAvailable: Optional[datetime] = None
    queueDepth: Optional[int] = None
    avgQueueTime: Optional[int] = None  # in minutes
    numberQubits: Optional[int] = None
    paradigm: ExperimentType
    modality: Optional[str] = None  # only applies to QPUs
    noiseModels: Optional[list[str]] = None  # only applies to simulators
    pricingModel: Optional[Literal["fixed", "dynamic"]] = None  # None if direct access is False
    pricing: Optional[DevicePricing] = None  # only applies to fixed pricing model
    directAccess: bool = True
