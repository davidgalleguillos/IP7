// IPv7 Admin Dashboard - JavaScript
const API = 'http://localhost:8765';
const latencyData = Array(60).fill(null);
let chart = null;
let statsInterval = null;

// ---- Navigation ----
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    const section = item.dataset.section;
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    item.classList.add('active');
    document.getElementById(`section-${section}`).classList.add('active');
    document.getElementById('page-title').textContent =
      item.querySelector('.nav-label').textContent;
  });
});

// ---- Canvas Chart ----
function initChart() {
  const canvas = document.getElementById('latency-chart');
  chart = canvas.getContext('2d');
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
}

function resizeCanvas() {
  const canvas = document.getElementById('latency-chart');
  canvas.width = canvas.parentElement.clientWidth - 44;
  drawChart();
}

function drawChart() {
  const canvas = document.getElementById('latency-chart');
  const ctx = chart;
  const W = canvas.width, H = canvas.height;
  const data = latencyData.filter(v => v !== null);

  ctx.clearRect(0, 0, W, H);

  if (data.length < 2) return;

  const max = Math.max(...data, 200);
  const min = 0;
  const padT = 20, padB = 30, padL = 50, padR = 20;
  const drawW = W - padL - padR;
  const drawH = H - padT - padB;

  // Grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.05)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padT + (drawH / 4) * i;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    const val = Math.round(max - (max / 4) * i);
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.font = '10px JetBrains Mono, monospace';
    ctx.fillText(`${val}ms`, 2, y + 4);
  }

  // Area fill
  const gradient = ctx.createLinearGradient(0, padT, 0, H - padB);
  gradient.addColorStop(0, 'rgba(0,229,255,0.25)');
  gradient.addColorStop(1, 'rgba(0,229,255,0)');

  ctx.beginPath();
  data.forEach((v, i) => {
    const x = padL + (i / (data.length - 1)) * drawW;
    const y = padT + drawH - ((v - min) / (max - min)) * drawH;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.lineTo(padL + drawW, H - padB);
  ctx.lineTo(padL, H - padB);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // Line
  ctx.beginPath();
  ctx.strokeStyle = '#00e5ff';
  ctx.lineWidth = 2;
  ctx.shadowColor = '#00e5ff';
  ctx.shadowBlur = 8;
  data.forEach((v, i) => {
    const x = padL + (i / (data.length - 1)) * drawW;
    const y = padT + drawH - ((v - min) / (max - min)) * drawH;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Last dot
  const lastV = data[data.length - 1];
  const lastX = padL + drawW;
  const lastY = padT + drawH - ((lastV - min) / (max - min)) * drawH;
  ctx.beginPath();
  ctx.arc(lastX, lastY, 5, 0, Math.PI * 2);
  ctx.fillStyle = '#00e5ff';
  ctx.shadowColor = '#00e5ff';
  ctx.shadowBlur = 12;
  ctx.fill();
  ctx.shadowBlur = 0;
}

// ---- Stats Polling ----
async function fetchStats() {
  try {
    const res = await fetch(`${API}/api/stats`);
    if (!res.ok) return;
    const d = await res.json();

    document.getElementById('stat-latency').textContent   = `${d.latency_ms} ms`;
    document.getElementById('stat-bandwidth').textContent = `${d.bandwidth_mbps} Mbps`;
    document.getElementById('stat-congestion').textContent = `${Math.round(d.congestion * 100)}%`;
    document.getElementById('stat-errors').textContent    = `${(d.error_rate * 100).toFixed(2)}%`;

    document.getElementById('badge-uptime').textContent   = `⏱ ${d.uptime_s}s`;
    document.getElementById('badge-packets').textContent  = `📦 ${d.packets_sent} pkts`;
    document.getElementById('badge-blocked').textContent  = `🛡 ${d.packets_blocked} blocked`;
    document.getElementById('badge-quantum').textContent  = `⊕ ${d.quantum_channels} channels`;

    latencyData.push(d.latency_ms);
    if (latencyData.length > 60) latencyData.shift();
    drawChart();

    // Color congestion dynamically
    const cEl = document.getElementById('stat-congestion');
    cEl.className = 'stat-value ' + (d.congestion > 0.8 ? 'red' : d.congestion > 0.5 ? 'orange' : 'orange');

    // Color latency
    const lEl = document.getElementById('stat-latency');
    lEl.className = 'stat-value ' + (d.latency_ms > 100 ? 'pink' : 'cyan');

  } catch (e) {
    addLog('warn', `API unreachable — is server.py running?`);
  }
}

// ---- Activity Log ----
function addLog(type, msg) {
  const log = document.getElementById('activity-log');
  const entry = document.createElement('div');
  const now = new Date().toLocaleTimeString();
  entry.className = `log-entry ${type}`;
  entry.textContent = `${now}  ${msg}`;
  log.insertBefore(entry, log.firstChild);
  while (log.children.length > 50) log.removeChild(log.lastChild);
}

// ---- Show result ----
function showResult(id, html, cls='') {
  const el = document.getElementById(id);
  el.innerHTML = html;
  el.className = `result-box visible ${cls}`;
}

// ---- Send Packet ----
async function sendPacket() {
  const btn = document.getElementById('btn-send');
  btn.textContent = '⇄ Sending...';
  btn.disabled = true;
  try {
    const src = document.getElementById('send-source').value;
    const dst = document.getElementById('send-dest').value;
    const qos = document.getElementById('send-qos').value;
    const payload = document.getElementById('send-payload').value;

    const url = `${API}/api/send?source=${encodeURIComponent(src)}&dest=${encodeURIComponent(dst)}&qos=${qos}&payload=${encodeURIComponent(payload)}`;
    const res = await fetch(url);
    const d = await res.json();

    if (d.success) {
      showResult('send-result',
        `✓ Packet delivered successfully
From  : ${d.source}
To    : ${d.dest}
QoS   : ${d.qos}
Payload: "${d.payload}"`, 'result-ok');
      addLog('ok', `Packet sent [${d.qos}] → ${d.dest.substring(0, 20)}...`);
    } else {
      showResult('send-result', `✗ Routing failed — no path to destination.`, 'result-err');
      addLog('err', `Packet routing FAILED`);
    }
  } catch(e) {
    showResult('send-result', `✗ Error: ${e.message}`, 'result-err');
  } finally {
    btn.textContent = '⇄ Send Packet';
    btn.disabled = false;
  }
}

// ---- Route Analysis ----
async function analyzeRoute() {
  const latency   = document.getElementById('sl-latency').value;
  const bandwidth = document.getElementById('sl-bandwidth').value;
  const congestion = (document.getElementById('sl-congestion').value / 100).toFixed(2);

  const url = `${API}/api/route?latency=${latency}&bandwidth=${bandwidth}&congestion=${congestion}`;
  try {
    const res = await fetch(url);
    const d = await res.json();

    const healthColor = { good: '✓', warning: '⚠', poor: '✗', critical: '✗' };
    const recs = d.recommendations.length
      ? d.recommendations.map(r => `  • ${r}`).join('\n')
      : '  • No issues detected.';
    showResult('route-result',
      `${healthColor[d.health] || '?'} Network Health: ${d.health.toUpperCase()}
Bottleneck: ${d.bottleneck || 'None'}
Recommendations:
${recs}`,
      d.health === 'good' ? 'result-ok' : d.health === 'critical' ? 'result-err' : 'result-warn');
    addLog(d.health === 'good' ? 'ok' : 'warn', `Route analysis: ${d.health} (bottleneck: ${d.bottleneck || 'none'})`);
  } catch(e) {
    showResult('route-result', `✗ Error: ${e.message}`, 'result-err');
  }
}

// ---- Quantum ----
async function quantumOp() {
  const peer   = document.getElementById('q-peer').value;
  const action = document.getElementById('q-action').value;

  const url = `${API}/api/quantum?peer=${encodeURIComponent(peer)}&action=${action}`;
  try {
    const res = await fetch(url);
    const d = await res.json();

    if (d.success) {
      const viz = document.getElementById('entanglement-viz');
      viz.style.display = 'flex';
      showResult('quantum-result',
        `✓ ${action === 'establish' ? 'Quantum channel established' : 'Bell state entanglement created'}
Peer   : ${d.peer}
Action : ${d.action}
Status : SUCCESS`, 'result-ok');
      addLog('ok', `Quantum ${action}: ${peer}`);
    } else {
      showResult('quantum-result', `✗ Quantum operation failed (decoherence or capacity limit)`, 'result-err');
      addLog('err', `Quantum ${action} FAILED: ${peer}`);
    }
  } catch(e) {
    showResult('quantum-result', `✗ Error: ${e.message}`, 'result-err');
  }
}

// ---- Security ----
async function analyzeSecurity() {
  const payload = document.getElementById('sec-payload').value;
  const url = `${API}/api/security?payload=${encodeURIComponent(payload)}`;
  try {
    const res = await fetch(url);
    const d = await res.json();

    if (d.safe) {
      showResult('security-result',
        `✓ SAFE — Packet cleared all security filters
Payload          : "${d.payload}"
Threat Score Avg : ${d.threat_score_avg}
High-Risk Sources: ${d.high_threat_sources}
Blocked Patterns : ${d.blocked_patterns}`, 'result-ok');
      addLog('ok', `Security: SAFE — "${payload.substring(0, 30)}"`);
    } else {
      showResult('security-result',
        `⚠ BLOCKED — Threat detected!
Payload          : "${d.payload}"
Threat Score Avg : ${d.threat_score_avg}
High-Risk Sources: ${d.high_threat_sources}
Blocked Patterns : ${d.blocked_patterns}`, 'result-err');
      addLog('err', `Security: BLOCKED — "${payload.substring(0, 30)}"`);
    }
  } catch(e) {
    showResult('security-result', `✗ Error: ${e.message}`, 'result-err');
  }
}

// ---- Preset shortcut ----
function setPreset(val) {
  document.getElementById('sec-payload').value = val;
}

// ---- Routing Table ----
async function fetchRoutingTable() {
  try {
    const res = await fetch(`${API}/api/routing-table`);
    const d = await res.json();
    const tbody = document.querySelector('#routing-table tbody');
    tbody.innerHTML = '';
    
    if (d.routes.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px; color: var(--text-muted);">No routes defined in persistence. Use CLI or API to add some.</td></tr>';
      return;
    }

    d.routes.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="mono">${r.prefix.substring(0, 16)}...</td>
        <td class="mono">${r.next_hop.substring(0, 16)}...</td>
        <td class="cyan">${r.interface}</td>
        <td class="purple">${r.metric}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error('Failed to fetch routing table', e);
  }
}

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
  initChart();
  fetchStats();
  fetchRoutingTable();
  statsInterval = setInterval(fetchStats, 2000);
  setInterval(fetchRoutingTable, 5000);
  addLog('ok', 'IPv7 Dashboard initialized');
  addLog('ok', 'Connecting to API server...');
});
