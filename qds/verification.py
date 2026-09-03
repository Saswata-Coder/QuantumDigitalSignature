"""Signature verification based on state fidelity."""

from dataclasses import dataclass
import numpy as np

from .signature import QuantumSignature
from quantum.states import fidelity


@dataclass
class VerificationResult:
    accepted: bool
    average_fidelity: float
    per_qubit_fidelity: list[float]
    threshold: float


def verify(signature: QuantumSignature,
           received_states: list[np.ndarray],
           threshold: float = 0.90) -> VerificationResult:
    if len(signature.states) != len(received_states):
        raise ValueError("signature and received state counts differ")

    fidelities = [
        fidelity(expected, received)
        for expected, received in zip(signature.states, received_states)
    ]

    average = float(np.mean(fidelities)) if fidelities else 0.0
    accepted = average >= threshold and all(f >= threshold for f in fidelities)

    return VerificationResult(
        accepted=accepted,
        average_fidelity=average,
        per_qubit_fidelity=fidelities,
        threshold=threshold,
    )
