"""Custom transpiler passes for XQ Cloud."""

from __future__ import annotations

import math
from typing import Iterable

from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass

from xq_cloud.gates import DDCRotXGate


class FixDDCRotXDirection(TransformationPass):
    """Rewrite ``ddcrotx`` instructions to match target qubit orientation.

    The XQ1 target only implements :class:`DDCRotXGate` with the electron qubit
    (logical qubit 0) as the control and carbon-13 qubits (2 or 3) as targets.
    When routing generic circuits, the transpiler may temporarily introduce a
    ``ddcrotx`` with the opposite orientation (e.g. control qubit 2 targeting
    the electron). This pass replaces those instructions with an equivalent
    circuit that keeps the electron as the control qubit while reproducing the
    original unitary.
    """

    def __init__(self, allowed_qargs: Iterable[tuple[int, ...]]):
        super().__init__()
        self._allowed = {tuple(qarg) for qarg in allowed_qargs}

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        for node in dag.op_nodes(DDCRotXGate):
            qargs = node.qargs
            qubit_indices = tuple(dag.find_bit(q).index for q in qargs)

            if qubit_indices in self._allowed:
                continue

            reversed_qargs = (qubit_indices[1], qubit_indices[0])
            if reversed_qargs not in self._allowed:
                # Orientation cannot be repaired; leave for later validation.
                continue

            # Only substitute when the electron (logical 0) is present so the
            # decomposition remains valid for the target hardware.
            if qubit_indices[1] != 0 or qubit_indices[0] not in (2, 3):
                continue

            replacement_dag = circuit_to_dag(self.build_replacement_circuit())
            replacement_qubits = tuple(replacement_dag.qubits)
            wire_map = {
                replacement_qubits[0]: qargs[1],  # electron / original target
                replacement_qubits[1]: qargs[0],  # nuclear / original control
            }
            dag.substitute_node_with_dag(node, replacement_dag, wires=wire_map)
        return dag

    @staticmethod
    def build_replacement_circuit():
        """
        Return a decomposition of DDCRotXGate with reversed control and target by using only RZ, SX, and DDCRotXGate.

              ┌──────────┐
        q_e: ─┤1         ├─
              │  Ddcrotx │
        q_n: ─┤0         ├─
              └──────────┘

        is replaced with

             ┌─────────┐┌─────────┐           ┌──────────┐┌──────────┐┌──────────┐
        q_e: ┤ Rz(π/2) ├┤ Rx(π/2) ├───────────┤0         ├┤ Rx(-π/2) ├┤ Rz(-π/2) ├
             └┬────────┤└──┬────┬─┘┌─────────┐│  Ddcrotx │├─────────┬┘└──┬────┬──┘
        q_n: ─┤ Rz(-π) ├───┤ √X ├──┤ Rz(π/2) ├┤1         ├┤ Rz(π/2) ├────┤ √X ├───
              └────────┘   └────┘  └─────────┘└──────────┘└─────────┘    └────┘
        """
        qc = QuantumCircuit(2)
        electron, nuclear = 0, 1

        qc.rz(math.pi / 2, electron)
        qc.rx(math.pi / 2, electron)

        qc.rz(-math.pi, nuclear)
        qc.sx(nuclear)
        qc.rz(math.pi / 2, nuclear)

        qc.append(DDCRotXGate(), [electron, nuclear])

        qc.rx(-math.pi / 2, electron)
        qc.rz(-math.pi / 2, electron)

        qc.rz(math.pi / 2, nuclear)
        qc.sx(nuclear)

        return qc
