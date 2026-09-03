"""Single-qubit state utilities."""

import numpy as np


# Normalization of Vectors
def normalize_state(state: np.ndarray) -> np.ndarray:
    state = np.asarray(state, dtype=complex).reshape(-1)            # Reshaping finally produce matrix [a,b]

    if state.shape != (2,):
        raise ValueError("A single qubit state must have exactly 2 amplitudes")
    
    norm = np.linalg.norm(state)

    if norm == 0:
        raise ValueError("Zero vector is not a quantum state")

    return state / norm


# State Conversion for Z Basis (0 -> |0> or 1 -> |1>)
def computational_state(bit: int) -> np.ndarray:
    if bit not in (0, 1):
        raise ValueError("Bit must be 0 or 1")
    
    if bit == 0:
        return np.array([1, 0], dtype=complex)

    return np.array([0, 1], dtype=complex)


# State Conversion for X Basis (0 -> |+> or 1 -> |->)
def plus_state() -> np.ndarray:
    return np.array([1, 1], dtype=complex) / np.sqrt(2)

def minus_state() -> np.ndarray:
    return np.array([1, -1], dtype=complex) / np.sqrt(2)


# Quantum State Formation from Bits based on X or Z basis
def state_from_bit_basis(bit: int, basis: int) -> np.ndarray:
    """basis 0 = Z/computational, basis 1 = X/diagonal."""

    # Z basis
    if basis == 0:
        return computational_state(bit)

    # X basis
    if basis == 1:
        return plus_state() if bit == 0 else minus_state()
    
    raise ValueError("basis must be 0 or 1")


def density_matrix(state: np.ndarray) -> np.ndarray:
    psi = normalize_state(state)

    return np.outer(psi, np.conjugate(psi))


def fidelity(a: np.ndarray, b: np.ndarray) -> float:
    """Pure-state fidelity |<a|b>|^2."""
    a = normalize_state(a)
    
    if np.asarray(b).shape == (2,):
        b = normalize_state(b)
        return float(abs(np.vdot(a, b)) ** 2)

    rho_b = np.asarray(b, dtype=complex)
    return float(np.real(np.vdot(a, rho_b @ a)))
