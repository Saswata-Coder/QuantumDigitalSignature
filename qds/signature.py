"""Signature construction.

This is a controlled-teleportation QDS *prototype*, not a production QDS
scheme. The signer derives one qubit state per message-digest bit using
key material and records the state description as the verification reference.
"""

from dataclasses import dataclass
import numpy as np

from .key_generation import KeyPair
from .message import message_digest
from quantum.states import state_from_bit_basis


@dataclass
class QuantumSignature:
    message: str
    digest_bits: str
    states: list[np.ndarray]
    bases: list[int]
    bits: list[int]


def sign(message: str, key: KeyPair, n_qubits: int) -> QuantumSignature:
    digest = message_digest(message, n_qubits)
    states = []
    used_bases = []
    used_bits = []

    # Quantum State Formation
    for i, digest_bit in enumerate(digest):
        # XOR makes the message-dependent state different for different key material.
        value = int(digest_bit) ^ key.bits[i]
        basis = key.bases[i]

        state = state_from_bit_basis(value, basis)

        states.append(state)
        used_bases.append(basis)
        used_bits.append(value)

    return QuantumSignature(message=message, digest_bits=digest, states=states, bases=used_bases, bits=used_bits)
