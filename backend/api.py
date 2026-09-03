from __future__ import annotations

import base64
import io
import secrets
import string
import threading
import uuid
from typing import Any, Dict, List

import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from qds.initialization import ProtocolConfig, initialize
from qds.key_generation import generate_keypair, key_fingerprint
from qds.message import message_digest
from qds.signature import sign
from qds.teleportation import controlled_teleport
from qds.verification import verify
from qds.security import summarize_security
from qds.quantum_channel import depolarize
from quantum.states import density_matrix, fidelity, normalize_state

app = FastAPI(title="Controlled-Teleportation QDS API", version="2.0.0")

# Set VITE_FRONTEND_ORIGIN in production, e.g. https://your-site.netlify.app
origins = [o.strip() for o in __import__("os").getenv("VITE_FRONTEND_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://quantum-digital-system.netlify.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BELL_STATES: dict[str, np.ndarray] = {
    "Phi+": np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2),
    "Phi-": np.array([1, 0, 0, -1], dtype=complex) / np.sqrt(2),
    "Psi+": np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2),
    "Psi-": np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2),
}
GHZ = np.array([1, 0, 0, 0, 0, 0, 0, 1], dtype=complex) / np.sqrt(2)
W = np.array([0, 1, 1, 1, 0, 0, 0, 0], dtype=complex) / np.sqrt(3)


class EntanglementRequest(BaseModel):
    family: str = Field(default="bell", pattern="^(bell|ghz|w)$")
    bell_state: str = Field(default="Phi+", pattern="^(Phi\\+|Phi-|Psi\\+|Psi-)$")


class TeleportRequest(BaseModel):
    family: str = Field(default="bell", pattern="^(bell|ghz|w)$")
    bell_state: str = Field(default="Phi+", pattern="^(Phi\\+|Phi-|Psi\\+|Psi-)$")
    theta: float = Field(default=1.1, ge=0, le=np.pi)
    phi: float = Field(default=0.7, ge=-2 * np.pi, le=2 * np.pi)
    shots: int = Field(default=1024, ge=32, le=20000)
    noise_probability: float = Field(default=0.0, ge=0, le=1)
    seed: int = Field(default=42, ge=0)


class AttackRequest(TeleportRequest):
    attack: str = Field(default="forgery", pattern="^(replay|impersonation|forgery)$")
    threshold: float = Field(default=0.90, ge=0, le=1)


class SignRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    n_qubits: int = Field(default=8, ge=1, le=32)
    shots: int = Field(default=1024, ge=32, le=10000)
    seed: int = Field(default=42, ge=0)
    fidelity_threshold: float = Field(default=0.90, ge=0.0, le=1.0)
    noise_probability: float = Field(default=0.0, ge=0.0, le=1.0)


sessions: dict[str, dict[str, Any]] = {}
session_lock = threading.Lock()


def cfloat(x: complex) -> dict[str, float]:
    return {"re": round(float(np.real(x)), 8), "im": round(float(np.imag(x)), 8)}


def matrix_json(m: np.ndarray) -> list[list[dict[str, float]]]:
    return [[cfloat(x) for x in row] for row in np.asarray(m)]


def state_json(state: np.ndarray) -> list[dict[str, float]]:
    return [cfloat(x) for x in np.asarray(state).reshape(-1)]


def state_vector(theta: float, phi: float) -> np.ndarray:
    return np.array([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)], dtype=complex)


def bloch_from_rho(rho: np.ndarray) -> list[float]:
    return [
        round(float(2 * np.real(rho[0, 1])), 6),
        round(float(2 * np.imag(rho[1, 0])), 6),
        round(float(np.real(rho[0, 0] - rho[1, 1])), 6),
    ]


def counts_from_rho(rho: np.ndarray, shots: int, seed: int) -> dict[str, int]:
    probs = np.real(np.diag(rho)).clip(0, 1)
    probs = probs / probs.sum()
    rng = np.random.default_rng(seed)
    values = rng.multinomial(shots, probs)
    return {str(i): int(v) for i, v in enumerate(values)}


