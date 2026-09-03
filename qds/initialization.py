"""Protocol configuration and deterministic setup."""

from dataclasses import dataclass
import numpy as np


# Default Protocol Configuration (Not Constant)
@dataclass(frozen=True)
class ProtocolConfig:
    shots: int = 256                        # Repetition no for Quantum Experiments
    n_qubits: int = 16                      # Signature Length 
    seed: int = 42
    fidelity_threshold: float = 0.90


def make_rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def initialize(config: ProtocolConfig | None = None) -> ProtocolConfig:
    """Return validated protocol configuration."""
    config = config or ProtocolConfig()

    if config.shots <= 0 or config.n_qubits <= 0:
        raise ValueError("Shots and Signature Length must be positive")
    
    if not 0.0 <= config.fidelity_threshold <= 1.0:
        raise ValueError("Fidelity Threshold must be in [0, 1]")
    
    return config
