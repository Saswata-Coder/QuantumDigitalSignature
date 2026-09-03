"""Pauli and protocol gate helpers."""

import numpy as np

# X (Bit-Flip) Gate
X = np.array([[0, 1], [1, 0]], dtype=complex)
# Y Gate
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
# Z (Phase-Flip) Gate
Z = np.array([[1, 0], [0, -1]], dtype=complex)


# Pauli Correction
def apply_pauli_correction(state: np.ndarray, m1: int, m2: int, mc: int) -> np.ndarray:
    """Undo X^m2 Z^(m1 XOR mc) from a controlled-teleportation branch."""
    out = np.asarray(state, dtype=complex)

    # X Gate Applied 
    if m2:
        out = X @ out

    # Z Gate Applied
    if m1 ^ mc:
        out = Z @ out

    norm = np.linalg.norm(out)
    return out / norm


def correction_label(m1: int, m2: int, mc: int) -> str:
    labels = []

    if m2:
        labels.append("X")

    if m1 ^ mc:
        labels.append("Z")

    if not labels:
        return "I"

    return "".join(labels)
