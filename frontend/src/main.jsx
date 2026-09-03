import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles.css';
import { QRCodeSVG } from 'qrcode.react';

const API = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';
const tabs = [
  ['dashboard','◈','Dashboard'],['entanglement','⟲','Entanglement'],['teleportation','⇢','Teleportation'],
  ['statistics','▦','Statistics'],['qds','◇','QDS Security'],['real','⌁','Real Scenario'],['summary','☰','Summary']
];
const bellStates=['Phi+','Phi-','Psi+','Psi-'];

function App(){
  const [tab,setTab]=useState('dashboard');
  const [dark,setDark]=useState(()=>localStorage.getItem('qds-theme')!=='light');
  const [apiOk,setApiOk]=useState(false);
  useEffect(()=>{document.documentElement.dataset.theme=dark?'dark':'light';localStorage.setItem('qds-theme',dark?'dark':'light')},[dark]);
  useEffect(()=>{fetch(`${API}/api/health`).then(r=>r.ok&&setApiOk(true)).catch(()=>setApiOk(false))},[]);
  return <div className="app-shell">
    <header className="site-header">
      <div className="team-strip container-fluid">
        <div className="team-logo">TEAM<br/>LOGO</div>
        <div><div className="team-name">YOUR TEAM NAME</div><div className="team-sub">Quantum Security Research &amp; Innovation Lab</div></div>
        <div className="header-actions ms-auto"><span className={`status-dot ${apiOk?'online':''}`}/><span className="small">Backend {apiOk?'online':'offline'}</span><button className="theme-btn" onClick={()=>setDark(v=>!v)}>{dark?'☀ Light':'◐ Dark'}</button></div>
      </div>
      <nav className="navbar-main container-fluid"><div className="brand-title"><span className="brand-orb">Ψ</span><span><b>Controlled Teleportation QDS</b><small>Interactive quantum signature prototype</small></span></div><div className="nav-scroll">{tabs.map(([id,icon,label])=><button key={id} className={tab===id?'active':''} onClick={()=>setTab(id)}><span>{icon}</span>{label}</button>)}</div></nav>
    </header>
    <main className="container-fluid page-wrap">
      {tab==='dashboard'&&<Dashboard onGo={setTab}/>} {tab==='entanglement'&&<Entanglement/>} {tab==='teleportation'&&<Teleportation/>}
      {tab==='statistics'&&<Statistics/>} {tab==='qds'&&<QDS/>} {tab==='real'&&<RealScenario/>} {tab==='summary'&&<Summary/>}
    </main>
    <footer className="site-footer"><div><b>Team Members</b><p>Member 1 · Member 2 · Member 3 · Member 4</p><small>Add names, roles, emails and institution details here.</small></div><div><b>Resources</b><p><a href="https://qiskit.org/" target="_blank">Qiskit</a> · <a href="https://fastapi.tiangolo.com/" target="_blank">FastAPI</a> · <a href="https://netlify.com/" target="_blank">Netlify</a></p></div></footer>
  </div>
}

function Section({eyebrow,title,children,actions}){return <section className="section-block"><div className="section-head"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1></div>{actions}</div>{children}</section>}
function Card({children,className=''}){return <div className={`glass-card ${className}`}>{children}</div>}
function Btn({children,onClick,disabled=false,variant='primary'}){return <button disabled={disabled} onClick={onClick} className={`btn-q ${variant}`}>{children}</button>}
function ApiImage({src,alt}){return src?<div className="diagram-frame"><img src={src} alt={alt}/></div>:<div className="diagram-placeholder">Run simulation to render the Matplotlib/Qiskit diagram.</div>}
function Matrix({matrix}){if(!matrix)return null; return <div className="matrix">{matrix.map((row,i)=><div key={i} className="matrix-row">{row.map((x,j)=><span key={j}>{`${Number(x.re).toFixed(3)}${x.im>=0?'+':''}${Number(x.im).toFixed(3)}i`}</span>)}</div>)}</div>}
function Metric({label,value,sub}){return <div className="metric"><small>{label}</small><strong>{value}</strong><span>{sub}</span></div>}
function Spinner(){return <span className="spinner-border spinner-border-sm"/>}

