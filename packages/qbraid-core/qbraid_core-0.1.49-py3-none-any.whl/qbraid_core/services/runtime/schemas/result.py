# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Pydantic schemas for result data
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from qbraid_core.decimal import Credits

from .enums import JobStatus
from .job import TimeStamps


class Result(BaseModel):
    """Schema for job result"""

    status: JobStatus
    cost: Credits
    timeStamps: TimeStamps
    resultData: dict[str, Any]
