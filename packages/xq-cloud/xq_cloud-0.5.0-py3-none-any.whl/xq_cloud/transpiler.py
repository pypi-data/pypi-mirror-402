import math

import qiskit.circuit.library as gates
import qiskit.transpiler.passes as passes
from qiskit.circuit import EquivalenceLibrary, Parameter, QuantumCircuit, SessionEquivalenceLibrary
from qiskit.transpiler import PassManager, Target

from xq_cloud.gates import DDCRotXGate, NCRXGate
from xq_cloud.passes import FixDDCRotXDirection


def transpile(circuits: QuantumCircuit | list[QuantumCircuit], target: Target) -> QuantumCircuit | list[QuantumCircuit]:
    equivalence_lib = EquivalenceLibrary(SessionEquivalenceLibrary)

    # Creating CRX from NCRX
    theta = Parameter('theta')
    crx_from_ncrx = QuantumCircuit(2)
    crx_from_ncrx.x(0)
    crx_from_ncrx.append(NCRXGate(theta), [0, 1])
    crx_from_ncrx.x(0)
    equivalence_lib.add_equivalence(
        gate=gates.CRXGate(theta),
        equivalent_circuit=crx_from_ncrx,
    )

    # Creating CNOT from DDCRotXGate.
    # Note: Use only RZ and SX on the target qubit to keep compatibility with
    # the XQ1 target where RX is unavailable on carbon spins.
    cnot_from_ddcrotx = QuantumCircuit(2)
    cnot_from_ddcrotx.append(DDCRotXGate(), [0, 1])
    # Control-side phase correction
    cnot_from_ddcrotx.rz(-math.pi / 2, 0)
    # Target-side: Rx(-pi/2) == Rz(pi) * Sx * Rz(-pi)
    cnot_from_ddcrotx.rz(math.pi, 1)
    cnot_from_ddcrotx.sx(1)
    cnot_from_ddcrotx.rz(-math.pi, 1)
    equivalence_lib.add_equivalence(
        gate=gates.CXGate(),
        equivalent_circuit=cnot_from_ddcrotx,
    )

    # Realize H using only RZ and SX so it can be performed on carbon spins.
    h_to_rzsx = QuantumCircuit(1)
    h_to_rzsx.rz(math.pi / 2, 0)
    h_to_rzsx.sx(0)
    h_to_rzsx.rz(math.pi / 2, 0)
    equivalence_lib.add_equivalence(
        gate=gates.HGate(),
        equivalent_circuit=h_to_rzsx,
    )

    # Provide a SWAP decomposition that uses only forward CNOTs (0 -> 1) by
    # flipping the middle reversed CNOT with H on both qubits.
    swap_forward = QuantumCircuit(2)
    swap_forward.cx(0, 1)

    # cx(1, 0) by using H on both qubits
    swap_forward.h(0)
    swap_forward.h(1)
    swap_forward.cx(0, 1)
    swap_forward.h(0)
    swap_forward.h(1)

    swap_forward.cx(0, 1)
    equivalence_lib.add_equivalence(
        gate=gates.SwapGate(),
        equivalent_circuit=swap_forward,
    )

    basis = list(target.operation_names)
    coupling_map = target.build_coupling_map()

    # Build the pass list
    pass_list = [
        passes.Unroll3qOrMore(),  # ensure no 3q+ ops remain (e.g., ccx)
        # TODO: This decomposes ALL definitions. Not sure that is what we want.
        passes.Decompose(apply_synthesis=True),  # Decompose any custom operations
        passes.TrivialLayout(coupling_map=coupling_map),
        passes.ApplyLayout(),
        passes.BasicSwap(coupling_map=coupling_map),
        passes.Optimize1qGatesDecomposition(),  # Decompose into u1, u2, u3
        passes.Optimize1qGatesSimpleCommutation(run_to_completion=True),  # Optimize 1q and 2q gate orders
        passes.Optimize1qGates(),  # Optimize 1q gates
        passes.CommutationAnalysis(),
        passes.CommutativeCancellation(),
        # Translate to the target basis
        passes.BasisTranslator(equivalence_lib, target_basis=basis, target=target),
    ]

    # Only add FixDDCRotXDirection if the target supports DDCrotXGate
    ddcrotx_gate_name = DDCRotXGate().name
    if ddcrotx_gate_name in target.operation_names:
        pass_list.append(FixDDCRotXDirection(target[ddcrotx_gate_name].keys()))

    pass_list.append(passes.Optimize1qGatesSimpleCommutation(basis=basis, target=target, run_to_completion=True))

    # See https://quantum.cloud.ibm.com/docs/en/api/qiskit/transpiler_passes
    pass_manager = PassManager(pass_list)
    return pass_manager.run(circuits)