function Dashboard({onGo}){return <Section eyebrow="Research demonstrator" title="Controlled teleportation, from entanglement to verification" actions={<Btn onClick={()=>onGo('real')}>Launch 3-device lab →</Btn>}>
  <div className="hero-grid"><Card className="hero-card"><div className="hero-kicker">QUANTUM DIGITAL SIGNATURE</div><h2>See the protocol as a complete visual pipeline.</h2><p>Build Bell, GHZ or W resources; teleport a state; inspect Bob's density matrix and finite-shot statistics; then introduce defensive attack scenarios and observe the verification signal.</p><div className="hero-flow"><b>Alice</b><i>entangle</i><b>Charlie</b><i>control</i><b>Bob</b><i>verify</i><b>QDS</b></div></Card><div className="dashboard-cards">{[['entanglement','01','Entanglement','4 Bell states + GHZ + W'],['teleportation','02','Teleportation','Alice / Bob / Charlie'],['statistics','03','Statistics','Counts · ρ · fidelity · errors'],['qds','04','Security','Replay · impersonation · forgery']].map(([id,n,t,d])=><Card key={id} className="feature-card" onClick={()=>onGo(id)}><span>{n}</span><h3>{t}</h3><p>{d}</p><button onClick={()=>onGo(id)}>Open →</button></Card>)}</div></div>
  <div className="notice"><b>Important research scope:</b> this is a simulation and visualization prototype. Fidelity is computed against simulator-known reference states; it is not a proof of a production QDS security property.</div>
</Section>}

function Entanglement(){
  const [family,setFamily]=useState('bell');
  const [bell,setBell]=useState('Phi+');

  const bellImages={
    'Phi+': '/media/entanglement/bell-phi-plus.svg',
    'Phi-': '/media/entanglement/bell-phi-minus.svg',
    'Psi+': '/media/entanglement/bell-psi-plus.svg',
    'Psi-': '/media/entanglement/bell-psi-minus.svg'
  };

  const familyImages={
    ghz: '/media/entanglement/ghz.svg',
    w: '/media/entanglement/w.svg'
  };

  const prettyState=(s)=>s==='Phi+'?'|Φ⁺⟩':s==='Phi-'?'|Φ⁻⟩':s==='Psi+'?'|Ψ⁺⟩':'|Ψ⁻⟩';

  const currentImage=family==='bell'?bellImages[bell]:familyImages[family];
  const currentTitle=family==='bell'
    ? `Bell State ${prettyState(bell)}`
    : family==='ghz'?'GHZ State':'W State';

  return <Section
    eyebrow="01 · Resource preparation"
    title="Entanglement state formation"
  >
    <div className="state-family-tabs">
      {[
        ['bell','Bell States','2 qubits','Choose from 4 Bell states'],
        ['ghz','GHZ State','3 qubits','Three-qubit entangled resource'],
        ['w','W State','3 qubits','Three-qubit symmetric resource']
      ].map(([v,l,q,d])=>
        <button
          key={v}
          className={family===v?'state-family active':'state-family'}
          onClick={()=>setFamily(v)}
        >
          <strong>{l}</strong>
          <span>{q}</span>
          <small>{d}</small>
        </button>
      )}
    </div>

    {family==='bell' && (
      <Card className="bell-selector-card">
        <div className="panel-title">Choose one of the four Bell states</div>

        <div className="bell-grid large">
          {bellStates.map(s=>
            <button
              key={s}
              className={bell===s?'bell selected':'bell'}
              onClick={()=>setBell(s)}
            >
              <b>{prettyState(s)}</b>
              <small>{s}</small>
              <span>
                {s==='Phi+'?'(|00⟩ + |11⟩)/√2':
                 s==='Phi-'?'(|00⟩ − |11⟩)/√2':
                 s==='Psi+'?'(|01⟩ + |10⟩)/√2':
                 '(|01⟩ − |10⟩)/√2'}
              </span>
            </button>
          )}
        </div>
      </Card>
    )}

    <Card className="entanglement-image-card">
      <div className="panel-title">{currentTitle}</div>
      <div className="entanglement-image-frame">
        <img
          src={currentImage}
          alt={currentTitle}
          className="entanglement-image"
        />
      </div>
      <p className="image-note">
        Static visualization — no Qiskit/API rendering is used in this tab.
      </p>
    </Card>
  </Section>
}
function StateControls({family,setFamily,bell,setBell,theta,setTheta,phi,setPhi,shots,setShots,noise,setNoise}){return <Card className="controls"><label>Resource</label><select value={family} onChange={e=>setFamily(e.target.value)}><option value="bell">Bell</option><option value="ghz">GHZ</option><option value="w">W</option></select>{family==='bell'&&<><label>Bell state</label><select value={bell} onChange={e=>setBell(e.target.value)}>{bellStates.map(s=><option key={s}>{s}</option>)}</select></>}<div className="two-col"><div><label>θ (state vector)</label><input type="number" step="0.05" value={theta} onChange={e=>setTheta(Number(e.target.value))}/></div><div><label>φ (phase)</label><input type="number" step="0.05" value={phi} onChange={e=>setPhi(Number(e.target.value))}/></div></div><label>Shots <span>{shots}</span></label><input type="range" min="32" max="10000" step="32" value={shots} onChange={e=>setShots(Number(e.target.value))}/><label>Channel noise <span>{Math.round(noise*100)}%</span></label><input type="range" min="0" max="0.5" step="0.01" value={noise} onChange={e=>setNoise(Number(e.target.value))}/></Card>}

