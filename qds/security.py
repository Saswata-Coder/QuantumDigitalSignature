"""Security/attack metrics for experiments.

These are experimental indicators, NOT a proof of QDS security.
"""


def forgery_score(verification_result) -> float:
    """Lower is better for a forger; based on observed average fidelity."""
    return float(verification_result.average_fidelity)


def tamper_detected(verification_result, threshold: float) -> bool:
    return verification_result.average_fidelity < threshold


def summarize_security(verification_result) -> dict:
    return {
        "accepted": verification_result.accepted,
        "average_fidelity": verification_result.average_fidelity,
        "min_fidelity": min(verification_result.per_qubit_fidelity)
        if verification_result.per_qubit_fidelity else 0.0,
        "tamper_indicator": not verification_result.accepted,
    }
