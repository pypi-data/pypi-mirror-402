from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

import requests
from pydantic import TypeAdapter

from xq_cloud.schemas import BackendInfo


class XQCloudApiError(Exception):
    """Generic API error raised for non-success HTTP responses."""

    def __init__(self, message: str, *, status_code: int, response_body: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class XQCloudNotFoundError(XQCloudApiError):
    """Raised when a resource is not found (404)."""

    pass


@dataclass
class ResultStatus:
    """Represents the status of a job execution."""

    status: str  # "running" or "completed"
    result: Optional[Dict[str, Any]] = None  # Can contain probabilities or photoluminescence data
    error: Optional[str] = None
    shots: Optional[int] = None


class HttpSession(Protocol):
    """
    Abstraction over an HTTP session, compatible with requests.Session and FastAPI's TestClient.
    """

    def get(self, url: str, *, headers: Optional[Dict[str, str]] = None, timeout: Optional[float] = None) -> Any: ...
    def post(
        self,
        url: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Any: ...


class XQCloudClient:
    """Synchronous client for the XQ Cloud API.

    This client is designed to work with both real servers (via requests.Session)
    and FastAPI's TestClient (which subclasses requests.Session). For tests,
    pass the TestClient instance as the ``session`` parameter.
    """

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str,
        session: Optional[HttpSession] = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds

    def list_backends(self) -> List[BackendInfo]:
        """Return available backends."""
        url = f"{self.base_url}/backends"
        response = self.session.get(
            url,
            headers=self.auth_headers(),
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            self.raise_for_status(response)
        data = response.json()
        return TypeAdapter(list[BackendInfo]).validate_python(data)

    def queue_circuit(self, qasm: str, *, backend: str, shots: int | None = None, readout: str = "population") -> int:
        """Submit a job to ``backend``'s execution queue and return its job id.

        Args:
            qasm: The OpenQASM 2.0 string representation of the circuit
            backend: Name of the backend to execute on
            shots: Number of shots to execute. For simulators, this is ignored.
                For hardware backends, this controls the number of measurement shots.
            readout: Readout mode. "population" for population estimation, "pl" for photoluminescence.
        """
        url = f"{self.base_url}/queue"
        payload = {"qasm": qasm, "backend": backend, "readout": readout}
        if shots is not None:
            payload["shots"] = shots
        response = self.session.post(
            url,
            json=payload,
            headers=self.auth_headers(),
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            self.raise_for_status(response)
        body = response.json()
        return int(body["job_id"])

    def queue_program(
        self, program: dict, *, backend: str, shots: int | None = None, readout: str = "population"
    ) -> int:
        """Submit a PulseProgram job to ``backend``'s execution queue and return its job id.

        Args:
            program: The PulseProgram as a serialized dictionary
            backend: Name of the backend to execute on
            shots: Number of shots to execute. For simulators, this is ignored.
                For hardware backends, this controls the number of measurement shots.
            readout: Readout mode. "population" for population estimation, "pl" for photoluminescence.
        """
        url = f"{self.base_url}/queue"
        payload = {"program": program, "backend": backend, "readout": readout}
        if shots is not None:
            payload["shots"] = shots
        response = self.session.post(
            url,
            json=payload,
            headers=self.auth_headers(),
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            self.raise_for_status(response)
        body = response.json()
        return int(body["job_id"])

    def estimate_duration(
        self,
        *,
        program: str | dict,
        backend: str,
        shots: int | None = None,
        readout: str = "population",
    ) -> float:
        """Estimate the duration of a job execution in seconds.

        Args:
            program: The program as either a QASM string (for QuantumCircuit) or a PulseProgram dict
            backend: Name of the backend to estimate duration for
            shots: Number of shots to execute. If None, uses 1 for estimation.
            readout: Readout mode. "population" for population estimation, "pl" for photoluminescence.
                Note: Readout mode doesn't affect duration estimation.

        Returns:
            Estimated duration in seconds (float)

        Raises:
            XQCloudApiError: If the API returns an error
        """
        url = f"{self.base_url}/estimate_duration"
        payload: dict[str, Any] = {
            "program": program,
            "backend": backend,
            "readout": readout,
        }
        if shots is not None:
            payload["shots"] = shots

        response = self.session.post(
            url,
            json=payload,
            headers=self.auth_headers(),
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            self.raise_for_status(response)
        body = response.json()
        return float(body["duration_seconds"])

    def get_queue_position(self, job_id: int) -> int:
        """Get the current position in the queue for a job (0 if not queued)."""
        url = f"{self.base_url}/queue/{job_id}"
        response = self.session.get(
            url,
            headers=self.auth_headers(),
            timeout=self.timeout_seconds,
        )
        if response.status_code == 404:
            raise XQCloudNotFoundError("Job not found", status_code=404, response_body=response.text)
        if response.status_code != 200:
            self.raise_for_status(response)
        body = response.json()
        return int(body.get("position", 0))

    def get_estimated_finish_time(self, job_id: int) -> float:
        """Get the estimated finish time for a job based on its position in the queue.

        Args:
            job_id: The job ID to get estimated finish time for

        Returns:
            Estimated finish time as Unix timestamp (seconds since epoch)

        Raises:
            XQCloudNotFoundError: If the job is not found (404)
            XQCloudApiError: If the API returns an error (403, 400, etc.)
        """
        url = f"{self.base_url}/queue/{job_id}/estimated_finish_time"
        response = self.session.get(
            url,
            headers=self.auth_headers(),
            timeout=self.timeout_seconds,
        )
        if response.status_code == 404:
            raise XQCloudNotFoundError("Job not found", status_code=404, response_body=response.text)
        if response.status_code != 200:
            self.raise_for_status(response)
        body = response.json()
        return float(body["estimated_finish_time"])

    def get_result(self, job_id: int) -> ResultStatus:
        """Check the result of a job execution.

        Returns ResultStatus where ``status`` is:
        - "running" while the circuit is still executing
        - "completed" once finished, with ``result`` and optional ``error`` fields
        """
        url = f"{self.base_url}/result/{job_id}"
        response = self.session.get(
            url,
            headers=self.auth_headers(),
            timeout=self.timeout_seconds,
        )
        if response.status_code == 404:
            raise XQCloudNotFoundError("Job not found", status_code=404, response_body=response.text)
        if response.status_code == 202:
            return ResultStatus(status="running")
        if response.status_code != 200:
            self.raise_for_status(response)
        body = response.json()
        return ResultStatus(
            status="completed",
            result=body.get("result"),
            error=body.get("error"),
            shots=body.get("shots"),
        )

    def get_backend_status(self, backend_name: str) -> Dict[str, Any]:
        """Get backend status including health check and setup-specific data.

        Args:
            backend_name: Name of the backend to get status for

        Returns:
            Dictionary with keys:
            - "healthy": bool - Health check status
            - "setup_data": dict - Free-form dictionary containing setup-specific data
                For mobile setup, contains "parameters" and "amplitudes" keys with
                characterization state (quantities converted to SI base units as floats)

        Raises:
            XQCloudNotFoundError: If backend not found (404)
            XQCloudApiError: If the API returns an error
        """
        url = f"{self.base_url}/backends/{backend_name}/status"
        response = self.session.get(
            url,
            headers=self.auth_headers(),
            timeout=self.timeout_seconds,
        )
        if response.status_code == 404:
            raise XQCloudNotFoundError("Backend not found", status_code=404, response_body=response.text)
        if response.status_code != 200:
            self.raise_for_status(response)
        return response.json()

    def wait_for_result(
        self,
        job_id: int,
        *,
        poll_interval_seconds: float = 0.1,
        timeout_seconds: float = 30.0,
        readout: str = "population",
    ) -> Dict[str, float]:
        """Poll until the job is completed or timeout is reached.

        Raises TimeoutError if the timeout elapses before completion.
        Raises XQCloudApiError if the API returns a non-success status.
        Raises XQCloudApiError if the job finished with an error.
        Returns the result probabilities dictionary on success.
        """
        start = time.monotonic()
        # Track consecutive checks where result is None/empty to detect race conditions
        consecutive_empty_checks = 0
        max_empty_checks = 10  # Wait up to 10 consecutive empty checks before giving up

        while True:
            status = self.get_result(job_id)
            if status.status == "completed":
                if status.error:
                    raise XQCloudApiError(
                        f"Job {job_id} failed: {status.error}", status_code=200, response_body=status.error
                    )
                # If result is None or empty, the job may have just completed but result data isn't ready yet
                # Wait a bit more to avoid race conditions
                if status.result is None or not status.result:
                    consecutive_empty_checks += 1
                    if consecutive_empty_checks >= max_empty_checks:
                        if time.monotonic() - start > timeout_seconds:
                            raise XQCloudApiError(
                                f"Job {job_id} completed but result data is not available after {max_empty_checks} checks",
                                status_code=200,
                                response_body="Result data not available",
                            )
                        # Reset counter if we haven't hit timeout yet, keep waiting
                        consecutive_empty_checks = 0
                    time.sleep(poll_interval_seconds)
                    continue

                # Validate that the result contains the expected data structure
                # For PL readout, check for "photoluminescence" key with non-None value
                # For population readout, check that it's a non-empty dict
                if readout == "pl":
                    if "photoluminescence" not in status.result or status.result.get("photoluminescence") is None:
                        consecutive_empty_checks += 1
                        if consecutive_empty_checks >= max_empty_checks:
                            if time.monotonic() - start > timeout_seconds:
                                raise XQCloudApiError(
                                    f"Job {job_id} completed but photoluminescence data is not available",
                                    status_code=200,
                                    response_body="Photoluminescence data not available",
                                )
                            consecutive_empty_checks = 0
                        time.sleep(poll_interval_seconds)
                        continue
                else:
                    # For population readout, ensure we have expectation values
                    if not isinstance(status.result, dict) or len(status.result) == 0:
                        consecutive_empty_checks += 1
                        if consecutive_empty_checks >= max_empty_checks:
                            if time.monotonic() - start > timeout_seconds:
                                raise XQCloudApiError(
                                    f"Job {job_id} completed but expectation values are not available",
                                    status_code=200,
                                    response_body="Expectation values not available",
                                )
                            consecutive_empty_checks = 0
                        time.sleep(poll_interval_seconds)
                        continue

                # Result is available and contains expected data
                consecutive_empty_checks = 0  # Reset on success
                return status.result

            # Job is still running
            consecutive_empty_checks = 0  # Reset counter when job is not completed
            if time.monotonic() - start > timeout_seconds:
                raise TimeoutError(f"Timed out waiting for result of job {job_id}")
            time.sleep(poll_interval_seconds)

    def auth_headers(self) -> Dict[str, str]:
        return {"x-key": self.api_key}

    def raise_for_status(self, response: requests.Response) -> None:
        try:
            response_data = response.json()
            # FastAPI returns errors in the format {"detail": "error message"}
            if isinstance(response_data, dict) and "detail" in response_data:
                error_message = response_data["detail"]
            else:
                error_message = (
                    f"HTTP {response.status_code} error for {response.request.method} {response.request.url}"
                )
            response_body = response_data
        except Exception:
            error_message = f"HTTP {response.status_code} error for {response.request.method} {response.request.url}"
            response_body = response.text
        raise XQCloudApiError(
            error_message,
            status_code=response.status_code,
            response_body=response_body,
        )