def diagram_data_uri(qc: QuantumCircuit) -> str:
    """Render a self-contained SVG from Qiskit's stable text circuit drawer.

    This avoids optional mpl drawer dependencies on fresh deployment servers.
    """
    import html
    lines = [line.rstrip() for line in str(qc.draw(output="text", fold=-1)).splitlines() if line.strip()]
    width = max(760, min(1500, 18 * max((len(x) for x in lines), default=40) + 80))
    height = max(180, 34 * len(lines) + 80)
    texts = []
    for i, line in enumerate(lines):
        y = 48 + i * 32
        texts.append('<text x="28" y="{}" font-family="monospace" font-size="18" fill="#d9e7ff">{}</text>'.format(y, html.escape(line)))
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}"><rect width="100%" height="100%" rx="18" fill="#08111f"/><text x="28" y="26" font-family="Arial" font-size="13" fill="#78a9ff">QISKIT CIRCUIT / SIMULATION</text>{}</svg>'.format(width,height,width,height,''.join(texts))
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def resource_for(family: str, bell_state: str) -> tuple[np.ndarray, str]:
    if family == "bell":
        return BELL_STATES[bell_state], bell_state
    if family == "ghz":
        return GHZ, "GHZ"
    return W, "W"


def entanglement_circuit(family: str, bell_state: str = "Phi+") -> QuantumCircuit:
    if family == "bell":
        qc = QuantumCircuit(2, name=bell_state)
        if bell_state in ("Phi+", "Phi-"):
            qc.h(0)
            qc.cx(0, 1)
            if bell_state == "Phi-": qc.z(1)
        else:
            qc.h(0)
            qc.cx(0, 1)
            qc.x(1)
            if bell_state == "Psi-": qc.z(1)
        qc.barrier()
        qc.measure_all()
        return qc
    qc = QuantumCircuit(3, name=family.upper())
    if family == "ghz":
        qc.h(0); qc.cx(0, 1); qc.cx(0, 2)
    else:
        qc.prepare_state(W, [0, 1, 2])
    qc.barrier()
    qc.measure_all()
    return qc


def teleport_circuit(family: str, bell_state: str, theta: float, phi: float) -> QuantumCircuit:
    psi = state_vector(theta, phi)
    if family == "bell":
        qc = QuantumCircuit(3, 2)
        qc.initialize(psi, 0)
        resource = QuantumCircuit(2)
        if bell_state in ("Phi+", "Phi-"):
            qc.h(1); qc.cx(1, 2)
            if bell_state == "Phi-": qc.z(2)
        else:
            qc.h(1); qc.cx(1, 2); qc.x(2)
            if bell_state == "Psi-": qc.z(2)
        qc.barrier(label="Bell pair")
        qc.cx(0, 1); qc.h(0)
        qc.measure(0, 0); qc.measure(1, 1)
        qc.barrier(label="Bob correction")
        qc.x(2); qc.z(2)
        return qc
    qc = QuantumCircuit(4, 3)
    qc.initialize(psi, 0)
    if family == "ghz":
        qc.h(1); qc.cx(1, 2); qc.cx(1, 3)
    else:
        qc.prepare_state(W, [1, 2, 3])
    qc.barrier(label=f"{family.upper()} resource")
    qc.cx(0, 1); qc.h(0)
    qc.h(2)
    qc.measure(0, 0); qc.measure(1, 1); qc.measure(2, 2)
    qc.barrier(label="Bob correction")
    qc.x(3); qc.z(3)
    return qc


