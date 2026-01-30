from typing import Any

import numpy as np
import qiskit.circuit.library as std_gates
from qiskit.circuit import Parameter, ParameterExpression
from qiskit.quantum_info import DensityMatrix
from qiskit.transpiler import InstructionProperties, Target

from xq_cloud.gates import DDCRotXGate, LaserResetGate, NCRXGate
from xq_cloud.schemas import (
    SerializedInstructionProperties,
    SerializedOperation,
    SerializedTarget,
)


def permute_density_matrix(dm: DensityMatrix, permutation: list[int]) -> DensityMatrix:
    """Permute qubit order of a density matrix."""
    assert dm.num_qubits == len(permutation)
    n = len(permutation)
    new_indices: list[int] = []
    for old_index in range(1 << n):
        new_index = 0
        for new_pos, old_pos in enumerate(permutation):
            bit = (old_index >> old_pos) & 1
            new_index |= bit << new_pos
        new_indices.append(new_index)
    size = len(new_indices)
    rho = dm.data
    P = np.zeros((size, size))
    for i, j in enumerate(new_indices):
        P[i, j] = 1
    return DensityMatrix(P @ rho @ P.T)


def serialize_target(target: Target) -> SerializedTarget:
    """Serialize a Qiskit Target into a structured payload."""
    operations_payload: list[SerializedOperation] = []

    # Collect operations and ensure deterministic ordering by name
    try:
        operations = list(target.operations)  # type: ignore[attr-defined]
    except Exception:
        # Fallback: derive from operation_names by scanning any op objects present
        operations = []
        for name in sorted(target.operation_names):  # type: ignore[attr-defined]
            for op in getattr(target, "operations", []):
                if getattr(op, "name", None) == name:
                    operations.append(op)
                    break

    for op in sorted(operations, key=lambda o: o.name):
        params: list[str] = []
        for p in getattr(op, "params", []):
            # Only simple Parameter symbols are supported
            if isinstance(p, Parameter):
                params.append(p.name)
            elif isinstance(p, ParameterExpression):
                # Reject complex expressions for now
                raise ValueError(f"Unsupported ParameterExpression for operation '{op.name}': {p}")
            else:
                # Non-parameter values are not serialized for the operation template
                continue

        inst_map = target[op.name]
        # Deterministic sort of qargs
        qargs_sorted = sorted(inst_map.keys())
        qargs_list: list[list[int]] = []
        props_list: list[SerializedInstructionProperties | None] = []
        for q in qargs_sorted:
            qargs_list.append([int(i) for i in q])
            prop = inst_map[q]
            if prop is None:
                props_list.append(None)
            else:
                props_list.append(
                    SerializedInstructionProperties(
                        duration=float(prop.duration) if prop.duration is not None else None,
                        error=float(prop.error) if prop.error is not None else None,
                        properties=prop.properties if getattr(prop, "properties", None) else None,
                    )
                )

        operations_payload.append(
            SerializedOperation(
                name=op.name,
                num_qubits=int(op.num_qubits),
                parameters=params,
                qargs=qargs_list,
                properties=props_list,
            )
        )

    return SerializedTarget(
        num_qubits=int(target.num_qubits),
        description=getattr(target, "description", None),
        operations=operations_payload,
    )


_GATE_FACTORIES: dict[str, Any] = {
    "rx": lambda params: std_gates.RXGate(*params),
    "ry": lambda params: std_gates.RYGate(*params),
    "rz": lambda params: std_gates.RZGate(*params),
    "sx": lambda params: std_gates.SXGate(),
    "crx": lambda params: std_gates.CRXGate(*params),
    "ncrx": lambda params: NCRXGate(*params),
    "ddcrotx": lambda params: DDCRotXGate(),
    "laser_reset": lambda params: LaserResetGate(),
}


def deserialize_target(data: SerializedTarget | dict[str, Any]) -> Target:
    """Deserialize a serialized target payload back into a Qiskit Target.

    Accepts either a previously returned ``SerializedTarget`` instance or a
    compatible ``dict`` and raises ``ValueError`` for unsupported entries.
    """
    payload = SerializedTarget.model_validate(data)

    target = Target(description=payload.description, num_qubits=int(payload.num_qubits))

    for entry in payload.operations:
        name = entry.name
        param_names = entry.parameters
        params = [Parameter(n) for n in param_names]
        factory = _GATE_FACTORIES.get(name)
        if factory is None:
            raise ValueError(f"Unsupported operation name in target payload: {name}")
        op = factory(params)

        inst_map: dict[tuple[int, ...], InstructionProperties] = {}
        for q_list, prop_payload in zip(entry.qargs, entry.properties):
            q_tuple = tuple(int(q) for q in q_list)
            if prop_payload is None:
                inst_map[q_tuple] = InstructionProperties()
            else:
                # Build kwargs only for supported fields on this environment
                ip0 = InstructionProperties()
                ip_kwargs: dict[str, Any] = {}
                if hasattr(ip0, "duration"):
                    ip_kwargs["duration"] = prop_payload.duration
                if hasattr(ip0, "error"):
                    ip_kwargs["error"] = prop_payload.error
                if hasattr(ip0, "properties"):
                    ip_kwargs["properties"] = prop_payload.properties
                inst_map[q_tuple] = InstructionProperties(**ip_kwargs)

        target.add_instruction(op, inst_map)

    return target
