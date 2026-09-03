"""Controlled teleportation using a 4-qubit statevector.

Qubit layout:
    q0 = secret state (Alice)
    q1 = Alice's GHZ qubit
    q2 = Charlie/controller
    q3 = Bob

Protocol:
1. Charlie/Alice/Bob create a GHZ state.
2. Alice performs the Bell-measurement operations on q0 and q1.
3. Charlie measures his qubit in the X basis.
4. Bob's uncorrected state is:
       X^m2 Z^(m1 XOR mc) |psi>
5. Bob can reconstruct |psi> after receiving the classical outcomes.

The branch calculation is exact (statevector simulation); shots are sampled
from the eight equally likely measurement branches.
"""

from dataclasses import dataclass
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from quantum.states import normalize_state
from quantum.gates import apply_pauli_correction


@dataclass
class TeleportationResult:
    measurement_outcomes: list[tuple[int, int, int]]
    corrected_states: list[np.ndarray]
    raw_states: list[np.ndarray]
    probabilities: list[float]
    circuit: QuantumCircuit


def _build_pre_measurement_circuit(secret_state: np.ndarray) -> QuantumCircuit:
    psi = normalize_state(secret_state)

    qc = QuantumCircuit(4)
    # Prepare |psi> on q0. Statevector initialization is only for simulation.
    qc.initialize(psi, 0)

    # GHZ over q1, q2, q3
    qc.h(1)
    qc.cx(1, 2)
    qc.cx(1, 3)

    # Alice's Bell measurement operations
    qc.cx(0, 1)
    qc.h(0)

    # Charlie measures in X basis
    qc.h(2)

    return qc


def _branch_statevector(statevector: np.ndarray, m1: int, m2: int, mc: int):
    """Extract Bob's normalized state for a measurement branch."""
    bob = np.zeros(2, dtype=complex)
    probability = 0.0

    # Qiskit basis ordering uses q3 q2 q1 q0 in the integer index.
    for b in (0, 1):
        index = (b << 3) | (mc << 2) | (m2 << 1) | m1
        amp = statevector[index]
        bob[b] = amp
        probability += abs(amp) ** 2

    if probability < 1e-14:
        return None, 0.0

    return bob / np.sqrt(probability), float(probability)


def controlled_teleport(secret_state: np.ndarray, shots: int = 256, seed: int = 42):
    if shots <= 0:
        raise ValueError("shots must be positive")

    qc = _build_pre_measurement_circuit(secret_state)
    sv = Statevector.from_instruction(qc)
    raw_sv = np.asarray(sv.data)

    branches = []
    probabilities = []

    for m1 in (0, 1):
        for m2 in (0, 1):
            for mc in (0, 1):
                raw, p = _branch_statevector(raw_sv, m1, m2, mc)
                if raw is not None:
                    branches.append((m1, m2, mc, raw))
                    probabilities.append(p)

    probabilities = np.asarray(probabilities, dtype=float)
    probabilities /= probabilities.sum()

    rng = np.random.default_rng(seed)
    selected = rng.choice(len(branches), size=shots, p=probabilities)

    outcomes = []
    raw_states = []
    corrected_states = []

    for idx in selected:
        m1, m2, mc, raw = branches[idx]
        correction = apply_pauli_correction(raw, m1, m2, mc)
        outcomes.append((m1, m2, mc))
        raw_states.append(raw)
        corrected_states.append(correction)

    return TeleportationResult(
        measurement_outcomes=outcomes,
        corrected_states=corrected_states,
        raw_states=raw_states,
        probabilities=probabilities.tolist(),
        circuit=qc,
    )
