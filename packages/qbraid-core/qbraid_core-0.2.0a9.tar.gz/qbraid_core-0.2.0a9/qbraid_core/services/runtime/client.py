# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module providing client for interacting with the qBraid Runtime API.

"""

import json
from typing import Any, Optional

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

    def list_jobs(
        self,
        vendor: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        status_group: Optional[str] = None,
        tags: Optional[dict[str, Any]] = None,
        search: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[RuntimeJob]:
        """Returns a list of quantum jobs matching the given filters.

        Args:
            vendor: Filter by vendor (aws, azure, ibm, ionq, qbraid, all).
            provider: Filter by provider name.
            status: Filter by individual status (INITIALIZING, QUEUED, RUNNING, etc.).
            status_group: Filter by status group (pending, returned, all).
            tags: Filter by tags (e.g., {"experiment": "bell-state"}).
            search: Text search filter.
            page: Page number for pagination.
            limit: Number of results per page.

        Returns:
            List of RuntimeJob objects matching the filters.
        """
        params: dict[str, Any] = {}
        if vendor is not None:
            params["vendor"] = vendor
        if provider is not None:
            params["provider"] = provider
        if status is not None:
            params["status"] = status
        if status_group is not None:
            params["statusGroup"] = status_group
        if tags is not None:
            params["tags"] = json.dumps(tags)
        if search is not None:
            params["search"] = search
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        try:
            response = self.session.get("/jobs", params=params if params else None)
            resp_data: list[dict[str, Any]] = response.json()["data"]
            return [RuntimeJob.model_validate(job) for job in resp_data]
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(f"Failed to retrieve jobs: {err}") from err

    def get_job_statuses(self) -> dict[str, Any]:
        """Returns job status options and available filters.

        Returns:
            Dictionary containing status options and available filter values.
        """
        try:
            response = self.session.get("/jobs/statuses")
            return response.json()["data"]
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(
                f"Failed to retrieve job statuses: {err}"
            ) from err

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

    def delete_job(self, job_qrn: str) -> None:
        """Deletes a specific quantum job.

        Args:
            job_qrn: The QRN of the job to delete.
        """
        try:
            self.session.delete(f"/jobs/{job_qrn}")
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(
                f"Failed to delete job '{job_qrn}': {err}"
            ) from err

    def delete_jobs(self, job_qrns: list[str]) -> None:
        """Deletes multiple quantum jobs.

        Args:
            job_qrns: List of job QRNs to delete.
        """
        try:
            self.session.delete("/jobs", params={"qrns": json.dumps(job_qrns)})
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(
                f"Failed to delete jobs: {err}"
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