def branch_bob_state(raw_sv: np.ndarray, family: str, m1: int, m2: int, mc: int | None = None) -> tuple[np.ndarray | None, float]:
    # Qiskit integer ordering: highest index is leftmost bit.
    if family == "bell":
        bob = np.zeros(2, complex); p = 0.0
        for b in (0, 1):
            idx = (b << 2) | (m2 << 1) | m1
            amp = raw_sv[idx]; bob[b] = amp; p += abs(amp) ** 2
    else:
        bob = np.zeros(2, complex); p = 0.0
        for b in (0, 1):
            idx = (b << 3) | (mc << 2) | (m2 << 1) | m1
            amp = raw_sv[idx]; bob[b] = amp; p += abs(amp) ** 2
    if p < 1e-14: return None, 0.0
    return bob / np.sqrt(p), float(p)


def correct_state(raw: np.ndarray, family: str, m1: int, m2: int, mc: int | None, bell_state: str = "Phi+") -> np.ndarray:
    x = np.array([[0, 1], [1, 0]], complex); z = np.diag([1, -1]).astype(complex)
    out = raw
    if family == "bell":
        # Standard teleportation correction, plus the Pauli label of the selected Bell resource.
        if m2: out = x @ out
        if m1: out = z @ out
        if bell_state in ("Psi+", "Psi-"): out = x @ out
        if bell_state in ("Phi-", "Psi-"): out = z @ out
    else:
        if m2: out = x @ out
        if m1 ^ int(mc): out = z @ out
    return out / np.linalg.norm(out)


def generic_teleport(req: TeleportRequest) -> dict[str, Any]:
    psi = state_vector(req.theta, req.phi)
    resource, resource_label = resource_for(req.family, req.bell_state)
    qc = QuantumCircuit(3 if req.family == "bell" else 4)
    qc.initialize(psi, 0)
    qc.initialize(resource, [1, 2] if req.family == "bell" else [1, 2, 3])
    qc.barrier(label=f"{resource_label} resource")
    qc.cx(0, 1); qc.h(0)
    if req.family != "bell": qc.h(2)
    sv = np.asarray(Statevector.from_instruction(qc).data)
    branches = []
    for m1 in (0, 1):
        for m2 in (0, 1):
            for mc in ((0, 1) if req.family != "bell" else (None,)):
                raw, p = branch_bob_state(sv, req.family, m1, m2, mc)
                if raw is not None:
                    corrected = correct_state(raw, req.family, m1, m2, mc, req.bell_state)
                    branches.append((m1, m2, mc, corrected, p))
    probs = np.array([b[-1] for b in branches], float); probs /= probs.sum()
    rng = np.random.default_rng(req.seed)
    selected = rng.choice(len(branches), size=req.shots, p=probs)
    corrected_samples = [branches[i][3] for i in selected]

    # Average density matrix across sampled branches. For an ideal Bell/GHZ protocol
    # this approaches exactly |psi><psi|; W is intentionally non-deterministic.
    rho = sum(np.outer(s, np.conjugate(s)) for s in corrected_samples) / len(corrected_samples)
    if req.noise_probability:
        rho = (1 - req.noise_probability) * rho + req.noise_probability * np.eye(2) / 2
    f = float(np.real(np.vdot(psi, rho @ psi)))
    counts = counts_from_rho(rho, req.shots, req.seed + 100)
    errors = int(round(req.shots * (1 - f)))
    # Statistical standard error for an observed Bernoulli-like fidelity proxy.
    stderr = float(np.sqrt(max(f * (1 - f), 0) / max(req.shots, 1)))
    return {
        "family": req.family, "resource": resource_label, "inputState": state_json(psi),
        "theta": req.theta, "phi": req.phi, "shots": req.shots,
        "counts": counts, "errors": errors, "errorRate": round(errors / req.shots, 6),
        "bobDensityMatrix": matrix_json(rho), "bloch": bloch_from_rho(rho),
        "fidelity": round(f, 8), "fidelityStdError": round(stderr, 8),
        "idealFidelity": 1.0 if req.family in ("bell", "ghz") else None,
        "stateDependent": req.family == "w" or req.noise_probability > 0,
        "circuit": diagram_data_uri(teleport_circuit(req.family, req.bell_state, req.theta, req.phi)),
        "note": "W-state resource is a research-demonstration channel here, not a claim of deterministic standard teleportation.",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "controlled-teleportation-qds", "version": "2.0.0"}


