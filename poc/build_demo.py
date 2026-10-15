#!/usr/bin/env python3
"""Generate the static board demo (demo/index.html) from demo_data.json.

GitHub Pages is static, so the hosted demo simulates the access-control model in
the browser. The same authorization map and denial semantics are enforced for
real by poc/access.py (SQLite) and port directly to Snowflake row access
policies. Run after seed.py:  python3 poc/build_demo.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "demo" / "demo_data.json"
OUT = ROOT / "demo" / "index.html"

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Interactive access-control demo · Snow Compliance Demo</title>
<link rel="stylesheet" href="../assets/style.css">
<style>
  .demo-wrap { max-width: 1000px; margin: 0 auto; padding: 28px 24px 64px; }
  .sim-banner { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; border-radius: 12px; padding: 12px 16px; font-size: 14px; margin-bottom: 20px; }
  .user-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px,1fr)); gap: 12px; margin: 16px 0; }
  .user-card { text-align: left; background: #fff; border: 1px solid #e3e8ef; border-radius: 12px; padding: 14px 16px; cursor: pointer; box-shadow: var(--shadow); }
  .user-card:hover { border-color: #0d9488; }
  .user-card strong { display: block; }
  .user-card span { font-size: 13px; color: #52627a; }
  .pill-role { display:inline-block; font-size:11px; font-weight:700; padding:2px 8px; border-radius:999px; background:#eef2f7; color:#52627a; margin-top:6px; }
  .panel { background:#fff; border:1px solid #e3e8ef; border-radius:12px; padding:20px; box-shadow: var(--shadow); margin-bottom:16px; }
  .doc-link { color:#0f766e; font-weight:600; cursor:pointer; background:none; border:none; padding:0; font:inherit; text-align:left; }
  .doc-link:hover { text-decoration:underline; }
  .denied { color:#dc2626; font-weight:700; }
  .allowed { color:#047857; font-weight:700; }
  .clause { border-left:3px solid #0d9488; padding:4px 0 4px 10px; margin:6px 0; font-size:14px; }
  .clause .snip { color:#52627a; display:block; }
  .row { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
  .btn { background:#0d9488; color:#fff; border:none; border-radius:8px; padding:9px 14px; font:inherit; font-weight:600; cursor:pointer; }
  .btn.ghost { background:#334155; }
  select { font:inherit; padding:8px 10px; border-radius:8px; border:1px solid #cbd5e1; }
  .flash { margin-top:12px; padding:10px 12px; border-radius:8px; }
  .flash.denied { background:#fef2f2; border:1px solid #fecaca; }
  .flash.allowed { background:#ecfdf5; border:1px solid #a7f3d0; }
</style>
</head>
<body>
<header class="topbar"><div class="inner">
  <a class="brand" href="../index.html"><span class="mark" aria-hidden="true">SC</span>
    <span>Snow Compliance Demo<small>Interactive POC &middot; board review</small></span></a>
  <nav class="nav" aria-label="Primary"><a href="../index.html">Overview</a><a href="../data-foundation.html">Data foundation</a><a href="../security.html">Confidentiality</a><a class="active" href="index.html">Interactive demo</a><a href="../roadmap.html">Roadmap</a></nav>
</div></header>

<main class="demo-wrap">
  <div class="sim-banner">
    <strong>Simulated security.</strong> This hosted page simulates the access model in the
    browser so the board can click through it. The same authorization map and denial rules are
    enforced for real by the SQLite POC (<code>poc/access.py</code>, <code>poc/server.py</code>)
    and port directly to Snowflake row access policies.
  </div>
  <div id="app"></div>
</main>
<script>window.DEMO_DATA = __DEMO_DATA__;</script>
<script>
const D = window.DEMO_DATA;
const OVERSIGHT = ['compliance_admin', 'auditor'];
const app = document.getElementById('app');
let current = null;
let audit = D.seed_audit.slice();

function nowISO() { return new Date().toISOString().replace(/\.\d+Z$/, 'Z'); }
function logEvent(user, action, target, outcome) {
  audit.push({ at: nowISO(), user: user.username, role: user.role, action, target: target || null, outcome });
}
function docsFor(user) {
  if (OVERSIGHT.includes(user.role)) return D.documents.slice();
  const allowed = D.authorizations[user.username] || [];
  return D.documents.filter(d => allowed.includes(d.matter_id));
}
function esc(s) { return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

function renderLogin() {
  current = null;
  app.innerHTML = `<div class="panel">
    <h2>Sign in as a hypothetical user</h2>
    <p class="lead">Each person is authorized only for specific matters. Pick one to see what the wall does.</p>
    <div class="user-grid">
      ${D.users.map(u => `<button class="user-card" data-u="${esc(u.username)}">
        <strong>${esc(u.name)}</strong><span>${esc(u.practice || '')}</span>
        <div class="pill-role">${esc(u.role)} &middot; ${esc(u.username)}</div></button>`).join('')}
    </div>
    <p class="muted" style="font-size:13px">Password is simulated as <code>demo</code> for every user.</p>
  </div>`;
  app.querySelectorAll('button[data-u]').forEach(b => b.onclick = () => {
    current = D.users.find(u => u.username === b.dataset.u);
    logEvent(current, 'login', null, 'allowed');
    renderDashboard();
  });
}

function renderDashboard() {
  const user = current;
  const auditTab = OVERSIGHT.includes(user.role)
    ? `<button class="btn ghost" id="tab-audit">View audit log</button>` : '';
  app.innerHTML = `
    <div class="panel"><div class="row">
      <strong>${esc(user.name)}</strong>
      <span class="pill-role">${esc(user.role)}</span>
      <span style="margin-left:auto">${auditTab}<button class="btn" id="out">Sign out</button></span>
    </div></div>
    <div id="body"></div>`;
  document.getElementById('out').onclick = renderLogin;
  if (document.getElementById('tab-audit')) document.getElementById('tab-audit').onclick = renderAudit;
  if (OVERSIGHT.includes(user.role)) renderAudit(); else renderDocs();
}

function renderDocs() {
  const user = current;
  const mine = docsFor(user);
  const allMine = new Set(mine.map(d => d.contract_id));
  const restricted = D.documents.filter(d => !allMine.has(d.contract_id));
  document.getElementById('body').innerHTML = `
    <div class="panel"><h3>Your documents (${mine.length})</h3>
      <div class="table-scroll"><table><thead><tr><th>Document</th><th>Type</th><th>Matter</th><th>Confidentiality</th><th>Risk</th></tr></thead>
      <tbody>${mine.map(d => `<tr><td><button class="doc-link" data-id="${esc(d.contract_id)}">${esc(d.title.slice(0,58))}${d.title.length>58?'…':''}</button></td>
        <td>${esc(d.contract_type)}</td><td>${esc(d.matter_name)}</td><td>${esc(d.confidentiality)}</td>
        <td><span class="badge ${d.risk_band.toLowerCase()}">${esc(d.risk_band)}</span></td></tr>`).join('') || '<tr><td colspan=5>No documents</td></tr>'}
      </tbody></table></div>
    </div>
    <div id="detail"></div>
    <div class="panel"><h3>Attempt to open a restricted document</h3>
      <p class="muted">These belong to matters you are not authorized for. The request is denied and recorded.</p>
      <div class="row"><select id="restricted">
        ${restricted.map(d => `<option value="${esc(d.contract_id)}">${esc(d.matter_name)} — ${esc(d.title.slice(0,44))}</option>`).join('') || '<option value="">(none — you can see everything)</option>'}
      </select><button class="btn" id="try">Request access</button></div>
      <div id="flash"></div>
    </div>`;
  document.querySelectorAll('button[data-id]').forEach(b => b.onclick = () => openDoc(b.dataset.id));
  const tryBtn = document.getElementById('try');
  if (tryBtn) tryBtn.onclick = () => {
    const id = document.getElementById('restricted').value; if (!id) return;
    const target = D.documents.find(d => d.contract_id === id);
    logEvent(user, 'view_document', id, 'denied');
    document.getElementById('flash').innerHTML =
      `<div class="flash denied"><span class="denied">DENIED</span> — not authorized for <strong>${esc(target.matter_name)}</strong>. Recorded in the audit log.</div>`;
  };
}

function openDoc(id) {
  const user = current;
  const d = D.documents.find(x => x.contract_id === id);
  const allowed = OVERSIGHT.includes(user.role) || (D.authorizations[user.username] || []).includes(d.matter_id);
  if (!allowed) {
    logEvent(user, 'view_document', id, 'denied');
    document.getElementById('detail').innerHTML = `<div class="panel"><span class="denied">DENIED</span> — not authorized for this matter.</div>`;
    return;
  }
  logEvent(user, 'view_document', id, 'allowed');
  document.getElementById('detail').innerHTML = `<div class="panel">
    <h3>${esc(d.title)}</h3>
    <p class="muted">${esc(d.client_name)} &middot; ${esc(d.matter_name)} &middot; ${esc(d.confidentiality)}</p>
    <p>Risk: <span class="badge ${d.risk_band.toLowerCase()}">${esc(d.risk_band)} (${d.risk_score})</span>
       &middot; drivers: ${d.risk_drivers.map(esc).join(', ') || '—'}</p>
    <h4>Clause categories present (${d.present_categories.length} of 41)</h4>
    ${d.present_categories.slice(0, 18).map(c => `<div class="clause">${esc(c)}</div>`).join('')}
    ${d.present_categories.length > 18 ? `<p class="muted">+ ${d.present_categories.length-18} more</p>` : ''}
  </div>`;
}

function renderAudit() {
  const rows = audit.slice().reverse();
  document.getElementById('body').innerHTML = `<div class="panel">
    <h3>Audit log — who accessed which files</h3>
    <p class="muted">Pre-seeded example events plus this session's simulated activity.</p>
    <div class="table-scroll"><table><thead><tr><th>When</th><th>User</th><th>Role</th><th>Action</th><th>Target</th><th>Outcome</th></tr></thead>
    <tbody>${rows.map(a => `<tr><td>${esc(a.at)}</td><td>${esc(a.user)}</td><td>${esc(a.role)}</td><td>${esc(a.action)}</td><td>${esc(a.target||'')}</td><td class="${a.outcome}">${esc(a.outcome)}</td></tr>`).join('')}
    </tbody></table></div></div>`;
}

renderLogin();
</script>
</body>
</html>
"""


def main() -> None:
    data = json.loads(DATA.read_text())
    html = TEMPLATE.replace("__DEMO_DATA__", json.dumps(data))
    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
