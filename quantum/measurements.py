"""Measurement helpers for single-qubit states."""

import numpy as np


def probabilities_z(state: np.ndarray) -> dict[int, float]:
    state = np.asarray(state, dtype=complex)
    p = np.abs(state) ** 2
    return {0: float(p[0]), 1: float(p[1])}


def measure_z(state: np.ndarray, shots: int = 1, seed: int = 42) -> list[int]:
    if shots <= 0:
        raise ValueError("shots must be positive")
    p = probabilities_z(state)
    rng = np.random.default_rng(seed)
    samples = rng.choice([0, 1], size=shots, p=[p[0], p[1]])
    return samples.tolist()


def count_results(results: list[int]) -> dict[str, int]:
    return {
        "0": results.count(0),
        "1": results.count(1),
    }
