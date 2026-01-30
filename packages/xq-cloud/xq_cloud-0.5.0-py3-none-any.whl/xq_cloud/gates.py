import math

import qiskit.circuit.library as gates
from qiskit.circuit import Gate, Parameter, QuantumCircuit
from typing_extensions import override


class NCRXGate(Gate):
    """
    A controlled arbitrary angle x rotation gate (CRXGate) with a negated control qubit.
    """

    def __init__(self, theta: Parameter):
        super().__init__('ncrx', 2, [theta])

    @override
    def _define(self):
        qc = QuantumCircuit(2, name='ncrx_def')
        qc.x(0)
        qc.append(gates.CRXGate(self.params[0]), [0, 1])
        qc.x(0)
        self.definition = qc


class DDCRotXGate(Gate):
    """
    A controlled rotation gate implemented using a resonant dynamical decoupling sequence.
    The control qubit is the electron spin, the target qubit is a nuclear spin.
    Described in https://arxiv.org/pdf/1205.4128.pdf.

    Depending on whether the control qubit (the electron spin) starts in the state |0⟩ or |1⟩,
    the gate performs a rotation around the x-axis or the -x-axis of the Bloch sphere.
    """

    # TODO: Why is this fixed angle

    def __init__(self):
        super().__init__('ddcrotx', 2, [])

    @override
    def _define(self):
        qc = QuantumCircuit(2, name='ddcrotx_def')
        qc.cx(0, 1)
        qc.rz(math.pi / 2, 0)
        qc.rx(math.pi / 2, 1)
        self.definition = qc


class LaserResetGate(Gate):
    """
    A two-qubit reset operation used for laser-based initialization.
    """

    def __init__(self):
        super().__init__('laser_reset', 2, [])