function Teleportation(){const [family,setFamily]=useState('bell'),[bell,setBell]=useState('Phi+'),[theta,setTheta]=useState(1.1),[phi,setPhi]=useState(.7),[shots,setShots]=useState(1024),[noise,setNoise]=useState(0.02),[data,setData]=useState(null),[loading,setLoading]=useState(false); async function run(){setLoading(true);try{const r=await fetch(`${API}/api/teleportation`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({family,bell_state:bell,theta,phi,shots,noise_probability:noise,seed:42})});setData(await r.json())}catch(e){alert(e.message)}finally{setLoading(false)}}return <Section eyebrow="02 · State transportation" title="Teleportation system" actions={<Btn onClick={run} disabled={loading}>{loading?<><Spinner/> Simulating…</>:'Run teleportation'}</Btn>}>
  <div className="tele-grid"><StateControls {...{family,setFamily,bell,setBell,theta,setTheta,phi,setPhi,shots,setShots,noise,setNoise}}/><div><Card className="actors-card"><Actor name="Alice" role="Input + measurement"/><div className="flow-arrow">→</div>{family!=='bell'&&<><Actor name="Charlie" role="Controller · X basis"/><div className="flow-arrow">→</div></>}<Actor name="Bob" role="Receiver + correction"/></Card><Card><div className="panel-title">Transport result</div>{data?<div className="metric-grid"><Metric label="Resource" value={data.resource}/><Metric label="Bob fidelity" value={data.fidelity.toFixed(4)} sub={data.stateDependent?'state/noise dependent':'ideal resource'} /><Metric label="Fidelity σ" value={data.fidelityStdError.toFixed(4)} sub="finite-shot estimate"/><Metric label="Error rate" value={`${(data.errorRate*100).toFixed(2)}%`} /></div>:<div className="empty-inline">Choose the resource and input state, then run.</div>}</Card></div></div>
  <Card className="diagram-card"><div className="panel-title">MPL / Matplotlib circuit</div><ApiImage src={data?.circuit} alt="Teleportation circuit"/></Card>
</Section>}