@app.post("/api/entanglement")
def create_entanglement(req: EntanglementRequest):
    state, label = resource_for(req.family, req.bell_state)
    return {"family": req.family, "label": label, "stateVector": state_json(state), "densityMatrix": matrix_json(density_matrix(state)), "circuit": diagram_data_uri(entanglement_circuit(req.family, req.bell_state)), "qubits": 2 if req.family == "bell" else 3}


@app.post("/api/teleportation")
def teleportation(req: TeleportRequest):
    return generic_teleport(req)


@app.post("/api/qds/run")
def run_qds(request: SignRequest):
    try:
        config = initialize(ProtocolConfig(shots=request.shots, n_qubits=request.n_qubits, seed=request.seed, fidelity_threshold=request.fidelity_threshold))
        key = generate_keypair(config.n_qubits, seed=config.seed)
        signature = sign(request.message, key, config.n_qubits)
        received_states = []; qubits = []; sample_measurements = []; circuit_text = ""
        for i, secret_state in enumerate(signature.states):
            result = controlled_teleport(secret_state, shots=config.shots, seed=config.seed + i)
            raw_state = result.raw_states[0]; corrected_state = result.corrected_states[0]; outcome = result.measurement_outcomes[0]
            m1, m2, mc = map(int, outcome)
            received = depolarize(corrected_state, request.noise_probability) if request.noise_probability > 0 else corrected_state
            received_states.append(received)
            qubits.append({"index": i, "digestBit": int(signature.digest_bits[i]), "basis": "Z" if signature.bases[i] == 0 else "X", "preparedBit": int(signature.bits[i]), "expectedState": "|0⟩" if np.allclose(secret_state, [1,0]) else "|1⟩" if np.allclose(secret_state,[0,1]) else "|+⟩" if np.allclose(secret_state,[1/np.sqrt(2),1/np.sqrt(2)]) else "|-⟩" if np.allclose(secret_state,[1/np.sqrt(2),-1/np.sqrt(2)]) else "|ψ⟩", "rawState": state_json(raw_state), "correctedState": matrix_json(received) if np.asarray(received).ndim == 2 else state_json(received), "m1": m1, "m2": m2, "mc": mc, "correction": (("X" if m2 else "") + ("Z" if (m1 ^ mc) else "")) or "I"})
            if i == 0:
                sample_measurements = [{"name": "Alice m1", "value": m1}, {"name": "Alice m2", "value": m2}, {"name": "Charlie mc", "value": mc}]
                circuit_text = str(result.circuit.draw("text"))
        verification = verify(signature, received_states, threshold=config.fidelity_threshold)
        security = summarize_security(verification)
        for item, f in zip(qubits, verification.per_qubit_fidelity): item["fidelity"] = round(float(f), 8)
        return {"status": "accepted" if verification.accepted else "rejected", "message": request.message, "digest": message_digest(request.message, request.n_qubits), "keyFingerprint": key_fingerprint(key), "shots": request.shots, "nQubits": request.n_qubits, "noiseProbability": request.noise_probability, "threshold": request.fidelity_threshold, "averageFidelity": round(verification.average_fidelity, 8), "minimumFidelity": round(min(verification.per_qubit_fidelity), 8), "verification": verification.accepted, "security": security, "measurements": sample_measurements, "qubits": qubits, "circuit": circuit_text, "protocol": ["Message hashed with SHA-256", "Digest bits mapped to quantum signature states", "GHZ entanglement established among Alice, Charlie and Bob", "Alice performs Bell measurement", "Charlie measures in X basis", "Bob applies controller-dependent Pauli correction", "Verifier evaluates state fidelity"]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/qds/attack")
def qds_attack(request: AttackRequest):
    baseline = generic_teleport(request)
    psi = np.array([complex(x["re"], x["im"]) for x in baseline["inputState"]])
    rho = np.array([[complex(x["re"], x["im"]) for x in row] for row in baseline["bobDensityMatrix"]])
    # Defensive simulation: attacks alter the received state or replay an old one.
    if request.attack == "replay":
        old = state_vector(0.35, -1.2)
        attack_rho = density_matrix(old)
        mechanism = "Old signed quantum state is replayed against the current message context."
    elif request.attack == "impersonation":
        fake = state_vector(np.pi - request.theta * 0.65, request.phi + np.pi / 2)
        attack_rho = density_matrix(fake)
        mechanism = "An unauthorized sender presents a different state as Alice's transmission."
    else:
        # Forgery moves the state toward an unrelated superposition.
        fake = state_vector(np.pi / 2, -request.phi)
        attack_rho = 0.35 * rho + 0.65 * density_matrix(fake)
        mechanism = "The received state is perturbed toward a forged signature state."
    attacked_f = float(np.real(np.vdot(psi, attack_rho @ psi)))
    delta = baseline["fidelity"] - attacked_f
    return {"attack": request.attack, "mechanism": mechanism, "baseline": baseline, "attackedDensityMatrix": matrix_json(attack_rho), "attackedFidelity": round(attacked_f, 8), "fidelityDrop": round(delta, 8), "detected": attacked_f < request.threshold, "threshold": request.threshold, "outflow": ["Alice", "Charlie", request.attack.title(), "Bob"], "matrixDistance": round(float(np.linalg.norm(rho - attack_rho, ord="fro")), 8)}


def make_code(n=6):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


@app.post("/api/session/create")
def create_session():
    sid = uuid.uuid4().hex[:12]
    with session_lock:
        sessions[sid] = {"access": make_code(6), "devices": {}, "message": None}
    return {"sessionId": sid, "accessCode": sessions[sid]["access"], "joinUrl": f"/real-scenario?session={sid}"}


@app.get("/api/session/{sid}")
def session_info(sid: str):
    with session_lock:
        s = sessions.get(sid)
        if not s: raise HTTPException(status_code=404, detail="Session not found")
        return {"sessionId": sid, "devices": [{"id": k, "role": v["role"], "online": v["online"]} for k,v in s["devices"].items()], "message": s["message"]}


@app.websocket("/ws/session/{sid}")
async def websocket_session(ws: WebSocket, sid: str):
    await ws.accept()
    try:
        with session_lock:
            if sid not in sessions: await ws.close(code=4404); return
        hello = await ws.receive_json()
        if hello.get("accessCode") != sessions[sid]["access"]: await ws.close(code=4403); return
        role = hello.get("role", "observer")
        device_id = hello.get("deviceId") or uuid.uuid4().hex[:8]
        ws.state.device_id = device_id
        with session_lock:
            sessions[sid]["devices"][device_id] = {"role": role, "online": True, "ws": ws}
            peers = list(sessions[sid]["devices"].values())
        await ws.send_json({"type":"joined", "deviceId":device_id, "role":role})
        while True:
            event = await ws.receive_json()
            if event.get("type") == "message":
                with session_lock: sessions[sid]["message"] = event.get("message", "")
            payload = {"type": "session_event", "from": device_id, **event}
            with session_lock: peers = list(sessions[sid]["devices"].items())
            for pid, peer in peers:
                if pid != device_id and peer.get("online"):
                    try: await peer["ws"].send_json(payload)
                    except Exception: pass
    except WebSocketDisconnect:
        pass
    finally:
        with session_lock:
            if sid in sessions and hasattr(ws.state, "device_id"):
                sessions[sid]["devices"].pop(ws.state.device_id, None)
