"""Classical/quantum key material for the prototype."""

from dataclasses import dataclass
import secrets
import numpy as np


@dataclass
class KeyPair:
    """Toy signing key.

    basis[i] = 0 -> computational basis
    basis[i] = 1 -> X basis
    bit[i]   -> state value inside that basis.
    """
    bits: list[int]
    bases: list[int]


def generate_keypair(n: int, seed: int | None = None) -> KeyPair:
    if n <= 0:
        raise ValueError("Signature Length must be positive")

    if seed is None:
        bits = [secrets.randbelow(2) for _ in range(n)]             # Chooses either 0 or 1
        bases = [secrets.randbelow(2) for _ in range(n)]

    else:
        rng = np.random.default_rng(seed)

        bits = rng.integers(0, 2, size=n).tolist()
        bases = rng.integers(0, 2, size=n).tolist()

    return KeyPair(bits=bits, bases=bases)


# String Representation of Fingerprint --> First 16 Bits : First 16 Bases
def key_fingerprint(key: KeyPair) -> str:
    """Short non-secret diagnostic fingerprint."""
    return "".join(map(str, key.bits[:16])) + ":" + "".join(map(str, key.bases[:16]))
