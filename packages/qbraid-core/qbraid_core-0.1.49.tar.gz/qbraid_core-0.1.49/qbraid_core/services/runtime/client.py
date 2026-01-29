# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module providing client for interacting with the qBraid Runtime API.

"""

from typing import Any

from qbraid_core.client import QbraidClientV1
from qbraid_core.exceptions import RequestsApiError

from .exceptions import QuantumRuntimeServiceRequestError
from .schemas.device import RuntimeDevice
from .schemas.job import JobRequest, Program, RuntimeJob
from .schemas.result import Result


class QuantumRuntimeClient(QbraidClientV1):
    """Client for interacting with the qBraid Runtime API."""

    def list_devices(self) -> list[RuntimeDevice]:
        """Returns a list of all quantum devices."""
        try:
            response = self.session.get("/devices")
            resp_data: list[dict[str, Any]] = response.json()["data"]
            return [RuntimeDevice.model_validate(d) for d in resp_data]
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(f"Failed to retrieve devices: {err}") from err

    def get_device(self, device_qrn: str) -> RuntimeDevice:
        """Returns the metadata for a specific quantum device."""
        try:
            response = self.session.get(f"/devices/{device_qrn}")
            resp_data: dict[str, Any] = response.json()["data"]
            return RuntimeDevice.model_validate(resp_data)
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(
                f"Failed to retrieve device '{device_qrn}': {err}"
            ) from err

    def create_job(self, request: JobRequest) -> RuntimeJob:
        """Submits a new quantum job."""
        try:
            response = self.session.post("/jobs", json=request.model_dump())
            resp_data: dict[str, Any] = response.json()["data"]
            return RuntimeJob.model_validate(resp_data)
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(f"Failed to create job: {err}") from err

    def get_job(self, job_qrn: str) -> RuntimeJob:
        """Returns the metadata for a specific quantum job."""
        try:
            response = self.session.get(f"/jobs/{job_qrn}")
            resp_data = response.json()["data"]
            return RuntimeJob.model_validate(resp_data)
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(
                f"Failed to retrieve job '{job_qrn}': {err}"
            ) from err

    def cancel_job(self, job_qrn: str) -> None:
        """Cancels a specific quantum job."""
        try:
            self.session.post(f"/jobs/{job_qrn}/cancel")
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(
                f"Failed to cancel job '{job_qrn}': {err}"
            ) from err

    def get_job_result(self, job_qrn: str) -> Result:
        """Returns the results for a specific quantum job."""
        try:
            response = self.session.get(f"/jobs/{job_qrn}/result")
            resp_data = response.json()["data"]
            return Result.model_validate(resp_data)
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(
                f"Failed to retrieve result for job '{job_qrn}': {err}"
            ) from err

    def get_job_program(self, job_qrn: str) -> Program:
        """Returns the program data for a specific quantum job."""
        try:
            response = self.session.get(f"/jobs/{job_qrn}/program")
            resp_data = response.json()["data"]
            return Program.model_validate(resp_data)
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(
                f"Failed to retrieve program for job '{job_qrn}': {err}"
            ) from err
