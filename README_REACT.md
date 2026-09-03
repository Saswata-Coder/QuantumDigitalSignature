# Controlled-Teleportation QDS Interactive Prototype — v2

A React/Vite + FastAPI research demonstrator built on the supplied controlled-teleportation QDS prototype.

## Tabs / features

1. **Dashboard** — project overview and quick navigation.
2. **Entanglement** — four Bell states, GHZ and W resources; Qiskit circuits rendered through Matplotlib and returned as SVG images.
3. **Teleportation** — Bell teleportation with Alice/Bob; GHZ/W controlled demonstrations with Alice/Charlie/Bob; configurable input state `(theta, phi)`, shots and noise.
4. **Statistics** — Bob density matrix, Bloch vector, finite-shot counts, estimated errors and fidelity with standard error.
5. **QDS Security** — preserves the original message → digest → signature → controlled teleportation → verification workflow and adds replay, impersonation and forgery attack demonstrations using GHZ resources and matrix/fidelity deltas.
6. **Real Scenario** — shared browser/device session using session code, device login/access code and QR join link. Multiple Alice/Bob/Charlie/attacker clients can join the same simulated lab over WebSockets.
7. **Summary** — theoretical architecture, technical flow, security caveats and media placeholders.

## Important fidelity design choice

A noiseless, valid quantum teleportation protocol should ideally reproduce the input state, so fidelity is expected to be ~1. A constant 1 is therefore not itself an implementation error. This version makes fidelity informative by exposing:

- finite-shot sampling;
- explicit depolarizing channel noise;
- state-dependent input parameters `theta` and `phi`;
- an experimental W-resource comparison, where the resource is **not claimed to provide deterministic standard teleportation**;
- replay / impersonation / forgery state substitutions and density-matrix distance.

This avoids artificially changing an ideal Bell/GHZ fidelity just to make the chart look different.

## Local run

### Backend

From the project root:

```powershell
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn backend.api:app --reload --port 8000
```

### Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.

If the backend is elsewhere:

```powershell
$env:VITE_API_BASE="https://YOUR-BACKEND.onrender.com"
npm run dev
```

## Deployment architecture

```text
                 Netlify
          React + Vite frontend
                  |
          HTTPS REST / WebSocket
                  |
                 Render
          FastAPI + Qiskit backend
                  |
       Qiskit + NumPy + Matplotlib
                  |
        Quantum-state simulation
```

### Deploy backend

Push this project to GitHub. Create a Render **Web Service** using the repository.

Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
uvicorn backend.api:app --host 0.0.0.0 --port $PORT
```

Set this environment variable on Render after you know the Netlify URL:

```text
VITE_FRONTEND_ORIGIN=https://YOUR-SITE.netlify.app
```

### Deploy frontend to Netlify

For a repository containing this project at its root, the included `netlify.toml` uses:

```text
Build command: cd frontend && npm install && npm run build
Publish directory: frontend/dist
```

Set Netlify environment variable:

```text
VITE_API_BASE=https://YOUR-BACKEND.onrender.com
```

Redeploy after changing environment variables.

## Production notes

- The WebSocket session store is intentionally in-memory for a hackathon/demo deployment. Restarting the backend clears active sessions.
- For a multi-instance production service, use a shared state/pub-sub layer (for example Redis) instead of the in-memory `sessions` dictionary.
- QR access currently carries the demo session/access information. For a real deployment, use short-lived signed join tokens and authentication rather than treating a QR code as a permanent credential.
- Do not describe the prototype as a production-secure QDS implementation. The attack lab demonstrates verification behavior inside a simulator.
- The frontend is static and can be served by Netlify; Python/Qiskit must remain on a backend/server because the browser does not run this Python stack directly.