function Statistics(){const [family,setFamily]=useState('bell'),[bell,setBell]=useState('Phi+'),[theta,setTheta]=useState(1.1),[phi,setPhi]=useState(.7),[shots,setShots]=useState(2048),[noise,setNoise]=useState(.04),[data,setData]=useState(null);async function run(){const r=await fetch(`${API}/api/teleportation`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({family,bell_state:bell,theta,phi,shots,noise_probability:noise,seed:17})});setData(await r.json())}return <Section eyebrow="03 · Statistical verification" title="Bob's state, counts, fidelity and errors" actions={<Btn onClick={run}>Calculate statistics</Btn>}>
  <div className="tele-grid"><StateControls {...{family,setFamily,bell,setBell,theta,setTheta,phi,setPhi,shots,setShots,noise,setNoise}}/><div>{data?<><div className="metric-grid"><Metric label="Fidelity" value={data.fidelity.toFixed(6)} sub="F(ρBob, |ψ⟩)"/><Metric label="Standard error" value={data.fidelityStdError.toFixed(6)}/><Metric label="Shots" value={data.shots}/><Metric label="Errors" value={`${data.errors} (${(data.errorRate*100).toFixed(2)}%)`}/></div><Card className="mt-3"><div className="panel-title">Bob density matrix</div><Matrix matrix={data.bobDensityMatrix}/><div className="bloch">Bloch vector: [{data.bloch.join(', ')}]</div></Card><Card className="mt-3"><div className="panel-title">Bob measurement counts</div><div className="bars">{Object.entries(data.counts).map(([k,v])=><div className="bar-row" key={k}><span>|{k}⟩</span><div><i style={{width:`${(v/data.shots)*100}%`}}/></div><b>{v}</b></div>)}</div></Card></>:<Card className="empty-inline">Statistics appear here after a run. Try changing θ, φ, shots and noise to see why a real noisy channel does not have one constant fidelity.</Card>}</div></div>
</Section>}

function QDS(){const [message,setMessage]=useState('HELLO QUANTUM WORLD'),[n,setN]=useState(8),[shots,setShots]=useState(1024),[noise,setNoise]=useState(.01),[threshold,setThreshold]=useState(.9),[result,setResult]=useState(null),[attack,setAttack]=useState('forgery'),[attackResult,setAttackResult]=useState(null),[loading,setLoading]=useState(false);async function run(){setLoading(true);try{const r=await fetch(`${API}/api/qds/run`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,n_qubits:n,shots,seed:42,fidelity_threshold:threshold,noise_probability:noise})});setResult(await r.json())}finally{setLoading(false)}}async function runAttack(){const r=await fetch(`${API}/api/qds/attack`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({family:'ghz',theta:1.1,phi:.7,shots,noise_probability:noise,seed:42,attack,threshold})});setAttackResult(await r.json())}return <Section eyebrow="04 · Main QDS demonstrator" title="Signature verification & attack laboratory" actions={<Btn onClick={run} disabled={loading}>{loading?<><Spinner/> Running QDS…</>:'Run QDS protocol'}</Btn>}>
  <div className="qds-grid"><Card><label>Message</label><textarea rows="4" value={message} onChange={e=>setMessage(e.target.value)}/><div className="two-col"><div><label>Signature qubits</label><input type="number" min="1" max="32" value={n} onChange={e=>setN(Number(e.target.value))}/></div><div><label>Shots</label><input type="number" min="32" max="10000" value={shots} onChange={e=>setShots(Number(e.target.value))}/></div></div><label>Fidelity threshold <span>{threshold.toFixed(2)}</span></label><input type="range" min=".5" max="1" step=".01" value={threshold} onChange={e=>setThreshold(Number(e.target.value))}/><label>Channel noise <span>{Math.round(noise*100)}%</span></label><input type="range" min="0" max=".5" step=".01" value={noise} onChange={e=>setNoise(Number(e.target.value))}/></Card>{result?<div><div className="metric-grid"><Metric label="Decision" value={result.status.toUpperCase()} sub={result.verification?'all checks passed':'verification failed'}/><Metric label="Average fidelity" value={result.averageFidelity.toFixed(4)}/><Metric label="Minimum" value={result.minimumFidelity.toFixed(4)}/><Metric label="Digest" value={`${result.digest.length} bits`}/></div><Card className="mt-3"><div className="panel-title">Protocol trace</div>{result.protocol.map((s,i)=><div className="trace" key={i}><b>{i+1}</b>{s}<span>✓</span></div>)}</Card></div>:<Card className="empty-inline">Run the original QDS workflow here. This tab retains the core signature functionality from the supplied prototype.</Card>}</div>
  {result&&<><Card className="mt-4"><div className="panel-title">Per-qubit verification</div><div className="table-wrap"><table><thead><tr><th>Qubit</th><th>Digest</th><th>Basis</th><th>Expected</th><th>m₁</th><th>m₂</th><th>mᶜ</th><th>Correction</th><th>Fidelity</th></tr></thead><tbody>{result.qubits.map(q=><tr key={q.index}><td>q{q.index}</td><td>{q.digestBit}</td><td>{q.basis}</td><td>{q.expectedState}</td><td>{q.m1}</td><td>{q.m2}</td><td>{q.mc}</td><td>{q.correction}</td><td className={q.fidelity>=result.threshold?'good':'bad'}>{q.fidelity.toFixed(4)}</td></tr>)}</tbody></table></div></Card><Card className="mt-4"><div className="panel-title">Controlled-teleportation circuit · first signature qubit</div><pre className="circuit-text">{result.circuit}</pre></Card></>}
  <Card className="attack-lab"><div className="panel-title">GHZ attack laboratory</div><div className="attack-row">{['replay','impersonation','forgery'].map(a=><button className={attack===a?'selected':''} onClick={()=>setAttack(a)} key={a}>{a}</button>)}<Btn onClick={runAttack} variant="secondary">Simulate attack</Btn></div>{attackResult&&<div className="attack-result"><div className="attack-flow"><span>Alice</span><i>→</i><span>Charlie</span><i>→</i><strong>{attack}</strong><i>→</i><span>Bob</span></div><div className="metric-grid"><Metric label="Baseline fidelity" value={attackResult.baseline.fidelity.toFixed(4)}/><Metric label="Attacked fidelity" value={attackResult.attackedFidelity.toFixed(4)}/><Metric label="Drop" value={attackResult.fidelityDrop.toFixed(4)}/><Metric label="Detection" value={attackResult.detected?'TRIGGERED':'NOT TRIGGERED'}/></div><p>{attackResult.mechanism}</p><div className="two-col"><div><b>Baseline ρBob</b><Matrix matrix={attackResult.baseline.bobDensityMatrix}/></div><div><b>Attacked ρBob</b><Matrix matrix={attackResult.attackedDensityMatrix}/></div></div><ApiImage src={attackResult.baseline.circuit} alt="GHZ attack circuit"/></div>}</Card>
