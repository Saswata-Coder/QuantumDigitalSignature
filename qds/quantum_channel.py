"""Quantum-channel abstraction.

The channel here is deliberately explicit: it records whether a qubit passed
through an ideal or noisy channel. Noise is implemented as a simple
depolarizing-style state mixing operation for experimentation.
"""

from dataclasses import dataclass
import numpy as np

from quantum.states import normalize_state, density_matrix


@dataclass
class ChannelResult:
    input_state: np.ndarray
    output_state: np.ndarray
    error_probability: float


def depolarize(state: np.ndarray, p: float) -> np.ndarray:
    """Return the density matrix after simple depolarizing noise."""
    if not 0 <= p <= 1:
        raise ValueError("p must be in [0, 1]")
    psi = normalize_state(state)
    rho = density_matrix(psi)
    identity = np.eye(2, dtype=complex) / 2
    return (1 - p) * rho + p * identity


def transmit(state: np.ndarray, noise_probability: float = 0.0) -> ChannelResult:
    psi = normalize_state(state)
    output = depolarize(psi, noise_probability)
    return ChannelResult(psi, output, noise_probability)
