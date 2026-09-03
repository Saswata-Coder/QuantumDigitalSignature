"""End-to-end controlled-teleportation QDS prototype.

Run:
    python main.py

Install:
    pip install qiskit numpy
"""

import numpy as np

from qds.initialization import ProtocolConfig, initialize
from qds.key_generation import generate_keypair, key_fingerprint
from qds.signature import sign
from qds.teleportation import controlled_teleport
from qds.verification import verify
from qds.security import summarize_security


def main():
    config = initialize(
        ProtocolConfig(
            shots=32,
            n_qubits=8,
            seed=42,
            fidelity_threshold=0.90,
        )
    )

    message = "HELLO QDS"

    # 1. Key generation
    key = generate_keypair(config.n_qubits, seed=config.seed)
    print("Key fingerprint:", key_fingerprint(key))

    # 2. Sign message
    signature = sign(message, key, config.n_qubits)
    print("Message:", message)
    print("SHA-256 prefix:", signature.digest_bits)

    # 3. Controlled teleportation of each signature qubit
    received_states = []
    for i, secret_state in enumerate(signature.states):
        result = controlled_teleport(
            secret_state,
            shots=config.shots,
            seed=config.seed + i,
        )

        # In this simulator every corrected branch reconstructs the secret.
        # We use the first corrected state as the received representative.
        received_states.append(result.corrected_states[0])

    # 4. Verification
    verification = verify(
        signature,
        received_states,
        threshold=config.fidelity_threshold,
    )

    print("\nVerification")
    print("-------------")
    print("Accepted:", verification.accepted)
    print("Average fidelity:", round(verification.average_fidelity, 6))
    print("Minimum fidelity:", round(min(verification.per_qubit_fidelity), 6))

    # 5. Security/tamper indicator
    print("\nSecurity indicators")
    print("--------------------")
    for name, value in summarize_security(verification).items():
        print(f"{name}: {value}")

    # 6. Show one controlled-teleportation circuit
    demo = controlled_teleport(signature.states[0], shots=1, seed=config.seed)
    print("\nControlled-teleportation circuit:")
    print(demo.circuit.draw("text"))


if __name__ == "__main__":
    main()