</Section>}

function RealScenario(){const [session,setSession]=useState(null),[role,setRole]=useState('alice'),[access,setAccess]=useState(''),[connected,setConnected]=useState(false),[deviceId,setDeviceId]=useState(''),[message,setMessage]=useState('Secure message from Alice'),[events,setEvents]=useState([]),wsRef=useRef(null);async function create(){const r=await fetch(`${API}/api/session/create`,{method:'POST'});setSession(await r.json())}function join(){if(!session)return;const wsUrl=API.replace(/^http/,'ws')+`/ws/session/${session.sessionId}`;const ws=new WebSocket(wsUrl);ws.onopen=()=>{ws.send(JSON.stringify({type:'hello',role,accessCode:access,deviceId:deviceId||undefined}))};ws.onmessage=e=>{const d=JSON.parse(e.data);if(d.type==='joined'){setConnected(true);setDeviceId(d.deviceId)}else setEvents(x=>[...x,d])};ws.onclose=()=>setConnected(false);wsRef.current=ws}function send(){wsRef.current?.send(JSON.stringify({type:'message',message,role,at:new Date().toISOString()}))}useEffect(()=>()=>wsRef.current?.close(),[]);useEffect(()=>{const qs=new URLSearchParams(window.location.search);const sid=qs.get('session');const code=qs.get('access');if(sid){fetch(`${API}/api/session/${sid}`).then(r=>r.ok?r.json():null).then(info=>{if(info){setSession({sessionId:sid,joinUrl:`/real-scenario?session=${sid}`});if(code)setAccess(code)}}).catch(()=>{})}},[]);const joinUrl=session?`${window.location.origin}${session.joinUrl}${session.accessCode?`&access=${session.accessCode}`:''}`:'';return <Section eyebrow="05 · Real-world simulation" title="Three-device entanglement laboratory" actions={!session?<Btn onClick={create}>Create shared lab session</Btn>:<span className="session-badge">Session {session.sessionId}</span>}>
  <div className="real-grid"><Card><div className="panel-title">Device login methods</div><p>Use any of these prototype connection methods:</p><div className="method"><b>① Session code</b><span>{session?.sessionId||'Create a session first'}</span></div><div className="method"><b>② Access code / device login</b><input value={access} onChange={e=>setAccess(e.target.value)} placeholder="6-character code"/></div><div className="method"><b>③ QR / phone scanner</b>{joinUrl?<QRCodeSVG value={joinUrl} size={150}/>:<div className="qr-empty">QR appears after session creation.</div>}</div>{session&&<div className="device-form"><select value={role} onChange={e=>setRole(e.target.value)}><option value="alice">Alice device</option><option value="bob">Bob device</option><option value="charlie">Charlie device</option><option value="attacker">Attacker device</option></select><Btn onClick={join}>{connected?'Connected':'Join device'}</Btn></div>}</Card><div><div className="device-cards"><Device name="Alice" role="Signer / message source" live={connected&&role==='alice'}/><Device name="Charlie" role="Controller / ideal channel" live={connected&&role==='charlie'}/><Device name="Bob" role="Receiver / verifier" live={connected&&role==='bob'}/><Device name="Attacker ×N" role="Optional simulated adversary devices" live={connected&&role==='attacker'}/></div><Card className="mt-3"><div className="panel-title">Message outflow</div><div className="network-flow"><span>Alice</span><i>quantum state</i><span>Charlie</span><i>controlled channel</i><span>Bob</span></div><textarea rows="3" value={message} onChange={e=>setMessage(e.target.value)}/><Btn onClick={send} disabled={!connected}>Send from {role}</Btn></Card><Card className="mt-3"><div className="panel-title">Live verification stream</div><div className="events">{events.length?events.map((e,i)=><div key={i}><code>{e.from}</code> {e.type} {e.message||''}</div>):<span className="muted">Connect two or more browser tabs/devices to see events.</span>}</div></Card></div></div>
  <div className="notice mt-4"><b>How this works:</b> the devices are logically linked through the server session and the quantum state is simulated. Alice, Charlie and Bob are kept as separate browser clients; attacker clients can inject simulated events. No physical quantum hardware is implied.</div>
</Section>}
function Device({name,role,live}){return <Card className="device"><div className="device-icon">{name[0]}</div><div><b>{name}</b><small>{role}</small><span className={live?'live':''}>{live?'● connected':'○ waiting'}</span></div></Card>}

