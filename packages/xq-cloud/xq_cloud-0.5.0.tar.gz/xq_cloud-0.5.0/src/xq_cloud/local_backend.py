from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from qiskit.circuit import QuantumCircuit
from qiskit.providers import BackendV2 as Backend
from qiskit.providers import JobV1 as Job
from qiskit.providers import Options
from qiskit.providers.jobstatus import JobStatus
from qiskit.quantum_info import Statevector
from qiskit.result import Result
from qiskit.result.models import ExperimentResultData
from qiskit.result.result import ExperimentResult
from qiskit.transpiler import Target
from typing_extensions import override
from xq_pulse.pulse.program import PulseProgram

from xq_cloud.backend import XQCloudBackend


class XQLocalJob(Job):
    """In-memory job that requires explicit submission like the cloud job."""

    _backend: XQLocalBackend
    _result: Result | None
    _job_id: str | None
    _circuit: QuantumCircuit
    shots: int
    readout: str

    def __init__(self, backend: XQLocalBackend, *, shots: int, readout: str, circuit: QuantumCircuit):
        super().__init__(backend, job_id="")
        self._backend = backend
        self.shots = shots
        self.readout = readout
        self._circuit = circuit
        self._result = None
        self._job_id = None

    def _build_result(self, circuit: QuantumCircuit) -> Result:
        if self.readout == "pl":
            # Photoluminescence is not supported locally; validated earlier.
            raise ValueError("Photoluminescence readout is not supported by the local backend.")

        state = Statevector.from_instruction(circuit)
        probabilities_dict: dict[str, float] = cast(dict[str, float], state.probabilities_dict())
        probabilities: dict[str, float] = {
            str(bitstring): float(prob) for bitstring, prob in probabilities_dict.items()
        }

        shots_used = self.shots if self.shots > 0 else 1
        data = ExperimentResultData(expectation_values=probabilities)

        return Result(
            backend_name=self._backend.name,
            backend_version=self._backend.backend_version,
            job_id=self._job_id,
            success=True,
            results=[
                ExperimentResult(
                    shots=shots_used,
                    success=True,
                    data=data,
                    status=JobStatus.DONE,
                )
            ],
        )

    @override
    def submit(self) -> None:
        """Submit the local job; mirrors cloud job semantics."""
        if self._job_id is not None:
            raise RuntimeError("Job has already been submitted.")

        self._job_id = f"local-{uuid4()}"
        self._result = self._build_result(self._circuit)

    @override
    def result(self, timeout_seconds: float | None = None):
        if self._job_id is None or self._result is None:
            raise RuntimeError("Job has not been submitted yet. Call submit() before requesting results.")
        return self._result

    @override
    def cancel(self) -> None:
        raise NotImplementedError("Cancellation is not supported for local jobs.")

    @override
    def status(self) -> JobStatus:
        if self._job_id is None:
            return JobStatus.INITIALIZING
        return JobStatus.DONE

    @property
    def duration(self) -> float:
        return 0.0


class XQLocalBackend(Backend):
    """Local, Aer-backed backend mirroring the XQCloudBackend interface."""

    # Reuse the compatibility checks from the remote backend
    assert_compatible = staticmethod(XQCloudBackend.assert_compatible)

    def __init__(
        self,
        *,
        target: Target,
        name: str = "xq-local",
        description: str = "Local simulator backend",
        backend_version: str = "0.0.0",
        supports_pulse_level: bool = False,
    ) -> None:
        super().__init__(
            provider=None,
            name=name,
            description=description,
            backend_version=backend_version,
        )
        self._target = target
        self._options = self._default_options()
        self.supports_pulse_level = supports_pulse_level

    @property
    @override
    def target(self) -> Target:  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        return self._target

    @property
    @override
    def options(self) -> Options:  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        return self._options

    @property
    @override
    def max_circuits(self) -> int | None:  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        return 1

    @override
    def run(
        self,
        run_input: QuantumCircuit | PulseProgram | list[QuantumCircuit | PulseProgram],
        **options: Any,
    ) -> Any:  # type: ignore[override]
        if isinstance(run_input, list):
            assert len(run_input) == 1, f"Only single-circuit jobs are supported by the {self.name} backend"
            program = run_input[0]
        else:
            program = run_input

        if isinstance(program, PulseProgram):
            if self.supports_pulse_level:
                raise NotImplementedError("Local pulse-level simulation is not implemented.")
            raise ValueError(f"Backend {self.name} does not support PulseProgram submission.")

        self.assert_compatible(program, self.target)

        shots = options.get("shots", None)
        readout = options.get("readout", "population")

        if readout not in ("population", "pl"):
            raise ValueError(f'Invalid readout mode "{readout}". Must be "population" or "pl".')
        if readout == "pl":
            raise ValueError("Photoluminescence readout is not supported by the local backend.")

        return XQLocalJob(
            backend=self,
            shots=shots if shots is not None else -1,
            readout=readout,
            circuit=program,
        )

    @classmethod
    @override
    def _default_options(cls) -> Options:  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        return Options()

    def status(self) -> dict[str, object]:
        return {"healthy": True, "setup_data": {}}

    @override
    def __repr__(self) -> str:
        return f"XQLocalBackend(name={self.name}, description={self.description})"
