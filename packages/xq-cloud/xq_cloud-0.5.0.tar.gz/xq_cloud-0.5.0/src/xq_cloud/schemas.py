from __future__ import annotations

from typing import Any

from pydantic import BaseModel, model_validator


class SerializedInstructionProperties(BaseModel):
    """Serialized representation of optional instruction metadata."""

    duration: float | None = None
    error: float | None = None
    properties: dict[str, Any] | None = None


class SerializedOperation(BaseModel):
    """Serialized representation of a target operation entry."""

    name: str
    num_qubits: int
    parameters: list[str]
    qargs: list[list[int]]
    properties: list[SerializedInstructionProperties | None]

    @model_validator(mode="after")
    def _validate_alignment(self) -> "SerializedOperation":
        if len(self.qargs) != len(self.properties):
            raise ValueError("qargs and properties lengths must match")
        return self


class SerializedTarget(BaseModel):
    """Structured payload describing a backend's target."""

    num_qubits: int
    description: str | None = None
    operations: list[SerializedOperation]


class BackendInfo(BaseModel):
    """Public schema describing an execution backend."""

    name: str
    description: str | None = None
    target: SerializedTarget
    backend_version: str | None = None
    supports_pulse_level: bool = False