function Summary(){return <Section eyebrow="06 · Theoretical showcase" title="Protocol architecture & technical flow"><div className="summary-grid"><Card className="architecture"><div className="panel-title">Architecture</div><div className="arch"><span>Message</span><i>SHA-256</i><span>Quantum signature</span><i>Entanglement</i><span>Alice</span><i>Classical outcomes</i><span>Charlie</span><i>Controlled teleportation</i><span>Bob</span><i>ρ + Fidelity</i><span>Verifier</span></div></Card><Card><div className="panel-title">Protocol idea</div><h3>Why controlled teleportation?</h3><p>Alice prepares a message-dependent quantum signature state. A shared entangled resource links Alice, Charlie and Bob. Charlie's controller result participates in Bob's correction, after which Bob compares the received state with the verification reference available in this simulation.</p><h3>Security demonstrations</h3><ul><li>Replay: stale state used against a new message context.</li><li>Impersonation: an unauthorized state is presented as Alice's.</li><li>Forgery: the received state is deliberately displaced from the expected density matrix.</li></ul></Card><Card><div className="panel-title">Suggested presentation media</div><div className="media-placeholder">Drop your team logo, architecture PNG, protocol animation or demo video into <code>frontend/public/media/</code> and reference it here.</div></Card><Card><div className="panel-title">Technical caveats</div><p><b>Fidelity:</b> ideal noiseless teleportation with a valid resource should be 1. A constant 1 in every experiment is not a bug. To obtain meaningful variation, the prototype exposes finite-shot sampling, explicit channel noise, and an intentionally experimental W-resource comparison.</p><p><b>QDS:</b> this dashboard is a research demonstrator, not a standards-compliant production signature system.</p></Card></div></Section>}

function Actor({name,role}){return <div className="actor"><div className="actor-avatar">{name[0]}</div><div><b>{name}</b><small>{role}</small></div></div>}

createRoot(document.getElementById('root')).render(<App/>);
