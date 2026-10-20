#!/usr/bin/env python3
"""Generate the static board-review site for the Snowflake compliance demo.

No build tooling runs on GitHub Pages (legacy source = main:/), so this script
emits plain, self-contained HTML. Run:  python3 build_site.py
"""
import html
import pathlib

ROOT = pathlib.Path(__file__).parent

NAV = [
    ("index.html", "Overview"),
    ("data-foundation.html", "Data foundation"),
    ("architecture.html", "Architecture"),
    ("security.html", "Confidentiality"),
    ("identity-verification.html", "Verified login"),
    ("support-agent.html", "Support agent"),
    ("risk-analysis.html", "Risk analysis"),
    ("audit-verification.html", "Audit"),
    ("poc.html", "POC & findings"),
    ("demo/index.html", "Interactive demo"),
    ("snowflake-options.html", "Snowflake options"),
    ("roadmap.html", "Roadmap"),
    ("full-dataset.html", "Full-dataset plan"),
]

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Snow Compliance Demo</title>
<meta name="description" content="Board-review recommendations for a Snowflake legal-compliance demonstration built on the public CUAD dataset plus synthetic law-firm records.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar">
  <div class="inner">
    <a class="brand" href="index.html">
      <span class="mark" aria-hidden="true">SC</span>
      <span>Snow Compliance Demo<small>Board review &middot; v1</small></span>
    </a>
    <nav class="nav" aria-label="Primary">{nav}</nav>
  </div>
</header>
{body}
<footer class="footer">
  <div class="wrap">
    <div>
      <strong>Snow Compliance Demo</strong> &mdash; internal staging for board review.<br>
      Built on the public <a href="https://github.com/The-Atticus-Project/cuad">CUAD</a> dataset (CC&nbsp;BY&nbsp;4.0) plus synthetic records.
    </div>
    <div>Prepared by the CEO office &middot; For discussion only &mdash; not legal advice.</div>
  </div>
</footer>
</body>
</html>
"""


def nav_html(active):
    out = []
    for href, label in NAV:
        cls = ' class="active"' if href == active else ""
        out.append(f'<a href="{href}"{cls}>{label}</a>')
    return "".join(out)


def toc(items):
    links = "".join(f'<li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in items)
    return f'<aside class="toc"><h2>On this page</h2><ul>{links}</ul></aside>'


def page(fname, title, header, content, toc_items):
    body = f"""{header}
<main class="main">
  <div class="wrap">
    <div class="grid">
      {toc(toc_items)}
      <div class="content">
        {content}
      </div>
    </div>
  </div>
</main>"""
    out = SHELL.format(title=html.escape(title), nav=nav_html(fname), body=body)
    (ROOT / fname).write_text(out)
    print("wrote", fname)


# --------------------------------------------------------------------------
# Overview
# --------------------------------------------------------------------------
def build_index():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Snowflake integration &middot; demo proposal</p>
  <h1>A Snowflake compliance demo the board can actually inspect</h1>
  <p class="lede">A self-contained Snowflake demonstration that ingests real, public contract
  data (CUAD) enriched with synthetic law-firm records, then shows matter-level
  confidentiality, row-level security, clause-risk analysis, and a full audit trail.</p>
  <div class="pills">
    <span class="pill">Plan approved 2026-10-15</span>
    <span class="pill">Public research data only</span>
    <span class="pill">No real client or privileged material</span>
    <span class="pill">Snowflake simulated for now</span>
  </div>
  <p style="margin-top:22px"><a href="demo/index.html" style="display:inline-block;background:#0d9488;color:#fff;font-weight:700;padding:12px 20px;border-radius:10px;text-decoration:none">Open the interactive access-control demo &rarr;</a>
  &nbsp;<a href="poc.html" style="display:inline-block;color:#c3d3e4;font-weight:600;padding:12px 8px">POC &amp; CUAD findings</a></p>
</div></section>"""

    content = """
<section id="purpose">
  <div class="section-kicker">Purpose</div>
  <h2>What this project delivers</h2>
  <p class="lead">This is the recommendation and design package for a demonstrable Snowflake
  capability in a legal-services context. It is deliberately scoped to be built and
  shown quickly, while exercising the Snowflake features that matter to a compliance
  audience: <strong>governed access, data protection, and auditability</strong>.</p>
  <p>Everything here is a <em>starting point for discussion</em>. The board is asked to
  confirm scope, the data-sourcing approach, and the security posture before we build.</p>
</section>

<section id="outcomes">
  <div class="section-kicker">Outcomes</div>
  <h2>Four things the demo proves</h2>
  <div class="cards">
    <div class="card"><h3>1. Governed ingestion</h3><p>Real contract text and CUAD clause
      annotations are loaded and joined to synthetic clients, matters, and staff with
      validated foreign-key relationships.</p></div>
    <div class="card"><h3>2. Matter-level confidentiality</h3><p>Attorneys see only the
      matters they are authorized for. Snowflake row access policies and masking enforce
      the wall at query time, not in application code.</p></div>
    <div class="card"><h3>3. Contract-risk analytics</h3><p>CUAD clause categories feed a
      transparent, rule-based risk rubric that flags termination, indemnification,
      liability, and governing-law exposure.</p></div>
    <div class="card"><h3>4. Verifiable audit</h3><p>We run the same query under multiple
      roles, capture allowed and denied access, and reconstruct it from Snowflake's own
      query and access history.</p></div>
  </div>
</section>

<section id="poc">
  <div class="section-kicker">Proof of concept</div>
  <h2>Working POC and interactive demo</h2>
  <p class="lead">The board asked for a simple login experience, an examination of the CUAD sample, and
  Python scaffolding adaptable to Snowflake. All three are built and staged here.</p>
  <div class="cards">
    <div class="card"><h3>Interactive demo</h3><p>Sign in as a hypothetical attorney and see only your
      documents; sign in as admin to review who accessed which files. Includes a simulated Snowflake
      console and risk register. <a href="demo/index.html">Open the demo &rarr;</a></p></div>
    <div class="card"><h3>Python + SQLite POC</h3><p>A real enforcement layer (<code>poc/access.py</code>),
      a shared risk engine (<code>poc/risk.py</code>), the simulated Snowflake engine, and an
      evidence pack. <a href="poc.html">POC &amp; CUAD findings &rarr;</a></p></div>
    <div class="card"><h3>30 CUAD documents</h3><p>Extracted, analyzed, and modeled. Two assumptions in
      the original plan needed correcting. <a href="poc.html#findings">See the findings &rarr;</a></p></div>
  </div>
</section>

<section id="verified-login">
  <div class="section-kicker">Proposed next capability</div>
  <h2>Webcam-verified login for compliance and RBAC</h2>
  <p class="lead">A design for requiring a webcam photo at sign-in: 1:1 face verification,
  auditable photo retention, embedding and centroid maintenance, and an assurance level
  that actually gates privileged roles and high-confidentiality matters.</p>
  <div class="callout warn"><strong>Design only &mdash; approval gate first</strong>
    Facial biometrics are regulated, sensitive data. Legal review, a DPIA, written consent,
    retention approval, and vendor due diligence come before any real capture. Nothing on
    this site captures a camera or performs recognition today.</div>
  <p><a href="identity-verification.html">Read the verified-login design &rarr;</a>
  &nbsp;·&nbsp; <code>docs/WEBCAM_LOGIN_RBAC.md</code> · <code>sql/identity/01_identity_verification.sql</code></p>
</section>

<section id="support-agent">
  <div class="section-kicker">Proposed support layer</div>
  <h2>A bounded customer-support agent for verification requests</h2>
  <p class="lead">A narrow, retrieval-grounded assistant that explains verification
  policy, triages a fixed set of situations, and starts approved human workflows &mdash;
  without ever making an authentication decision or touching biometric data.</p>
  <div class="callout warn"><strong>Human-in-the-loop by design</strong>
    Consent withdrawal, photo access, appeals, accommodations, fraud reports, and
    break-glass requests always route to a person. Unknown requests are handed off,
    not guessed at.</div>
  <p><a href="support-agent.html">Read the support-agent design &rarr;</a>
  &nbsp;·&nbsp; <code>docs/SUPPORT_AGENT_INTEGRATION.md</code></p>
</section>

<section id="why">
  <div class="section-kicker">Rationale</div>
  <h2>Why CUAD plus synthetic records</h2>
  <p>Fabricated clause text produces a demo that feels fake and can misrepresent the
  strength of the platform. The <a href="https://github.com/The-Atticus-Project/cuad">Contract
  Understanding Atticus Dataset</a> gives us 510 real commercial contracts with 41
  expert-annotated clause categories &mdash; genuine language and genuine labels.</p>
  <p>CUAD is <strong>public research data released under CC&nbsp;BY&nbsp;4.0</strong>. We attach
  fictional matters and confidentiality labels strictly to demonstrate the mechanics.
  We will never present these documents as genuinely privileged, and we will carry the
  license attribution wherever the data appears.</p>
  <div class="callout warn"><strong>Non-negotiable framing</strong>
    Public documents, fictional matters, and a <em>simulated</em> legal-review rubric. The demo
    must not imply real legal advice, real privilege, or real client confidentiality.</div>
</section>

<section id="architecture-at-a-glance">
  <div class="section-kicker">At a glance</div>
  <h2>Proposed architecture</h2>
  <p>A single demo database landing <code>RAW</code> &rarr; <code>CORE</code> &rarr;
  <code>MARTS</code>, with a dedicated <code>SECURITY</code> schema for policies and a
  <code>GOV</code> schema for the audit/reporting views.</p>
  <pre><code>CUAD JSON + Faker seeds
        |
        v
  RAW     raw_cuad_contracts, raw_cuad_clauses, raw_synthetic_*
        |
        v
  CORE    dim_client, dim_employee, dim_matter, dim_contract, fact_clause,
          bridge_matter_contract, matter_authorization, ref_*
        |
        v
  MARTS   mart_matter_risk, mart_high_risk_register   <-- board-facing queries
        |
  SECURITY  matter_access_policy (row access), pii masks, classification tags
  GOV       audit_summary, denied_access_log, query_history views</code></pre>
</section>

<section id="recommendations">
  <div class="section-kicker">Recommendations</div>
  <h2>Ten recommendations</h2>
  <ol>
    <li><strong>Use CUAD as the factual spine.</strong> 20&ndash;30 contracts for the demo core, with the option to scale to all 510.</li>
    <li><strong>Synthesize the business layer, not the legal text.</strong> Faker generates clients, matters, staff, assignments, and approvals.</li>
    <li><strong>Model matters as the confidentiality boundary.</strong> Every access decision keys off <code>matter_id</code>.</li>
    <li><strong>Enforce with row access policies on a mapping table.</strong> No matter-based filtering in application SQL.</li>
    <li><strong>Centralize policy in a <code>SECURITY</code> schema</strong> owned by a compliance role, applied consistently across tables.</li>
    <li><strong>Mask sensitive metadata by role</strong> (client PII, deal values) with dynamic data masking and classification tags.</li>
    <li><strong>Keep the risk rubric transparent and editable.</strong> Rules live as data in a reference table, so thresholds are reviewable &mdash; and clearly labeled simulated.</li>
    <li><strong>Prove governance through Snowflake's own logs.</strong> Query history, access history, and policy references are the evidence.</li>
    <li><strong>Ship the review site from this repo.</strong> GitHub Pages from <code>main</code> is the board's staging surface.</li>
    <li><strong>Keep costs near zero.</strong> X-Small warehouses with aggressive auto-suspend, and a small data footprint.</li>
  </ol>
</section>

<section id="phases">
  <div class="section-kicker">Plan</div>
  <h2>Delivery phases</h2>
  <ol class="timeline">
    <li data-step="0"><h4>Enablement</h4><p>Snowflake account/trial, roles, database skeleton, CI for this Pages site. <a href="architecture.html">Architecture &rarr;</a></p></li>
    <li data-step="1"><h4>Ingest &amp; organize</h4><p>Load 20&ndash;30 CUAD contracts + annotations, generate synthetic records, validate relationships. <a href="data-foundation.html">Data foundation &rarr;</a></p></li>
    <li data-step="2"><h4>Enforce matter confidentiality</h4><p>Attorney/compliance roles, row access policies, masking, classification tags. <a href="security.html">Confidentiality &rarr;</a></p></li>
    <li data-step="3"><h4>Analyze contractual risk</h4><p>Clause-category analytics and the rule-based risk rubric. <a href="risk-analysis.html">Risk analysis &rarr;</a></p></li>
    <li data-step="4"><h4>Verify &amp; audit</h4><p>Multi-role access tests, query-history evidence, high-risk register. <a href="audit-verification.html">Audit &rarr;</a></p></li>
    <li data-step="5"><h4>Board review</h4><p>Publish this site, walk the demo, collect decisions. <a href="roadmap.html">Roadmap &rarr;</a></p></li>
  </ol>
</section>

<section id="decisions">
  <div class="section-kicker">Approved</div>
  <h2>Board decisions</h2>
  <div class="callout ok"><strong>Approved 2026-10-16 &mdash; full dataset</strong>
    The board approved scaling to the <strong>full 510-contract CUAD dataset</strong>, normalizing it
    <strong>inside Snowflake with no API</strong>, generating the simulated RBAC + risk metadata at
    <strong>510 matters</strong>, storing <strong>full contract text</strong>, and building the web app on
    <strong>Streamlit in Snowflake</strong> on a new trial account. Details:
    <a href="full-dataset.html">Full-dataset plan &rarr;</a></div>
  <div class="table-scroll"><table>
    <thead><tr><th>Decision</th><th>Resolution</th></tr></thead>
    <tbody>
      <tr><td>Scope of the demo</td><td><span class="badge low">Full four phases</span> against the full CUAD dataset</td></tr>
      <tr><td>Data sourcing</td><td><span class="badge low">CUAD + synthetic</span>, with full attribution</td></tr>
      <tr><td>Snowflake component</td><td><span class="badge low">Real trial account</span> (2026-10-16)</td></tr>
      <tr><td>Hosting of this review site</td><td><span class="badge low">This repo</span> (<code>main</code> auto-deploys)</td></tr>
      <tr><td>Risk rubric framing</td><td><span class="badge low">Simulated</span> and prominently disclaimed</td></tr>
      <tr><td>Web application</td><td><span class="badge low">Streamlit in Snowflake</span> first</td></tr>
    </tbody>
  </table></div>
</section>
"""
    page("index.html", "Overview", header, content, [
        ("purpose", "Purpose"), ("outcomes", "Outcomes"), ("poc", "Working POC & demo"),
        ("verified-login", "Verified login"), ("support-agent", "Support agent"), ("why", "Why CUAD"), ("architecture-at-a-glance", "Architecture at a glance"),
        ("recommendations", "Ten recommendations"), ("phases", "Delivery phases"),
        ("decisions", "What we need from the board"),
    ])


# --------------------------------------------------------------------------
# Data foundation
# --------------------------------------------------------------------------
def build_data():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Phase 1</p>
  <h1>Data foundation</h1>
  <p class="lede">CUAD supplies real contract language and clause annotations. Faker supplies
  the fictional business context that turns contracts into matters a law firm would recognize.</p>
</div></section>"""

    content = """
<section id="cuad">
  <div class="section-kicker">Source A</div>
  <h2>The CUAD dataset</h2>
  <p>The Contract Understanding Atticus Dataset is a legal AI benchmark: <strong>510
  commercial contracts</strong> annotated across <strong>41 clause categories</strong>
  (the CUAD v1 distribution ships the contracts and annotations as JSON). Each
  annotation carries the clause text span plus an expert Yes/No answer for whether the
  clause type is present.</p>
  <div class="kpis">
    <div class="kpi"><div class="n">510</div><div class="l">contracts available</div></div>
    <div class="kpi"><div class="n">41</div><div class="l">clause categories</div></div>
    <div class="kpi"><div class="n">20&ndash;30</div><div class="l">contracts in demo core</div></div>
    <div class="kpi"><div class="n">CC BY 4.0</div><div class="l">license (attribution)</div></div>
  </div>
  <div class="callout"><strong>License obligation</strong>
    CUAD is distributed under CC&nbsp;BY&nbsp;4.0. We retain the attribution notice, link to the
    source repository, and never imply the documents are client-confidential.</div>
  <h3>What we extract per contract</h3>
  <ul>
    <li><code>contract_name</code>, <code>contract_type</code> (NDA, license, service, etc.), party names.</li>
    <li>Per clause category: <code>answer</code> (Yes/No/NA), annotated <code>text</code> span, character offsets.</li>
  </ul>
  <p>Parsing reference: <code>ingest/load_cuad.py</code> in this repo.</p>
</section>

<section id="synthetic">
  <div class="section-kicker">Source B</div>
  <h2>The synthetic law-firm layer (Faker)</h2>
  <p>Faker (Python) generates deterministic, obviously-fictional records. We fix a random
  seed so every rebuild is reproducible and board reviewers see stable data.</p>
  <div class="table-scroll"><table>
    <thead><tr><th>Entity</th><th>Representative fields</th><th>Purpose in the demo</th></tr></thead>
    <tbody>
      <tr><td><code>client</code></td><td>client_id, name, industry, region, contact</td><td>Owns matters; drives PII masking</td></tr>
      <tr><td><code>employee</code></td><td>employee_id, name, title, practice, role</td><td>Attorneys, paralegals, compliance officers</td></tr>
      <tr><td><code>matter</code></td><td>matter_id, client_id, name, confidentiality_level, opened_on, lead_attorney</td><td>The confidentiality boundary</td></tr>
      <tr><td><code>matter_assignment</code></td><td>matter_id, employee_id, assignment_role</td><td>Working assignments (for reporting)</td></tr>
      <tr><td><code>matter_authorization</code></td><td>matter_id, employee_id, access_level, valid_from, valid_to</td><td><strong>Source of truth for row access</strong></td></tr>
      <tr><td><code>contract_attachment</code></td><td>matter_id, contract_id, executed_on</td><td>Links a CUAD contract to a fictional matter</td></tr>
      <tr><td><code>access_approval</code></td><td>matter_id, employee_id, approved_by, approved_on</td><td>Shows governance workflow</td></tr>
    </tbody>
  </table></div>
  <div class="callout warn"><strong>Clearly fictional</strong>
    Names, matters, and approvals are generated. Client and matter names are prefixed to
    make their synthetic nature unmistakable in screenshots.</div>
</section>

<section id="model">
  <div class="section-kicker">Data model</div>
  <h2>Logical relationships</h2>
  <p>Contracts and the business layer meet at a bridge, because a contract can serve
  more than one matter and a matter can hold more than one contract.</p>
  <pre><code>client 1---* matter *---* contract (via contract_attachment)
  matter 1---* fact_clause *---1 dim_contract
  matter 1---* matter_authorization *---1 employee
  matter 1---* matter_assignment   *---1 employee
  contract 1---* fact_clause *---1 dim_clause_category</code></pre>
  <div class="table-scroll"><table>
    <thead><tr><th>Schema</th><th>Object</th><th>Grain / notes</th></tr></thead>
    <tbody>
      <tr><td>RAW</td><td><code>raw_cuad_contracts</code>, <code>raw_cuad_clauses</code></td><td>VARIANT JSON as landed; no logic</td></tr>
      <tr><td>RAW</td><td><code>raw_synthetic_*</code></td><td>Faker CSV/JSON staging</td></tr>
      <tr><td>CORE</td><td><code>dim_client</code>, <code>dim_employee</code>, <code>dim_matter</code>, <code>dim_contract</code>, <code>dim_clause_category</code></td><td>Conformed dimensions</td></tr>
      <tr><td>CORE</td><td><code>fact_clause</code></td><td>One row per (contract, clause category)</td></tr>
      <tr><td>CORE</td><td><code>bridge_matter_contract</code></td><td>Resolves the many-to-many</td></tr>
      <tr><td>CORE</td><td><code>matter_authorization</code></td><td>Row access mapping table</td></tr>
      <tr><td>MARTS</td><td><code>mart_matter_risk</code>, <code>mart_high_risk_register</code></td><td>Board-facing outputs</td></tr>
    </tbody>
  </table></div>
  <p>Full DDL: <code>sql/02_data_model.sql</code>.</p>
</section>

<section id="quality">
  <div class="section-kicker">Trust</div>
  <h2>Data-quality checks</h2>
  <p>Every load ends with referential-integrity and completeness assertions. Failures
  are surfaced, never silently dropped.</p>
  <pre><code>-- Orphaned clauses (no matching contract)
SELECT f.contract_id, COUNT(*)
FROM core.fact_clause f
LEFT JOIN core.dim_contract c USING (contract_id)
WHERE c.contract_id IS NULL
GROUP BY 1;

-- Matters with no authorized attorney (governance gap)
SELECT m.matter_id
FROM core.dim_matter m
LEFT JOIN core.matter_authorization a USING (matter_id)
WHERE a.matter_id IS NULL;

-- Clause coverage vs CUAD's 41 categories
SELECT COUNT(DISTINCT clause_category_id) AS categories_present
FROM core.fact_clause;

-- Contracts attached to more than one matter (expected for the bridge)
SELECT contract_id, COUNT(DISTINCT matter_id) AS matters
FROM core.bridge_matter_contract GROUP BY 1 HAVING matters > 1;</code></pre>
</section>

<section id="attribution">
  <div class="section-kicker">Compliance</div>
  <h2>Attribution &amp; disclaimers</h2>
  <ul>
    <li>CUAD: The Atticus Project, CC&nbsp;BY&nbsp;4.0 &mdash; linked on every page footer and in the raw tables.</li>
    <li>Contract-to-matter assignments are fictional and exist only to demonstrate the data model.</li>
    <li>No personal data of real people is used; all individuals are synthetic.</li>
  </ul>
</section>
"""
    page("data-foundation.html", "Data foundation", header, content, [
        ("cuad", "The CUAD dataset"), ("synthetic", "Synthetic layer"),
        ("model", "Logical model"), ("quality", "Data-quality checks"),
        ("attribution", "Attribution & disclaimers"),
    ])


# --------------------------------------------------------------------------
# Architecture
# --------------------------------------------------------------------------
def build_architecture():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Phase 0 &amp; platform</p>
  <h1>Snowflake architecture</h1>
  <p class="lede">One demo database, three medallion layers, two tiny warehouses, and a role
  model that separates administration from compliance from legal work.</p>
</div></section>"""

    content = """
<section id="topology">
  <div class="section-kicker">Topology</div>
  <h2>Database &amp; schema layout</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Object</th><th>Type</th><th>Purpose</th></tr></thead>
    <tbody>
      <tr><td><code>SNOW_COMPLIANCE_DEMO</code></td><td>Database</td><td>Everything for the demo</td></tr>
      <tr><td><code>RAW</code></td><td>Schema</td><td>Landing JSON / CSVs, no transformation</td></tr>
      <tr><td><code>CORE</code></td><td>Schema</td><td>Modeled dimensions, facts, bridges</td></tr>
      <tr><td><code>MARTS</code></td><td>Schema</td><td>Curated views for the demo queries</td></tr>
      <tr><td><code>SECURITY</code></td><td>Schema</td><td>Row access policies, masks, mapping tables</td></tr>
      <tr><td><code>GOV</code></td><td>Schema</td><td>Audit summary views over Snowflake metadata</td></tr>
    </tbody>
  </table></div>
  <p>DDL: <code>sql/01_database_and_roles.sql</code>.</p>
</section>

<section id="warehouses">
  <div class="section-kicker">Compute</div>
  <h2>Warehouses</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Warehouse</th><th>Size</th><th>Auto-suspend</th><th>Used for</th></tr></thead>
    <tbody>
      <tr><td><code>WH_LOAD</code></td><td>X-Small</td><td>60s</td><td>Ingest / generation (build only)</td></tr>
      <tr><td><code>WH_ANALYTICS</code></td><td>X-Small</td><td>60s</td><td>Demo queries and reporting</td></tr>
    </tbody>
  </table></div>
  <p>X-Small with 60-second auto-suspend keeps an idle demo effectively free. The dataset
  is tiny (well under a gigabyte), so compute, not storage, is the only cost lever.</p>
</section>

<section id="roles">
  <div class="section-kicker">Access</div>
  <h2>Role model</h2>
  <pre><code>ACCOUNTADMIN
  SYSADMIN
    DEMO_ADMIN          -- builds RAW/CORE/MARTS
    COMPLIANCE_ADMIN    -- owns SECURITY schema (policies, masks, mapping)
    ATTORNEY            -- matter-scoped reads via row access policy
    PARALEGAL           -- matter-scoped reads, reduced columns
    AUDITOR             -- reads GOV audit views; no data mutation</code></pre>
  <div class="callout"><strong>Principle</strong>
    Administrators never use <code>ACCOUNTADMIN</code> for demo work. Analysts never see
    unfiltered matter data. Policy objects live in <code>SECURITY</code> and are owned by
    <code>COMPLIANCE_ADMIN</code>, not by whoever builds the tables.</div>
</section>

<section id="deploy">
  <div class="section-kicker">Delivery</div>
  <h2>Deployment &amp; environments</h2>
  <ul>
    <li><strong>Snowflake:</strong> scripts in <code>sql/</code> run in order; <code>ingest/</code> scripts populate data. Idempotent (CREATE OR REPLACE, MERGE) so the demo can be rebuilt from scratch.</li>
    <li><strong>Review site:</strong> this repo. GitHub Pages serves <code>main:/</code> &mdash; any push to <code>main</code> republishes automatically. It is the staging surface for board review.</li>
    <li><strong>Secrets:</strong> Snowflake credentials are stored as Paperclip secrets and injected at run time &mdash; never committed to this repo or pasted into documents.</li>
  </ul>
</section>

<section id="cost">
  <div class="section-kicker">Cost</div>
  <h2>Cost posture</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Item</th><th>Estimate</th><th>Note</th></tr></thead>
    <tbody>
      <tr><td>Snowflake compute</td><td>&lt; $5 while actively building/demoing</td><td>X-Small, auto-suspend; a trial credit covers it</td></tr>
      <tr><td>Snowflake storage</td><td>Negligible</td><td>Sub-GB dataset</td></tr>
      <tr><td>GitHub Pages</td><td>$0</td><td>Public repo, static site</td></tr>
    </tbody>
  </table></div>
</section>
"""
    page("architecture.html", "Architecture", header, content, [
        ("topology", "Database & schema layout"), ("warehouses", "Warehouses"),
        ("roles", "Role model"), ("deploy", "Deployment & environments"), ("cost", "Cost posture"),
    ])


# --------------------------------------------------------------------------
# Security / confidentiality
# --------------------------------------------------------------------------
def build_security():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Phase 2</p>
  <h1>Matter confidentiality</h1>
  <p class="lede">The confidentiality wall is enforced by Snowflake itself: row access
  policies scope every row to an authorized matter, and masking hides sensitive metadata
  from roles that should not see it.</p>
</div></section>"""

    content = """
<section id="goal">
  <div class="section-kicker">Goal</div>
  <h2>Prevent cross-matter access at query time</h2>
  <p>If an attorney queries a contract table, the result must contain only rows for
  matters they are authorized for &mdash; with no dependence on the application adding a
  <code>WHERE</code> clause. The authorization mapping is data, so access changes are
  auditable business events, not code deployments.</p>
</section>

<section id="mapping">
  <div class="section-kicker">Mechanism</div>
  <h2>The authorization mapping</h2>
  <p>Row access policies evaluate per query. The mapping table links a role (or an
  employee identity) to the matters they may see.</p>
  <pre><code>CREATE TABLE security.matter_access_map (
  role_name  STRING,
  matter_id  STRING,
  access_level STRING,      -- READ | WRITE
  valid_from DATE,
  valid_to   DATE
);</code></pre>
</section>

<section id="policies">
  <div class="section-kicker">Policy</div>
  <h2>Row access policy</h2>
  <p>Applied to every table that carries <code>matter_id</code>. Administrators bypass it
  by design; everyone else is scoped.</p>
  <pre><code>CREATE OR REPLACE ROW ACCESS POLICY security.matter_access_policy
  AS (matter_id STRING) RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('ACCOUNTADMIN','SYSADMIN','COMPLIANCE_ADMIN','AUDITOR')
    OR EXISTS (
        SELECT 1
        FROM security.matter_access_map m
        WHERE m.role_name = CURRENT_ROLE()
          AND m.matter_id = matter_id
          AND CURRENT_DATE() BETWEEN m.valid_from AND COALESCE(m.valid_to,'9999-12-31')
    );

ALTER TABLE core.fact_clause
  ADD ROW ACCESS POLICY security.matter_access_policy ON (matter_id);</code></pre>
  <div class="callout ok"><strong>Recommended variant</strong>
    Map by <em>role</em> for a clean demo, and note the production upgrade path: map by
    <code>employee_id</code> resolved from the session, so each named attorney has their own
    wall rather than a shared role.</div>
</section>

<section id="masking">
  <div class="section-kicker">Protection</div>
  <h2>Dynamic data masking</h2>
  <p>Row policies hide <em>rows</em>; masking policies hide <em>columns</em>. Applied to
  client PII and commercially sensitive metadata.</p>
  <pre><code>CREATE OR REPLACE MASKING POLICY security.pii_mask
  AS (val STRING) RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('COMPLIANCE_ADMIN','ACCOUNTADMIN') THEN val
      WHEN CURRENT_ROLE() IN ('ATTORNEY','PARALEGAL') THEN '***REDACTED***'
      ELSE NULL
    END;

ALTER TABLE core.dim_client
  MODIFY COLUMN contact_email SET MASKING POLICY security.pii_mask;
ALTER TABLE core.dim_client
  MODIFY COLUMN contact_phone SET MASKING POLICY security.pii_mask;</code></pre>
  <h3>Classification tags</h3>
  <p>Tag columns once (<code>PII</code>, <code>CONFIDENTIAL</code>, <code>ATTORNEY_WORK_PRODUCT</code>)
  and attach tag-based masking for consistent, self-documenting protection.</p>
</section>

<section id="gotchas">
  <div class="section-kicker">Details</div>
  <h2>Implementation notes</h2>
  <ul>
    <li>Row access policies and certain constraints are mutually exclusive &mdash; model keys without relying on blocked constraint types on protected tables.</li>
    <li>Policy-protected data must be read through secure views or the base tables directly; never copy unfiltered rows into a permissive table.</li>
    <li>Attach policies to <em>every</em> table carrying <code>matter_id</code>, including bridges, to avoid a leak through a join.</li>
    <li>Include an <code>AUDITOR</code> bypass so verification can enumerate the full picture.</li>
    <li>Document role reachability: which roles inherit the bypass, and why.</li>
  </ul>
  <p>Full DDL: <code>sql/03_row_access_and_masking.sql</code>.</p>
</section>
"""
    page("security.html", "Confidentiality", header, content, [
        ("goal", "Goal"), ("mapping", "Authorization mapping"), ("policies", "Row access policy"),
        ("masking", "Dynamic data masking"), ("gotchas", "Implementation notes"),
    ])


# --------------------------------------------------------------------------
# Verified login (proposed webcam feature)
# --------------------------------------------------------------------------
def build_identity():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Proposed capability &middot; not yet implemented</p>
  <h1>Webcam-verified login, governed end to end</h1>
  <p class="lede">A design for requiring a webcam photo at sign-in: 1:1 face
  verification, auditable photo retention, embedding and centroid maintenance,
  and an assurance level that actually controls RBAC.</p>
  <div class="pills">
    <span class="pill">Step-up, not a password replacement</span>
    <span class="pill">1:1 verification only</span>
    <span class="pill">Snowflake-governed audit</span>
    <span class="pill">Legal review required</span>
  </div>
</div></section>"""

    content = """
<section id="warning">
  <div class="callout danger"><strong>Biometric data &mdash; approval gate</strong>
    This is a proposal, not a working capture feature. Facial biometrics are sensitive
    personal information and are regulated in several jurisdictions. Do not enable
    real capture, store real employee photos, or pilot with real people until legal
    review, a DPIA, written consent, retention approval, and vendor due diligence are
    complete. This page and the full guide are design material, not legal advice.</div>
</section>

<section id="recommendation">
  <div class="section-kicker">Recommendation</div>
  <h2>Add verification as a step-up authenticator</h2>
  <p class="lead">A face is not a secret. A printed photo or replayed video can be
  presented to a camera, so webcam verification must sit <strong>after</strong>
  password + MFA and raise an <em>authentication assurance level</em>. It must never
  become the only factor protecting privileged roles.</p>
  <div class="table-scroll"><table>
    <thead><tr><th>Decision</th><th>Recommendation</th><th>Reason</th></tr></thead>
    <tbody>
      <tr><td>Matching mode</td><td><span class="badge low">1:1 self-verification</span></td><td>1:N identification creates much larger privacy, bias, and false-match exposure.</td></tr>
      <tr><td>Enrollment</td><td><span class="badge low">3&ndash;5 consented frames</span></td><td>One frame cannot estimate within-person variance or calibrate a threshold.</td></tr>
      <tr><td>Raw photo retention</td><td><span class="badge med">90 days default</span></td><td>Enough for audit; not an indefinite biometric archive. Legal hold overrides deletion.</td></tr>
      <tr><td>Embeddings</td><td><span class="badge med">Employment + audit tail</span></td><td>Vectors are still biometric data; delete on separation or withdrawal.</td></tr>
      <tr><td>Thresholds</td><td><span class="badge high">Calibrated, never guessed</span></td><td>Published numbers from other deployments do not transfer to our cameras and population.</td></tr>
      <tr><td>Fallback</td><td><span class="badge high">Assisted, never silent</span></td><td>Outages and accommodations must not become an authentication bypass.</td></tr>
    </tbody>
  </table></div>
</section>

<section id="flow">
  <div class="section-kicker">User experience</div>
  <h2>Enrollment and daily sign-in</h2>
  <div class="cards">
    <div class="card"><h3>1. Consent and enroll</h3><p>After password + MFA, explain purpose,
      retention, viewers, and the voluntary alternative. Capture 3&ndash;5 frames with a
      random challenge and quality/liveness gates. Store the template and centroid version.</p></div>
    <div class="card"><h3>2. Sign in</h3><p>Password + MFA produce a short-lived pre-auth session.
      The camera step captures a fresh frame with a server nonce, then runs quality &rarr;
      liveness &rarr; embedding &rarr; 1:1 comparison.</p></div>
    <div class="card"><h3>3. Issue assurance</h3><p>On accept, the token carries
      <code>verification_id</code>, <code>assurance_level</code>, <code>model_id</code>,
      <code>centroid_version</code>, and <code>verified_at</code>. Snowflake maps that to a role.</p></div>
    <div class="card"><h3>4. Step up when it matters</h3><p>Opening a High-confidentiality matter
      or changing policy requires a fresh verification (for example, within 5 minutes) with
      its own audit event.</p></div>
  </div>
  <div class="callout warn"><strong>Failure behavior is part of the design</strong>
    Poor lighting gets guidance; liveness failure gets one retry then a deny and an alert;
    a review-band score never auto-accepts; service outages fail closed for privileged roles
    and route to an assisted path with two-person approval.</div>
</section>

<section id="architecture">
  <div class="section-kicker">Architecture</div>
  <h2>Five isolated responsibilities</h2>
  <pre><code>Browser (getUserMedia, challenge UI)
        |
        |  TLS, server nonce, image bytes
        v
Verification API  --- signed event --->  SIEM
        |
        +--> Face pipeline: detect -> align -> quality -> liveness -> embed
        |             |
        |             +--> model registry / thresholds
        |
        +--> Encrypted photo store (Object Lock, 90-day lifecycle)
        |
        +--> Snowflake IDENTITY (templates, centroids, attempts, audit)
        |
        +--> IdP / token service (assurance claims -> Snowflake role)</code></pre>
  <p>The face model runs in a container service or vendor API, not as a Snowflake-native
  function. Only the resulting vector and decision metadata are written to Snowflake.
  Snowflake Cortex text embeddings are <strong>not</strong> a face-embedding substitute.</p>
</section>

<section id="model">
  <div class="section-kicker">Data model</div>
  <h2>Evidence, templates, and identity are separate</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Object</th><th>What it holds</th><th>Protection</th></tr></thead>
    <tbody>
      <tr><td><code>consent_record</code></td><td>Version, signature, withdrawal</td><td>Append-only; drives deletion workflow</td></tr>
      <tr><td><code>face_template</code></td><td>512-d embedding per enrollment frame</td><td>Restricted grants; never returned to the browser</td></tr>
      <tr><td><code>face_centroid</code></td><td>Current normalized centroid, sample count, intra-user distance</td><td>Row access; versioned; history retained</td></tr>
      <tr><td><code>login_attempt</code></td><td>Decision, scores, model/centroid version, request ID</td><td>Self-or-oversight row access; audit retention</td></tr>
      <tr><td><code>photo_audit</code></td><td>Object URI, SHA-256, retention date, legal hold</td><td>URI masked; deletions leave a tombstone</td></tr>
      <tr><td><code>verification_event</code></td><td>Canonical payload + hash chain</td><td>Append-only; periodically anchored</td></tr>
      <tr><td><code>role_assurance_policy</code></td><td>Required AAL per Snowflake role</td><td>Owned by <code>COMPLIANCE_ADMIN</code></td></tr>
    </tbody>
  </table></div>
  <p>Full DDL: <code>sql/identity/01_identity_verification.sql</code>. Vectors use
  Snowflake's <code>VECTOR(FLOAT, 512)</code>; raw photos stay in encrypted object storage,
  not in a table.</p>
</section>

<section id="embeddings">
  <div class="section-kicker">AI / ML</div>
  <h2>Embeddings and a centroid that does not drift away</h2>
  <p>Use an ArcFace/InsightFace-family model that outputs an L2-normalized
  <strong>512-dimensional</strong> vector, or a vendor verification API with a calibrated
  score. Record the exact model, preprocessing, and threshold versions. Pin artifact
  hashes and treat a model change as a new template generation.</p>
  <pre><code>c_0 = normalize(mean(e_1 ... e_n))          # enrollment centroid
d_i = 1 - cosine(e_i, c_0)                 # intra-user distance
p50, p95 = percentiles(d_i)
alpha_eff = max(0.05, 1 / (sample_count + 1))
c_new = normalize((1 - alpha_eff) * c_old + alpha_eff * e_accepted)</code></pre>
  <p>Update only on an <code>accept</code> with a margin above threshold, good liveness and
  quality, no legal hold, and no outlier flag. Cap updates at three per day and keep a
  version history with rollback.</p>
  <div class="table-scroll"><table>
    <thead><tr><th>Centroid risk</th><th>Guard</th></tr></thead>
    <tbody>
      <tr><td>One bad frame pulls the template</td><td>Outlier gate at the user's p99 + margin; reject the update</td></tr>
      <tr><td>Repeated spoofs shift identity</td><td>Liveness gate, daily cap, spoof alerts, quarantine after anomalies</td></tr>
      <tr><td>Camera or model drift</td><td>Cohort monitoring, per-user drift alerts, recompute on model upgrade</td></tr>
      <tr><td>Attacker re-enrolls the account</td><td>MFA + manager/compliance approval + cooling-off period</td></tr>
      <tr><td>Silent model change</td><td>New <code>model_id</code>; rebuild centroids from active templates; retain old vectors for audit</td></tr>
      <tr><td>Corrupt centroid</td><td>Version history, checksum, two-person review for forced updates, rollback</td></tr>
    </tbody>
  </table></div>
</section>

<section id="decision">
  <div class="section-kicker">Verification</div>
  <h2>Three bands, with liveness overriding the score</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Band</th><th>Similarity</th><th>Outcome</th><th>User experience</th></tr></thead>
    <tbody>
      <tr><td>Accept</td><td>&ge; 0.68</td><td><span class="badge low">accept</span></td><td>Sign in with the required assurance</td></tr>
      <tr><td>Review</td><td>0.58&ndash;0.679</td><td><span class="badge med">review</span></td><td>Assisted verification; never auto-accept</td></tr>
      <tr><td>Deny</td><td>&lt; 0.58</td><td><span class="badge high">deny</span></td><td>Neutral failure, retry policy, security log</td></tr>
    </tbody>
  </table></div>
  <p class="disclaimer">Illustrative starting points for an ArcFace-family model. Calibrate
  on a consented pilot and approve the FAR/FRR risk appetite before production. Liveness or
  quality failure is always a deny, even if the similarity is high.</p>
</section>

<section id="rbac">
  <div class="section-kicker">RBAC</div>
  <h2>Assurance levels map to real Snowflake roles</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Role</th><th>Required assurance</th><th>Step-up</th><th>Photo / embedding access</th></tr></thead>
    <tbody>
      <tr><td><code>PARALEGAL</code></td><td><code>AAL2</code></td><td>High matters</td><td>No</td></tr>
      <tr><td><code>ATTORNEY</code></td><td><code>AAL2</code></td><td>High matters</td><td>No</td></tr>
      <tr><td><code>AUDITOR</code></td><td><code>AAL2</code></td><td>Never</td><td>Break-glass only</td></tr>
      <tr><td><code>COMPLIANCE_ADMIN</code></td><td><code>AAL3</code></td><td>Policy changes</td><td>Yes, with reason + log</td></tr>
      <tr><td><code>DEMO_ADMIN</code></td><td><code>AAL3</code> + managed device</td><td>Always</td><td>Emergency only</td></tr>
    </tbody>
  </table></div>
  <ul>
    <li>Use external OAuth or governed token exchange so the app never holds a Snowflake password.</li>
    <li>Never trust a client-supplied <code>assurance_level</code>; read it from the signed token or server-side verification record.</li>
    <li>Bind the token to the verification event and expire it quickly; re-check freshness for step-up actions.</li>
    <li>Keep matter confidentiality in row access policies. Add assurance through roles/entitlements, not unverified session text.</li>
    <li>Break-glass is time-bound, two-person approved, reason-coded, and fully audited &mdash; not a silent fallback.</li>
  </ul>
</section>

<section id="audit">
  <div class="section-kicker">Audit &amp; retention</div>
  <h2>Provable decisions, deletable photos</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Artifact</th><th>Default retention</th><th>Deletion trigger</th></tr></thead>
    <tbody>
      <tr><td>Raw login photo</td><td>90 days</td><td>Consent withdrawal, erasure request, successful appeal</td></tr>
      <tr><td>Enrollment photos</td><td>Employment + 90 days</td><td>Separation + audit tail, withdrawal</td></tr>
      <tr><td>Template / embedding</td><td>Employment + audit tail</td><td>Separation, withdrawal, model retirement</td></tr>
      <tr><td>Login metadata</td><td>2 years</td><td>Investigation hold</td></tr>
      <tr><td>Audit hash chain</td><td>7 years</td><td>Legal requirement</td></tr>
      <tr><td>Photo access log</td><td>7 years</td><td>Legal requirement</td></tr>
    </tbody>
  </table></div>
  <p>Every attempt records the outcome, scores, model/centroid version, photo hash, request
  ID, IP/user agent, and resulting assurance. Every human view of a raw photo writes a
  <code>photo_access_log</code> row with a reason and approver. Photos use Object Lock and
  lifecycle deletion; legal hold blocks removal. The hash chain is periodically anchored in
  immutable storage, and Snowflake <code>ACCESS_HISTORY</code> provides independent evidence.</p>
</section>

<section id="compliance">
  <div class="section-kicker">Compliance</div>
  <h2>Requirements before any real capture</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Area</th><th>Requirement</th></tr></thead>
    <tbody>
      <tr><td>Legal basis</td><td>Written informed consent where required (for example BIPA, Texas CUBI, Washington); a genuine alternative and no retaliation.</td></tr>
      <tr><td>Notice</td><td>Purpose, data categories, retention, recipients, and rights explained before the first capture.</td></tr>
      <tr><td>DPIA</td><td>Before pilot; refresh on model, vendor, or retention changes.</td></tr>
      <tr><td>Minimization</td><td>No emotion, health, demographic, or surveillance data; do not retain rejected frames by default.</td></tr>
      <tr><td>Vendor</td><td>DPA, subprocessors, security attestations, deletion terms, breach notice, transfer mechanism.</td></tr>
      <tr><td>Access</td><td>Least privilege, two-person raw-photo access, break-glass with audit.</td></tr>
      <tr><td>Bias &amp; accessibility</td><td>Evaluate error rates across lighting, cameras, age, and accessibility needs; provide assisted verification; never adjust scores with protected attributes.</td></tr>
      <tr><td>AI governance</td><td>Model card, intended use, evaluation, human oversight, change control, incident response. Check EU AI Act and workplace-biometric rules with counsel.</td></tr>
      <tr><td>Employment</td><td>Confirm voluntariness, works council/union consultation, and non-retaliation.</td></tr>
    </tbody>
  </table></div>
  <div class="callout warn"><strong>Jurisdictions differ materially</strong>
    Some statutes require a written release and retention schedule; some restrict employer
    collection; some create a private right of action. This table is not a legal opinion.</div>
</section>

<section id="implementation">
  <div class="section-kicker">Implementation</div>
  <h2>What to build, in order</h2>
  <ol class="timeline">
    <li data-step="0"><h4>Legal &amp; design gate</h4><p>DPIA, consent text, retention schedule, vendor selection, works council review, threat model. No real captures.</p></li>
    <li data-step="1"><h4>Sandbox</h4><p>Integrate the model behind the reference interface; apply the <code>IDENTITY</code> DDL; calibrate thresholds; verify the audit chain and deletion workflow on synthetic data.</p></li>
    <li data-step="2"><h4>20-person pilot</h4><p>Both camera types, accessibility testing, assisted path, FAR/FRR measurement, bias review. Do not scale on a single happy path.</p></li>
    <li data-step="3"><h4>Privileged roles</h4><p>Compliance admin, auditors, and High-matter attorneys. Exercise step-up, break-glass, and rollback drills.</p></li>
    <li data-step="4"><h4>General rollout</h4><p>Training, support runbook, quarterly access review, retention-job monitoring, board reporting.</p></li>
  </ol>
  <p><strong>Reference logic:</strong> <code>poc/face_verification.py</code> implements the
  deterministic parts &mdash; normalization, cosine matching, centroid guards, quality/liveness
  gates, three-band decisions, and a hash chain. It uses a test-only hashing embedder; replace
  that with the approved model. Run <code>python3 -m unittest poc/test_face_verification.py -v</code>.</p>
  <pre><code># Proposed API surface
POST /v1/enrollment/start      -> challenge nonce + guidance
POST /v1/enrollment/capture    -> quality / liveness / frames remaining
POST /v1/enrollment/complete   -> template_id + centroid_version
POST /v1/login/verify          -> decision + assurance_level + verification_id
POST /v1/admin/photos/{id}/access -> short-lived URL + photo_access_log row</code></pre>
</section>

<section id="board">
  <div class="section-kicker">Decisions requested</div>
  <h2>What the board needs to settle</h2>
  <ol>
    <li>Mandatory, voluntary, or role-based participation &mdash; and the approved alternative for people who decline or cannot use a camera.</li>
    <li>Self-hosted model vs. vendor API; if vendor, which regions and retention terms.</li>
    <li>Raw-photo retention period and who may approve legal hold.</li>
    <li>Which roles require <code>AAL2</code> vs. <code>AAL3</code>, and which matters require fresh step-up.</li>
    <li>FAR/FRR risk appetite and who signs off on threshold calibration.</li>
    <li>Re-enrollment approval path and the two break-glass approvers.</li>
  </ol>
  <p>Full design, data model, threat model, API contracts, rollout criteria, and cost sketch:
  <code>docs/WEBCAM_LOGIN_RBAC.md</code> in the repository. Proposed DDL:
  <code>sql/identity/01_identity_verification.sql</code>.</p>
  <div class="callout ok"><strong>Status</strong>
    Design only. No camera capture, photo storage, model inference, or recognition is
    enabled in the current demo. The next step is the legal/DPIA gate, not a pilot.</div>
</section>
"""
    page("identity-verification.html", "Verified login", header, content, [
        ("warning", "Approval gate"), ("recommendation", "Recommendation"), ("flow", "User experience"),
        ("architecture", "Architecture"), ("model", "Data model"), ("embeddings", "Embeddings & centroid"),
        ("decision", "Decision bands"), ("rbac", "RBAC"), ("audit", "Audit & retention"),
        ("compliance", "Compliance"), ("implementation", "Implementation"), ("board", "Decisions requested"),
    ])


# --------------------------------------------------------------------------
# Bounded customer-support agent
# --------------------------------------------------------------------------
def build_support():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Proposed support layer &middot; bounded and human-in-the-loop</p>
  <h1>A support agent that knows what it must not do</h1>
  <p class="lede">Field the predictable requests around webcam verification &mdash;
  camera trouble, retries, lockouts, accommodations, consent withdrawal, appeals,
  and audit questions &mdash; without letting a chat message become an auth bypass.</p>
  <div class="pills">
    <span class="pill">Fixed situation catalog</span>
    <span class="pill">Grounded in approved policy</span>
    <span class="pill">Self-only tools</span>
    <span class="pill">Human handoff for high risk</span>
  </div>
</div></section>"""

    content = """
<section id="warning">
  <div class="callout danger"><strong>Bounded, not a general chatbot</strong>
    This assistant explains policy, triages a known situation set, and opens approved
    human workflows. It never approves access, changes a role, unlocks an account,
    deletes audit records, disables liveness, or reads raw photos, embeddings, or
    another employee's data. Unknown or low-confidence requests go to a person.</div>
</section>

<section id="why">
  <div class="section-kicker">Why</div>
  <h2>The login flow creates a predictable support tail</h2>
  <p class="lead">Most verification support is explanation and routing, not a decision.
  That is the safe scope for an agent: answer from approved policy, check the caller's
  own status, and create the right human request.</p>
  <div class="cards">
    <div class="card"><h3>Explain</h3><p>Camera permissions, lighting, liveness retries,
      review-band results, fresh step-up, retention, and who can view a photo.</p></div>
    <div class="card"><h3>Triage</h3><p>Map the message to one catalog situation with a
      confidence score. Ambiguous or unknown requests are handed off.</p></div>
    <div class="card"><h3>Start a workflow</h3><p>Open an assisted-verification request, a
      device ticket, an unlock ticket, an appeal, or a privacy case.</p></div>
    <div class="card"><h3>Protect the boundary</h3><p>No auth decisions, no biometric
      payloads, no cross-user reads, no role changes, and full audit.</p></div>
  </div>
</section>

<section id="situations">
  <div class="section-kicker">Scope</div>
  <h2>The initial situation catalog</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Code</th><th>Example request</th><th>Agent can</th><th>Human required</th></tr></thead>
    <tbody>
      <tr><td><code>ENROLLMENT</code></td><td>"How do I enroll my face?"</td><td>Explain steps, check own status, offer assisted enrollment</td><td>No</td></tr>
      <tr><td><code>CAMERA_DEVICE</code></td><td>"My camera is blocked."</td><td>Troubleshoot permissions, browser, lighting, virtual camera</td><td>No</td></tr>
      <tr><td><code>VERIFICATION_FAILURE</code></td><td>"It keeps failing liveness."</td><td>Explain reason codes, offer retry guidance and a fresh challenge</td><td>No</td></tr>
      <tr><td><code>ACCOUNT_LOCKOUT</code></td><td>"I am locked out."</td><td>Explain policy, open an unlock ticket</td><td>Yes, to unlock</td></tr>
      <tr><td><code>ASSISTED_VERIFICATION</code></td><td>"I need a person to verify me."</td><td>Create an assisted-verification request</td><td>Yes, to verify</td></tr>
      <tr><td><code>ACCOMMODATION</code></td><td>"I cannot use a camera."</td><td>Start an accommodation case; explain the equivalent path</td><td>Yes</td></tr>
      <tr><td><code>CONSENT_WITHDRAWAL</code></td><td>"Delete my face data."</td><td>Explain scope, open a privacy case</td><td>Yes, to confirm and execute</td></tr>
      <tr><td><code>AUDIT_RECORD</code></td><td>"Show my verification history."</td><td>Return the caller's own redacted summary</td><td>No</td></tr>
      <tr><td><code>APPEAL</code></td><td>"I want to appeal the denial."</td><td>Explain the path, open an appeal case</td><td>Yes</td></tr>
      <tr><td><code>STEP_UP</code></td><td>"Why verify again?"</td><td>Explain fresh step-up; send a new challenge</td><td>No</td></tr>
      <tr><td><code>SUSPECTED_FRAUD</code></td><td>"Someone is using my account."</td><td>Acknowledge, preserve context, escalate now</td><td>Immediately</td></tr>
      <tr><td><code>PHOTO_ACCESS</code></td><td>"Can I see my login photo?"</td><td>Explain viewers; open a compliance review</td><td>Yes, to release</td></tr>
      <tr><td><code>BREAK_GLASS</code></td><td>"I need emergency access."</td><td>Explain two-person approval; open an urgent ticket</td><td>Always</td></tr>
      <tr><td><code>POLICY_FAQ</code></td><td>"How long do you keep photos?"</td><td>Answer only from approved policy articles</td><td>No</td></tr>
      <tr><td><code>UNKNOWN</code></td><td>Anything else</td><td>Say it is out of scope and hand off</td><td>Yes</td></tr>
    </tbody>
  </table></div>
  <p>The catalog is data, not prompt text. Changing a situation or tool requires review,
  tests, and a new agent release.</p>
</section>

<section id="architecture">
  <div class="section-kicker">Architecture</div>
  <h2>Model for language, code for authority</h2>
  <pre><code>Chat widget (authenticated session)
        |
        v
Support API ---> SUPPORT schema (redacted transcript, intents, tool calls, escalations)
        |
        +--> Orchestrator
        |      +--> intent classifier (catalog code + confidence)
        |      +--> policy engine (scope, allowlist, human gate)
        |      +--> retrieval (approved KB only, citation required)
        |      +--> response composer (low temperature, JSON schema)
        |      +--> tool gateway (self-only, validated args, approvals)
        |
        +--> Human console / queue (warm handoff, SLA)
        |
        +--> Ticketing / HR / compliance case systems</code></pre>
  <p>The model never receives a database credential. It can propose an action, but the
  deterministic tool gateway decides whether that tool is allowed for the situation,
  whether it needs human approval, and which employee it may act on.</p>
</section>

<section id="guardrails">
  <div class="section-kicker">Safety</div>
  <h2>Guardrails that are enforced outside the prompt</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Risk</th><th>Control</th></tr></thead>
    <tbody>
      <tr><td>Prompt injection / "ignore instructions"</td><td>User and retrieved text are data; tool calls come from policy, not free text; tool names and arguments are validated.</td></tr>
      <tr><td>Cross-user data request</td><td>No cross-user tool exists; gateway derives employee ID from the verified session and ignores body IDs.</td></tr>
      <tr><td>Photo or embedding request</td><td>Biometric tools are denied; the support schema has no grants on <code>IDENTITY</code> or the photo stage.</td></tr>
      <tr><td>Credential phishing in chat</td><td>Never ask for passwords, MFA codes, tokens, photos, or government IDs; redact volunteered PII before storage.</td></tr>
      <tr><td>Hallucinated policy</td><td>Answers require an approved citation; no citation means "I cannot confirm" and a handoff.</td></tr>
      <tr><td>Ambiguous or unknown request</td><td>One clarifying question maximum, then handoff with the context.</td></tr>
      <tr><td>Unauthorized action</td><td>High-risk tools require human approval; every invocation is logged with args and result.</td></tr>
      <tr><td>Model or retrieval outage</td><td>Fail closed to a human queue; never fall back to an ungrounded answer.</td></tr>
    </tbody>
  </table></div>
</section>

<section id="tools">
  <div class="section-kicker">Integration</div>
  <h2>Tool contracts are small and self-only</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Tool</th><th>Purpose</th><th>Scope</th><th>Human approval</th></tr></thead>
    <tbody>
      <tr><td><code>get_my_enrollment_status</code></td><td>Status, model, last verification</td><td>Self</td><td>No</td></tr>
      <tr><td><code>get_my_login_attempts</code></td><td>Recent outcomes and reason codes</td><td>Self</td><td>No</td></tr>
      <tr><td><code>get_my_audit_summary</code></td><td>Redacted own audit summary</td><td>Self</td><td>No</td></tr>
      <tr><td><code>search_support_kb</code></td><td>Approved articles with citations</td><td>KB</td><td>No</td></tr>
      <tr><td><code>create_support_ticket</code></td><td>Open a categorized case</td><td>Self</td><td>No</td></tr>
      <tr><td><code>request_assisted_verification</code></td><td>Create a specialist review</td><td>Self</td><td>No</td></tr>
      <tr><td><code>start_reverification</code></td><td>Send a fresh challenge</td><td>Self</td><td>No</td></tr>
      <tr><td><code>request_accommodation</code></td><td>Start an HR/compliance case</td><td>Self</td><td>Yes</td></tr>
      <tr><td><code>request_consent_withdrawal</code></td><td>Open a deletion/withdrawal case</td><td>Self</td><td>Yes</td></tr>
      <tr><td><code>request_photo_access</code></td><td>Open a compliance review</td><td>Self</td><td>Yes</td></tr>
      <tr><td><code>escalate_to_human</code></td><td>Warm handoff with redacted context</td><td>Self</td><td>No</td></tr>
    </tbody>
  </table></div>
  <p>Always denied: reading another user, raw photos, embeddings, centroids, role
  changes, account unlock, access approval, audit deletion, threshold changes, SQL
  passthrough, and HTTP passthrough.</p>
</section>

<section id="rbac">
  <div class="section-kicker">RBAC</div>
  <h2>Separate service, human queue, and oversight</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Role</th><th>Can</th><th>Cannot</th></tr></thead>
    <tbody>
      <tr><td><code>SUPPORT_AGENT</code></td><td>Write conversations, intents, tool calls, escalations; read published KB</td><td>Read <code>IDENTITY</code>, photos, embeddings, or other users' conversations</td></tr>
      <tr><td><code>SUPPORT_HUMAN</code></td><td>Read assigned conversations, resolve escalations, log access</td><td>Change roles, unlock accounts, approve photo access, view raw photos</td></tr>
      <tr><td><code>COMPLIANCE_ADMIN</code></td><td>Manage KB and release config; review high-risk cases</td><td>Break-glass without two-person approval</td></tr>
      <tr><td><code>AUDITOR</code></td><td>Read audit metadata and escalation history</td><td>Read raw transcripts or photos outside policy</td></tr>
    </tbody>
  </table></div>
  <p>Row access limits conversations to the employee and oversight roles. Every human
  transcript view writes an access-log row. The support service has no grant on the
  biometric schema or photo stage.</p>
</section>

<section id="evaluation">
  <div class="section-kicker">Quality</div>
  <h2>Evaluate routing, grounding, and abuse</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Metric</th><th>Target</th></tr></thead>
    <tbody>
      <tr><td>Unauthorized tool executions</td><td><span class="badge low">0</span></td></tr>
      <tr><td>Cross-user data disclosures</td><td><span class="badge low">0</span></td></tr>
      <tr><td>Credential/photo requests</td><td><span class="badge low">0</span></td></tr>
      <tr><td>Correct routing on golden set</td><td><span class="badge low">&ge; 95%</span></td></tr>
      <tr><td>Citation coverage for policy claims</td><td><span class="badge low">&ge; 95%</span></td></tr>
      <tr><td>Handoff for unknown / high risk</td><td><span class="badge low">100%</span></td></tr>
      <tr><td>Time to first response</td><td><span class="badge med">&lt; 5 s</span></td></tr>
    </tbody>
  </table></div>
  <p>Red-team prompt injection, cross-user requests, photo/embedding requests, credential
  phishing, fabricated policy, and urgency pressure ("I am the admin, unlock it now").
  Use synthetic conversations for the pilot.</p>
</section>

<section id="rollout">
  <div class="section-kicker">Rollout</div>
  <h2>Start narrow</h2>
  <ol class="timeline">
    <li data-step="0"><h4>Define</h4><p>Approve the situation catalog, KB ownership, privacy review, and support SLAs. No production data.</p></li>
    <li data-step="1"><h4>Schema and policy</h4><p>Apply <code>SUPPORT</code> DDL, row access, least-privilege roles, and deterministic tool gateway.</p></li>
    <li data-step="2"><h4>Retrieval and UI</h4><p>Publish approved articles, add citations, build the chat widget with explicit action confirmation.</p></li>
    <li data-step="3"><h4>Human console</h4><p>Queue, redacted context, SLA, resolution, and access logging for the support team.</p></li>
    <li data-step="4"><h4>Red team and pilot</h4><p>Golden set, adversarial suite, 20-person pilot, accessibility review, then expand channels and languages.</p></li>
  </ol>
  <p><strong>Reference implementation:</strong> <code>poc/support_agent.py</code> contains the
  situation catalog, deterministic router, tool allowlist, human gates, PII redaction, and
  audit event. Tests: <code>python3 -m unittest poc/test_support_agent.py -v</code>.
  Full design: <code>docs/SUPPORT_AGENT_INTEGRATION.md</code>; DDL:
  <code>sql/support/01_support_agent.sql</code>.</p>
</section>

<section id="decisions">
  <div class="section-kicker">Decisions requested</div>
  <h2>What the board needs to settle</h2>
  <ol>
    <li>Phase-1 situation set and which situations are human-only from day one.</li>
    <li>Channels: web help only, or also email/chat/Slack.</li>
    <li>Cortex-hosted model vs. approved external LLM and its data boundary.</li>
    <li>KB ownership, review cadence, and support hours/SLAs per queue.</li>
    <li>Transcript retention and whether the agent may send a fresh challenge.</li>
    <li>Languages, accessibility requirements, and works council/union review.</li>
  </ol>
  <div class="callout ok"><strong>Status</strong>
    Design only. No chat endpoint, model call, support tool, or production transcript is
    enabled in the current demo. The next step is catalog and KB approval, not a pilot.</div>
</section>
"""
    page("support-agent.html", "Support agent", header, content, [
        ("warning", "Scope gate"), ("why", "Why"), ("situations", "Situation catalog"),
        ("architecture", "Architecture"), ("guardrails", "Guardrails"), ("tools", "Tool contracts"),
        ("rbac", "RBAC"), ("evaluation", "Quality"), ("rollout", "Rollout"),
        ("decisions", "Decisions requested"),
    ])


# --------------------------------------------------------------------------
# Risk analysis
# --------------------------------------------------------------------------
def build_risk():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Phase 3</p>
  <h1>Contract risk analysis</h1>
  <p class="lede">CUAD's annotated clause categories feed a transparent, rule-based risk
  rubric. Rules are data, so the board can inspect and adjust them.</p>
</div></section>"""

    content = """
<section id="disclaimer">
  <div class="callout danger"><strong>Simulated legal review</strong>
    This rubric is a demonstration of analytics mechanics, not legal advice. It encodes a
    plausible but simplified set of review criteria and must be labeled as simulated
    everywhere it appears.</div>
</section>

<section id="clauses">
  <div class="section-kicker">Inputs</div>
  <h2>Clause categories used</h2>
  <p>A subset of CUAD's <strong>actual 41 categories</strong> carries the contract-risk story.
  Weights are stored as data, not hard-coded.</p>
  <div class="callout warn"><strong>Corrected against the real dataset</strong>
    CUAD v1 has <em>no</em> "Indemnification" or "Limitation of Liability" category. Liability
    exposure is expressed as <code>Uncapped Liability</code> / <code>Cap On Liability</code>.
    The rubric below uses CUAD's real category names (see <a href="poc.html#findings">findings</a>).</div>
  <div class="table-scroll"><table>
    <thead><tr><th>CUAD clause category</th><th>Risk theme</th><th>Weight</th></tr></thead>
    <tbody>
      <tr><td>Uncapped Liability</td><td>Uncapped exposure present</td><td><span class="badge high">High</span></td></tr>
      <tr><td>Cap On Liability <em>(absent)</em></td><td>No cap on liability</td><td><span class="badge high">High</span></td></tr>
      <tr><td>Termination For Convenience</td><td>Counterparty may exit at will</td><td><span class="badge med">Medium</span></td></tr>
      <tr><td>Anti-Assignment</td><td>Assignment restricted</td><td><span class="badge med">Medium</span></td></tr>
      <tr><td>Change Of Control</td><td>Ownership-change trigger</td><td><span class="badge med">Medium</span></td></tr>
      <tr><td>Minimum Commitment</td><td>Minimum purchase/volume</td><td><span class="badge med">Medium</span></td></tr>
      <tr><td>Governing Law <em>(absent)</em></td><td>No forum specified</td><td><span class="badge med">Medium</span></td></tr>
      <tr><td>Non-Compete / Exclusivity</td><td>Restrictive scope</td><td><span class="badge low">Low</span></td></tr>
      <tr><td>Renewal Term / Notice Period</td><td>Auto-renewal notice windows</td><td><span class="badge low">Low</span></td></tr>
    </tbody>
  </table></div>
</section>

<section id="rubric">
  <div class="section-kicker">Rubric</div>
  <h2>Rule-based scoring</h2>
  <p>Each rule evaluates an annotation (presence, absence, or a keyword signal) and
  contributes points. Scores roll up per contract and per matter.</p>
  <pre><code>CREATE TABLE core.ref_risk_rule (
  rule_id     STRING,
  clause_category STRING,
  signal      STRING,   -- PRESENT | ABSENT | KEYWORD
  pattern     STRING,
  points      INT,
  rationale   STRING
);

-- Examples
-- ('R1','Limitation of liability','ABSENT', NULL, 40,'No cap on liability')
-- ('R2','Indemnification','PRESENT', NULL, 25,'Indemnity present; review scope')
-- ('R3','Governing law','KEYWORD','foreign|arbitration', 10,'Offshore forum')</code></pre>
  <p>Risk bands: <span class="badge high">High &ge; 60</span>
  <span class="badge med">Medium 30&ndash;59</span>
  <span class="badge low">Low &lt; 30</span>.</p>
</section>

<section id="views">
  <div class="section-kicker">Outputs</div>
  <h2>Analytics views</h2>
  <pre><code>CREATE OR REPLACE VIEW marts.mart_matter_risk AS
SELECT m.matter_id, m.matter_name, c.contract_id, c.contract_type,
       SUM(CASE WHEN r.signal='ABSENT'  AND f.answer='No'  THEN r.points
                WHEN r.signal='PRESENT' AND f.answer='Yes' THEN r.points
                WHEN r.signal='KEYWORD' AND f.clause_text ILIKE '%'||r.pattern||'%'
                     THEN r.points ELSE 0 END) AS risk_score
FROM core.dim_matter m
JOIN core.bridge_matter_contract b USING (matter_id)
JOIN core.dim_contract c USING (contract_id)
JOIN core.fact_clause f ON f.contract_id = c.contract_id
JOIN core.ref_risk_rule r ON r.clause_category = f.clause_category
GROUP BY 1,2,3,4;</code></pre>
  <p>Because <code>dim_matter</code> and <code>fact_clause</code> carry
  <code>matter_id</code>, the same row access policy scopes these analytics &mdash; an
  attorney's risk report only covers their authorized matters.</p>
  <p>Full SQL: <code>sql/04_risk_views.sql</code>.</p>
</section>

<section id="sample">
  <div class="section-kicker">Illustration</div>
  <h2>Illustrative output</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Matter</th><th>Contract type</th><th>Score</th><th>Band</th><th>Driving clauses</th></tr></thead>
    <tbody>
      <tr><td>SYN-1042</td><td>Service Agreement</td><td>72</td><td><span class="badge high">High</span></td><td>No liability cap; broad indemnity</td></tr>
      <tr><td>SYN-1088</td><td>License Agreement</td><td>45</td><td><span class="badge med">Medium</span></td><td>Auto-renewal; assignment consent</td></tr>
      <tr><td>SYN-1103</td><td>NDA</td><td>18</td><td><span class="badge low">Low</span></td><td>Residuals clause</td></tr>
    </tbody>
  </table></div>
  <p class="disclaimer">Values are illustrative; the demo generates them from the loaded contracts.</p>
</section>
"""
    page("risk-analysis.html", "Risk analysis", header, content, [
        ("disclaimer", "Simulated review"), ("clauses", "Clause categories"),
        ("rubric", "Rule-based scoring"), ("views", "Analytics views"), ("sample", "Illustrative output"),
    ])


# --------------------------------------------------------------------------
# Audit & verification
# --------------------------------------------------------------------------
def build_audit():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Phase 4</p>
  <h1>Verify &amp; audit</h1>
  <p class="lede">The claim of governance is only credible if it is provable. We run the same
  queries under several roles and reconstruct what happened from Snowflake's own logs.</p>
</div></section>"""

    content = """
<section id="matrix">
  <div class="section-kicker">Test plan</div>
  <h2>Role &times; matter test matrix</h2>
  <p>For each role we run an identical query and record the row count and whether rows
  were filtered by policy.</p>
  <div class="table-scroll"><table>
    <thead><tr><th>Query</th><th>ATTORNEY (Matter A)</th><th>ATTORNEY (Matter B)</th><th>AUDITOR</th></tr></thead>
    <tbody>
      <tr><td>Select clauses for Matter A</td><td>Rows returned</td><td>0 rows (policy)</td><td>Rows returned</td></tr>
      <tr><td>Select clauses for Matter B</td><td>0 rows (policy)</td><td>Rows returned</td><td>Rows returned</td></tr>
      <tr><td>Select client contact email</td><td>Masked</td><td>Masked</td><td>Visible</td></tr>
      <tr><td>Read GOV audit views</td><td>Denied</td><td>Denied</td><td>Allowed</td></tr>
    </tbody>
  </table></div>
  <div class="callout"><strong>Key point</strong>
    A policy-filtered query returns <em>zero rows</em>, not an error. Verification therefore
    records row counts alongside the query ID, and confirms the policy is attached via
    <code>INFORMATION_SCHEMA.POLICY_REFERENCES</code>.</div>
</section>

<section id="evidence">
  <div class="section-kicker">Evidence</div>
  <h2>Where the proof comes from</h2>
  <ul>
    <li><code>SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY</code> &mdash; who ran what, as which role, and when (note: ~45 min latency).</li>
    <li><code>SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY</code> &mdash; which columns/tables were touched.</li>
    <li><code>INFORMATION_SCHEMA.POLICY_REFERENCES</code> &mdash; which policy is attached to which column/table.</li>
    <li><code>SNOWFLAKE.ACCOUNT_USAGE.ROW_ACCESS_POLICIES</code> &mdash; policy definitions in effect.</li>
  </ul>
  <pre><code>SELECT query_id, user_name, role_name, start_time, query_text
FROM snowflake.account_usage.query_history
WHERE role_name IN ('ATTORNEY','AUDITOR')
  AND query_text ILIKE '%fact_clause%'
ORDER BY start_time DESC;</code></pre>
  <p>Full queries: <code>sql/05_audit_queries.sql</code>.</p>
</section>

<section id="report">
  <div class="section-kicker">Deliverable</div>
  <h2>Unresolved high-risk clauses by authorized matter</h2>
  <p>The closing artifact of the demo: for the signed-in role, list high-risk clauses on
  the matters they are authorized to see, with the contract, clause category, and score.</p>
  <pre><code>SELECT matter_id, matter_name, contract_type, clause_category,
       risk_score, risk_band
FROM marts.mart_matter_risk
WHERE risk_band = 'High'
ORDER BY risk_score DESC;</code></pre>
  <p>Run as <code>ATTORNEY_A</code> and <code>ATTORNEY_B</code>, the same statement yields
  two different, correctly scoped reports &mdash; the single clearest demonstration of the wall.</p>
</section>

<section id="monitoring">
  <div class="section-kicker">Ongoing</div>
  <h2>Continuous governance</h2>
  <ul>
    <li>Alerts on policy changes (<code>POLICY_REFERENCES</code> diffs) and on unexpected role grants.</li>
    <li>A weekly access-review report listing authorizations expiring within 30 days.</li>
    <li>Row-access tests re-run on a schedule so regressions are caught, not hoped for.</li>
  </ul>
</section>
"""
    page("audit-verification.html", "Audit & verification", header, content, [
        ("matrix", "Test matrix"), ("evidence", "Evidence sources"),
        ("report", "High-risk report"), ("monitoring", "Continuous governance"),
    ])


# --------------------------------------------------------------------------
# Roadmap
# --------------------------------------------------------------------------
def build_roadmap():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Plan &amp; ownership</p>
  <h1>Roadmap, effort &amp; demo script</h1>
  <p class="lede">A short, bounded build with explicit owners, acceptance criteria, and the
  narrative we will run for the board.</p>
</div></section>"""

    content = """
<section id="plan">
  <div class="section-kicker">Schedule</div>
  <h2>Phased delivery</h2>
  <div class="callout ok"><strong>Approved &amp; in progress</strong>
    Plan approved 2026-10-15. Snowflake is simulated for now (no account). Phases 0&ndash;2 are working
    in the offline POC; phases 3&ndash;4 are being deepened now; the real trial-account build is deferred
    until an account is approved.</div>
  <ol class="timeline">
    <li data-step="0"><h4>Enablement <span class="badge low">done (simulated)</span></h4><p>Database/role DDL written; the simulated engine (<code>poc/snowflake_sim.py</code>) stands in for the account; this review site live on <code>main</code>.</p></li>
    <li data-step="1"><h4>Ingest &amp; organize <span class="badge low">done</span></h4><p>CUAD loader, synthetic generator, CORE model, and data-quality assertions implemented in the POC.</p></li>
    <li data-step="2"><h4>Confidentiality <span class="badge low">done (simulated)</span></h4><p>Roles, mapping, row access policy, and masking demonstrated offline; real policies on the trial later.</p></li>
    <li data-step="3"><h4>Risk analytics <span class="badge low">done (simulated)</span></h4><p>Rule engine (<code>poc/risk.py</code>), scoring, and a risk register in the demo (High 4 / Medium 19 / Low 7).</p></li>
    <li data-step="4"><h4>Verify &amp; audit <span class="badge low">done (simulated)</span></h4><p>Role × matter verification matrix and evidence pack; offline SQL harness + CI for the DDL.</p></li>
    <li data-step="5"><h4>Review <span class="badge low">signed off (simulated)</span></h4><p>Board reviewed the refreshed demo and signed off on the simulated phase 2026-10-15.</p></li>
  </ol>
</section>

<section id="owners">
  <div class="section-kicker">Team</div>
  <h2>Ownership</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Area</th><th>Owner</th><th>Responsibility</th></tr></thead>
    <tbody>
      <tr><td>Strategy &amp; board coordination</td><td>CEO</td><td>Scope, this site, review logistics</td></tr>
      <tr><td>Data pipeline &amp; SQL</td><td>Prototype (engineer)</td><td>CUAD loader, Faker, CORE/MARTS, risk views</td></tr>
      <tr><td>Snowflake platform &amp; security</td><td>Platform (devops)</td><td>Account, roles, policies, audit evidence</td></tr>
      <tr><td>Visual design</td><td>Design</td><td>Board-facing presentation and readability</td></tr>
      <tr><td>Site build</td><td>Frontend (engineer)</td><td>Interactive polish for the review site</td></tr>
    </tbody>
  </table></div>
</section>

<section id="risks">
  <div class="section-kicker">Risk</div>
  <h2>Risks &amp; mitigations</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Risk</th><th>Impact</th><th>Mitigation</th></tr></thead>
    <tbody>
      <tr><td>Demo mistaken for real client data</td><td><span class="badge high">High</span></td><td>Prominent synthetic labeling; CUAD attribution; disclaimer on every page</td></tr>
      <tr><td>Permissions overstatement (privilege)</td><td><span class="badge high">High</span></td><td>Explicit "public documents, fictional matters" framing</td></tr>
      <tr><td>Snowflake account not provisioned</td><td><span class="badge med">Medium</span></td><td>Phase 0 first; works on a trial account</td></tr>
      <tr><td>CUAD license misuse</td><td><span class="badge med">Medium</span></td><td>Retain CC BY 4.0 attribution and source link</td></tr>
      <tr><td>Row policy gaps via joins</td><td><span class="badge med">Medium</span></td><td>Attach policy to every <code>matter_id</code> table; verify with tests</td></tr>
      <tr><td>Cost creep if left running</td><td><span class="badge low">Low</span></td><td>X-Small + 60s auto-suspend; teardown guidance</td></tr>
    </tbody>
  </table></div>
</section>

<section id="script">
  <div class="section-kicker">Demo</div>
  <h2>Board demo script (~4 minutes)</h2>
  <ol>
    <li><strong>Frame.</strong> "Public contract data, fictional matters, simulated review criteria. What we're showing is governance, not legal advice."</li>
    <li><strong>Show the data.</strong> A CUAD contract, its annotated clauses, and the fictional matter it belongs to.</li>
    <li><strong>Log in as ATTORNEY_A.</strong> Run the matter query &mdash; see authorized matters. Query the other matter &mdash; <strong>zero rows</strong>. Show masked client email.</li>
    <li><strong>Switch to ATTORNEY_B.</strong> Same query, complementary result. The wall holds at query time.</li>
    <li><strong>Risk analytics.</strong> Show the high-risk register and the rubric behind the score.</li>
    <li><strong>Audit.</strong> Open query history for both roles; show the policy attached via <code>POLICY_REFERENCES</code>.</li>
    <li><strong>Ask.</strong> Confirm scope, data sourcing, account, and rubric framing.</li>
  </ol>
</section>

<section id="acceptance">
  <div class="section-kicker">Done</div>
  <h2>Definition of done</h2>
  <ul>
    <li>Site published at <a href="https://jpeckenpaugh.github.io/snow-compliance-demo/">jpeckenpaugh.github.io/snow-compliance-demo</a>.</li>
    <li>Snowflake behaviour rebuildable from <code>sql/</code> and demonstrable offline in the simulation.</li>
    <li>Cross-matter access denied and demonstrated for at least two attorney roles.</li>
    <li>Audit evidence captured and linked from the audit page.</li>
    <li>High-risk-by-matter report produced.</li>
    <li><em>Deferred:</em> real row access policies / masking validated on a Snowflake trial once an account is approved.</li>
  </ul>
</section>
"""
    page("roadmap.html", "Roadmap", header, content, [
        ("plan", "Phased delivery"), ("owners", "Ownership"), ("risks", "Risks & mitigations"),
        ("script", "Board demo script"), ("acceptance", "Definition of done"),
    ])


def build_poc():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Proof of concept</p>
  <h1>POC &amp; CUAD findings</h1>
  <p class="lede">We extracted a 30-document CUAD sample, examined its real shape against the
  original plan, and built a Python + SQLite proof of concept that maps directly to Snowflake.</p>
  <p style="margin-top:18px"><a href="demo/index.html" style="display:inline-block;background:#0d9488;color:#fff;font-weight:700;padding:11px 18px;border-radius:10px;text-decoration:none">Open the interactive demo &rarr;</a></p>
</div></section>"""

    content = """
<section id="built">
  <div class="section-kicker">What we built</div>
  <h2>Footwork in place</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Artifact</th><th>Path</th><th>Purpose</th></tr></thead>
    <tbody>
      <tr><td>CUAD extractor</td><td><code>poc/extract_cuad.py</code></td><td>Downloads CUAD, normalizes the first N docs, emits the shape report</td></tr>
      <tr><td>SQLite schema</td><td><code>poc/schema.sql</code></td><td>Mirrors the Snowflake model: dims, fact, bridge, authorization, audit</td></tr>
      <tr><td>Seeder</td><td><code>poc/seed.py</code></td><td>Loads 30 contracts + synthetic users/matters; exports the static demo data</td></tr>
      <tr><td>Risk engine</td><td><code>poc/risk.py</code></td><td>Shared, rule-based rubric (real CUAD categories); mirrors <code>sql/04</code></td></tr>
      <tr><td>Access layer</td><td><code>poc/access.py</code></td><td><strong>The enforcement point</strong> &mdash; authorization check + audit logging</td></tr>
      <tr><td>POC web server</td><td><code>poc/server.py</code></td><td>Standard-library HTTP server; real login, real denials, real audit</td></tr>
      <tr><td><strong>Simulated Snowflake</strong></td><td><code>poc/snowflake_sim.py</code></td><td>Emulates role context, row access policy, masking, query history, and a risk register offline (see <a href="snowflake-options.html">Snowflake options</a>)</td></tr>
      <tr><td>Offline SQL harness + CI</td><td><code>scripts/run_sql_offline.py</code>, <code>.github/workflows/ci.yml</code></td><td>Runs <code>sql/01…05</code> through fakesnow (DuckDB) in CI; reports supported vs. governance statements</td></tr>
      <tr><td>Static demo</td><td><code>demo/index.html</code></td><td>Board-clickable login/audit demo + Snowflake console + risk register, hosted on Pages</td></tr>
      <tr><td>Shape report</td><td><code>poc/analysis/cuad_shape_report.md</code></td><td>Full statistics over the 30-document sample</td></tr>
      <tr><td>Evidence pack</td><td><a href="https://github.com/jpeckenpaugh/snow-compliance-demo/blob/main/poc/analysis/evidence_pack.md"><code>poc/analysis/evidence_pack.md</code></a></td><td>Role × matter verification matrix (expected vs observed) with reproduction steps</td></tr>
    </tbody>
  </table></div>
  <pre><code>python3 poc/extract_cuad.py --limit 30   # fetch + normalize the sample
python3 poc/seed.py                      # build SQLite DB + demo data
python3 poc/build_demo.py                # regenerate the static Pages demo
python3 poc/server.py                    # functional POC at http://localhost:8000
python3 scripts/run_sql_offline.py       # run sql/01…05 offline via fakesnow (CI)</code></pre>
</section>

<section id="findings">
  <div class="section-kicker">Analysis</div>
  <h2>How the real data aligns with the plan</h2>
  <div class="kpis">
    <div class="kpi"><div class="n">30</div><div class="l">documents extracted</div></div>
    <div class="kpi"><div class="n">1,230</div><div class="l">annotations (30&times;41)</div></div>
    <div class="kpi"><div class="n">41</div><div class="l">clause categories</div></div>
    <div class="kpi"><div class="n">1&ndash;175k</div><div class="l">chars per contract</div></div>
  </div>
  <div class="table-scroll"><table>
    <thead><tr><th>Original plan assumed</th><th>CUAD actually provides</th><th>Change required</th></tr></thead>
    <tbody>
      <tr><td>510 contracts, 41 annotated categories</td><td>Confirmed (aok_v1.0)</td><td><span class="badge low">None</span></td></tr>
      <tr><td>A <code>contract_type</code> field</td><td>No such field; type is embedded in the title with <code>EX-10.x</code> noise</td><td><span class="badge med">Add title normalization</span></td></tr>
      <tr><td>A structured <code>parties</code> field</td><td>No parties field; parties are the "Parties" <em>clause annotation</em></td><td><span class="badge med">Model as annotation, not a column</span></td></tr>
      <tr><td>Clauses carry Yes/No answers</td><td>Extractive spans: <code>answers[{text, answer_start}]</code> + <code>is_impossible</code></td><td><span class="badge med">Derive presence from <code>is_impossible</code></span></td></tr>
      <tr><td>Clause text with start/end offsets</td><td>Only <code>answer_start</code>; end must be derived from the text length</td><td><span class="badge low">Derive end; store snippet</span></td></tr>
      <tr><td>Categories like Indemnification, Limitation of Liability, Confidentiality, Warranties</td><td>None of these exist; liability is <code>Uncapped Liability</code> / <code>Cap On Liability</code></td><td><span class="badge high">Remap the rubric</span></td></tr>
      <tr><td>Multiple paragraphs per document</td><td>One paragraph (the full contract) per document</td><td><span class="badge low">Simplifies ingestion</span></td></tr>
    </tbody>
  </table></div>
  <div class="callout danger"><strong>The headline finding</strong>
    Four clause categories named in the original brainstorm don't exist in CUAD. The risk rubric
    was remapped to real categories (<code>Uncapped Liability</code>, <code>Cap On Liability</code>,
    <code>Termination For Convenience</code>, <code>Anti-Assignment</code>, <code>Change Of Control</code>,
    <code>Minimum Commitment</code>, <code>Governing Law</code>, <code>Non-Compete</code>, <code>Exclusivity</code>).</div>
</section>

<section id="mapping">
  <div class="section-kicker">Path to Snowflake</div>
  <h2>How the POC maps to the warehouse</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>POC (SQLite / Python)</th><th>Snowflake target</th></tr></thead>
    <tbody>
      <tr><td><code>dim_*</code>, <code>fact_clause</code>, <code>bridge_matter_contract</code></td><td>Same tables under <code>CORE</code> (<code>sql/02_data_model.sql</code>)</td></tr>
      <tr><td><code>access.py</code> authorization check</td><td>Row access policy over <code>matter_authorization</code> (<code>sql/03</code>)</td></tr>
      <tr><td>PII masking in the query path</td><td>Masking policies + classification tags</td></tr>
      <tr><td><code>audit_log</code> table</td><td>Append-only audit table <em>and</em> <code>QUERY_HISTORY</code> / <code>ACCESS_HISTORY</code></td></tr>
      <tr><td>Risk scoring in <code>seed.py</code></td><td><code>CORE.ref_risk_rule</code> + <code>MARTS.mart_matter_risk</code> (<code>sql/04</code>)</td></tr>
      <tr><td>POC web server</td><td>Not needed &mdash; enforcement moves into the warehouse; any BI/UI reads governed tables</td></tr>
    </tbody>
  </table></div>
</section>

<section id="demo">
  <div class="section-kicker">Interactive</div>
  <h2>Try the access-control demo</h2>
  <p>Sign in as <strong>alice</strong>, <strong>bob</strong>, or <strong>carol</strong> (attorneys/paralegal)
  to see only your matters, request a document outside your matters to watch the denial get recorded,
  then sign in as <strong>admin</strong> to read the audit log of who accessed which files.</p>
  <p><a href="demo/index.html">Open the interactive demo &rarr;</a></p>
  <div class="callout"><strong>Simulated vs. functional</strong>
    The hosted demo simulates the model in the browser so it runs on static Pages. The SQLite POC
    enforces it for real server-side; both share the same authorization map and denial semantics.</div>
</section>
"""
    page("poc.html", "POC & findings", header, content, [
        ("built", "What we built"), ("findings", "Alignment with the plan"),
        ("mapping", "Path to Snowflake"), ("demo", "Try the demo"),
    ])


def build_options():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Snowflake options</p>
  <h1>Simulating Snowflake offline &amp; sandbox accounts</h1>
  <p class="lede">Per board direction, the Snowflake component is simulated for now. Here are the
  offline tooling and sandbox-account options, and our recommendation.</p>
</div></section>"""

    content = """
<section id="bottom-line">
  <div class="section-kicker">Bottom line</div>
  <h2>There is no true offline Snowflake</h2>
  <p>Snowflake is a hosted service; nothing runs the real engine locally. What exists falls into two
  buckets: <strong>emulators</strong> that accept Snowflake SQL/drivers but do <em>not</em> implement
  governance, and a <strong>free trial account</strong> that is the genuine article. Because the whole
  point of this demo is <em>governance</em> (row access policies, masking, audit), the emulators can carry
  the SQL while a simulation layer or a trial account carries the behaviour.</p>
  <div class="callout ok"><strong>Recommendation</strong>
    Proceed now with our own simulation layer (<code>poc/snowflake_sim.py</code>) for governance behaviour
    and use an emulator only for SQL/DDL portability and CI. When the board approves, validate the same
    <code>sql/01…05</code> unchanged on a free 30-day Snowflake trial.</div>
</section>

<section id="offline">
  <div class="section-kicker">Offline / local</div>
  <h2>Offline emulation options</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Option</th><th>What it is</th><th>Governance?</th><th>Best for</th></tr></thead>
    <tbody>
      <tr><td><strong>fakesnow</strong> <span class="tag">Apache-2.0</span></td>
        <td>Patches the Snowflake Python connector (or runs an HTTP server) and executes against DuckDB, translating SQL with sqlglot. Persists to disk.</td>
        <td><span class="badge high">No</span> row access / masking</td>
        <td>Running our DDL/scripts locally; SQL portability; CI</td></tr>
      <tr><td><strong>LocalStack for Snowflake</strong></td>
        <td>Managed, Docker-based Snowflake-compatible endpoint; works with the Snowflake CLI (<code>snow</code>). Free Hobby tier for non-commercial use.</td>
        <td><span class="badge med">Partial</span></td>
        <td>Driver/CLI compatibility, local dev</td></tr>
      <tr><td><strong>snowflake-emulator</strong> <span class="tag">MIT · Rust</span></td>
        <td>DataFusion-backed engine speaking the Snowflake SQL API v2; Docker image.</td>
        <td><span class="badge high">No</span> (GRANT/REVOKE are no-ops)</td>
        <td>Driver/SQL compatibility testing</td></tr>
      <tr><td><strong>DuckDB</strong> <span class="tag">MIT</span></td>
        <td>The analytical engine underneath fakesnow; excellent local SQL.</td>
        <td><span class="badge high">No</span></td>
        <td>Local analytics on the CORE/MARTS layer</td></tr>
      <tr><td><strong>dbt-duckdb</strong></td>
        <td>Runs the transformation layer (RAW &rarr; CORE &rarr; MARTS) offline; swap the adapter to <code>dbt-snowflake</code> later.</td>
        <td><span class="badge high">No</span></td>
        <td>Portable modeling / tests</td></tr>
      <tr><td><strong>Snowpark local testing framework</strong> <span class="tag">official</span></td>
        <td>Emulates Snowpark Python DataFrames locally without a connection.</td>
        <td><span class="badge high">No</span></td>
        <td>Unit-testing Snowpark DataFrame code</td></tr>
    </tbody>
  </table></div>
  <div class="callout warn"><strong>The catch</strong>
    Every emulator above explicitly omits access control. They can prove our SQL <em>runs</em>; they cannot
    prove a matter wall <em>holds</em>. That is exactly why we built the simulation layer.</div>
</section>

<section id="sandbox">
  <div class="section-kicker">Sandbox account</div>
  <h2>Free trial / sandbox account</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Option</th><th>What you get</th><th>Limits</th></tr></thead>
    <tbody>
      <tr><td><strong>Snowflake 30-day trial</strong></td>
        <td>$400 in free credits; <strong>Enterprise Edition</strong> features incl. <em>row access policies</em> and <em>dynamic data masking</em>; no credit card required; AWS/Azure/GCP + region choice; sample data preloaded.</td>
        <td>30 days or until credits run out; external network access, hybrid tables, Openflow limited; AI features off without a card; account suspended at end.</td></tr>
      <tr><td><strong>AWS Marketplace trial</strong></td>
        <td>Equivalent $400 / 30-day Snowflake offer through AWS Marketplace.</td>
        <td>Same as above; some AWS infra costs may apply.</td></tr>
    </tbody>
  </table></div>
  <p>Our footprint is tiny (30 contracts, X-Small warehouses, 60-second auto-suspend), so $400 of credits is
  far more than the demo needs. The trial is the only faithful way to validate row access policies and masking
  end-to-end.</p>
</section>

<section id="plan">
  <div class="section-kicker">Plan</div>
  <h2>How we'll simulate now, validate later</h2>
  <ol class="timeline">
    <li data-step="1"><h4>Now &mdash; govern in simulation</h4>
      <p><code>poc/snowflake_sim.py</code> emulates role context, the row access policy, masking, and query
      history offline. Demonstrated in the <a href="demo/index.html">interactive demo</a>'s Snowflake console.</p></li>
    <li data-step="2"><h4>Now &mdash; prove SQL portability</h4>
      <p>Run <code>sql/01…05</code> through fakesnow (or LocalStack) to catch syntax/portability issues in CI,
      and optionally model MARTS with dbt-duckdb.</p></li>
    <li data-step="3"><h4>When approved &mdash; validate for real</h4>
      <p>Stand up the 30-day trial, run the same DDL unchanged, and capture real
      <code>QUERY_HISTORY</code> / <code>POLICY_REFERENCES</code> evidence.</p></li>
  </ol>
</section>
"""
    page("snowflake-options.html", "Snowflake options", header, content, [
        ("bottom-line", "Bottom line"), ("offline", "Offline emulation"),
        ("sandbox", "Trial / sandbox account"), ("plan", "Simulate now, validate later"),
    ])


def build_full_dataset():
    header = """<section class="hero"><div class="wrap">
  <p class="eyebrow">Approved 2026-10-16 &middot; Full dataset</p>
  <h1>Full-dataset CUAD &rarr; Snowflake plan</h1>
  <p class="lede">Scale the demo from a 30-contract sample to all <strong>510 CUAD contracts / 20,910
  clause annotations</strong>, normalize them inside Snowflake with no API, generate the simulated
  RBAC + risk metadata, and put a Streamlit-in-Snowflake app in front of it.</p>
  <div class="pills">
    <span class="pill">510 contracts</span>
    <span class="pill">Normalized in SQL, no API</span>
    <span class="pill">510 matters (1:1)</span>
    <span class="pill">Streamlit in Snowflake</span>
  </div>
</div></section>"""

    content = """
<section id="summary">
  <div class="section-kicker">Recommendation</div>
  <h2>Proceed in three gated phases, all inside Snowflake</h2>
  <p class="lead">The repository already contains the hard parts (DDL, access model, risk rubric, offline
  POC). What changes for the full dataset is <strong>scale</strong> and the requirement that the walkthrough
  be runnable by hand in Snowsight. The board approved the full-dataset scope and methodology on 2026-10-16.</p>
  <div class="kpis">
    <div class="kpi"><div class="n">510</div><div class="l">contracts (30 today)</div></div>
    <div class="kpi"><div class="n">20,910</div><div class="l">clause annotations (6,702 present)</div></div>
    <div class="kpi"><div class="n">~27 MB</div><div class="l">full contract text</div></div>
    <div class="kpi"><div class="n">249 &rarr; 18</div><div class="l">raw contract types &rarr; controlled vocabulary</div></div>
  </div>
  <ol>
    <li><strong>Parse &amp; normalize inside Snowflake.</strong> Load the CUAD JSON into a <code>VARIANT</code>
      table, then flatten it with <code>LATERAL FLATTEN</code> in SQL. No external pipeline, no API.</li>
    <li><strong>Generate simulated RBAC + risk metadata at scale.</strong> One matter per contract (510),
      SQL-generated synthetic layer, role buckets + <code>matter_access_map</code>, row access policy,
      masking, and the 9-rule simulated rubric.</li>
    <li><strong>Web app on Streamlit in Snowflake.</strong> It runs as the caller's role, so RBAC + row
      access policies apply with no separate login store. External portal (with External OAuth) is a later step.</li>
  </ol>
</section>

<section id="state">
  <div class="section-kicker">Today vs. target</div>
  <h2>Gap analysis: 30-doc demo to full dataset</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Area</th><th>Demo core</th><th>Full dataset</th><th>Action</th></tr></thead>
    <tbody>
      <tr><td>Ingestion</td><td><code>extract_cuad.py --limit 30</code></td><td>510 docs, ~40 MB JSON</td><td>Add <code>VARIANT</code> load + SQL flatten</td></tr>
      <tr><td><code>contract_type</code></td><td>25 inferred types</td><td>249 noisy strings</td><td><code>CORE.ref_contract_type</code> map</td></tr>
      <tr><td>Matter graph</td><td>5 matters, 6 contracts each</td><td>510 matters (1:1)</td><td>Scale synthetic generator</td></tr>
      <tr><td>Roles</td><td>ATTORNEY_0/1, PARALEGAL&hellip;</td><td>same model, more buckets</td><td>Add ATTORNEY_0/1/2</td></tr>
      <tr><td>Full text</td><td>snippets only</td><td>~27 MB available</td><td>Store full text</td></tr>
      <tr><td>Risk register</td><td>9 rules, 5 matters</td><td>9 rules, 510 matters</td><td>Re-tune bands on distribution</td></tr>
    </tbody>
  </table></div>
</section>

<section id="phase1">
  <div class="section-kicker">Phase 1</div>
  <h2>Parse &amp; normalize the full CUAD dataset</h2>
  <p>Snowflake caps a single <code>VARIANT</code> value at ~16 MB, and the master file is ~40 MB, so it is
  split into one document per line (NDJSON) for <em>transport only</em> &mdash; all parsing and normalization
  runs in SQL. The runbook has the copy-paste steps.</p>
  <pre><code>-- 1. stage the NDJSON and land it (one document per row)
COPY INTO RAW.raw_cuad_json (src, source_file)
FROM (SELECT $1, METADATA$FILENAME FROM @RAW.cuad_stage)
FILE_FORMAT = RAW.json_ff PATTERN = '.*cuad_docs.*';

-- 2. normalize in SQL with LATERAL FLATTEN
CREATE OR REPLACE TABLE RAW.raw_cuad_contracts AS
SELECT 'CUAD-' || LPAD(src:ord::string, 4, '0') AS contract_id,
       src:title::string                        AS contract_name,
       UPPER(TRIM(SPLIT_PART(src:title::string,'-',-1))) AS contract_type,
       src:paragraphs[0]:context::string        AS contract_text
FROM RAW.raw_cuad_json;</code></pre>
  <div class="callout ok"><strong>Data-quality gates</strong>
    510 contracts &middot; 20,910 annotations &middot; 6,702 present &middot; 41 categories &middot; 0 orphaned clauses.
    All measured against the real <code>CUADv1.json</code>.</div>
  <p>Assets: <code>ingest/split_cuad_json.py</code> (NDJSON split), <code>sql/full_dataset/06_full_dataset.sql</code>
  (consolidated DDL), and <code>docs/SNOWFLAKE_WALKTHROUGH.md</code> (the manual runbook).</p>
</section>

<section id="phase2">
  <div class="section-kicker">Phase 2</div>
  <h2>Simulated RBAC + risk metadata</h2>
  <p>One matter per contract (510 matters). Everything synthetic is prefixed <code>SYNTHETIC</code> and
  generated deterministically in SQL &mdash; no external generator required.</p>
  <div class="table-scroll"><table>
    <thead><tr><th>Control</th><th>Where</th></tr></thead>
    <tbody>
      <tr><td>Access decision is data, not code</td><td><code>SECURITY.matter_access_map(role_name, matter_id, &hellip;)</code></td></tr>
      <tr><td>Matter wall</td><td><code>SECURITY.matter_access_policy</code> attached to every <code>matter_id</code> object</td></tr>
      <tr><td>PII protection</td><td><code>SECURITY.pii_mask</code> + <code>data_classification</code> tags</td></tr>
      <tr><td>Risk rubric</td><td><code>CORE.ref_risk_rule</code> &rarr; <code>MARTS.mart_matter_risk</code> (simulated)</td></tr>
    </tbody>
  </table></div>
</section>

<section id="phase3">
  <div class="section-kicker">Phase 3</div>
  <h2>Web application &mdash; Streamlit in Snowflake first</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Option</th><th>Auth / login</th><th>Governance</th><th>Verdict</th></tr></thead>
    <tbody>
      <tr><td><strong>Streamlit in Snowflake</strong></td><td>Snowflake SSO/MFA; app runs as caller's role</td><td><span class="badge low">Inherits</span> RBAC + row access + masking</td><td><strong>Recommended first</strong></td></tr>
      <tr><td>External portal</td><td>Build login/SSO + session&rarr;role mapping</td><td><span class="badge med">Duplicates</span> unless External OAuth</td><td>Later, if a standalone portal is required</td></tr>
      <tr><td>Snowpark Container Services / Native App</td><td>Snowflake auth</td><td><span class="badge low">Inherits</span></td><td>Overkill for the demo</td></tr>
    </tbody>
  </table></div>
  <p>Admin/auditability: native <code>QUERY_HISTORY</code> / <code>ACCESS_HISTORY</code> / <code>LOGIN_HISTORY</code>
  and <code>POLICY_REFERENCES</code> for data touches, plus an app-level audit table for UI actions mirroring
  <code>poc/access.py</code>.</p>
</section>

<section id="decisions">
  <div class="section-kicker">Approved 2026-10-16</div>
  <h2>Board decisions</h2>
  <div class="callout ok"><strong>Approved</strong>
    The board approved the full-dataset scope and all six methodology decisions below.</div>
  <div class="table-scroll"><table>
    <thead><tr><th>Decision</th><th>Resolution</th></tr></thead>
    <tbody>
      <tr><td>Snowflake account</td><td><span class="badge low">New trial account</span> (Enterprise)</td></tr>
      <tr><td>Normalization location</td><td><span class="badge low">In-Snowflake <code>VARIANT</code> + SQL</span></td></tr>
      <tr><td>Synthetic scale</td><td><span class="badge low">510 matters (1:1)</span></td></tr>
      <tr><td>Full contract text</td><td><span class="badge low">Store full text</span> (~27 MB)</td></tr>
      <tr><td>Web app approach</td><td><span class="badge low">Streamlit in Snowflake</span> first</td></tr>
      <tr><td>Publish this roadmap</td><td><span class="badge low">This page</span></td></tr>
    </tbody>
  </table></div>
</section>

<section id="risks">
  <div class="section-kicker">Risk</div>
  <h2>Risks &amp; mitigations</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Risk</th><th>Impact</th><th>Mitigation</th></tr></thead>
    <tbody>
      <tr><td>Manual steps drift from <code>sql/*.sql</code></td><td><span class="badge med">Medium</span></td><td>Runbook embeds the same DDL; keep files authoritative</td></tr>
      <tr><td><code>contract_type</code> noise (249 types)</td><td><span class="badge med">Medium</span></td><td>Controlled-vocabulary map; report unmapped as <code>Other</code></td></tr>
      <tr><td>Unstable <code>contract_id</code> across loads</td><td><span class="badge med">Medium</span></td><td>Derive from the NDJSON ordinal; document load order</td></tr>
      <tr><td>Row-policy gaps via joins</td><td><span class="badge high">High</span></td><td>Attach policy to every <code>matter_id</code> object; run the verification matrix</td></tr>
      <tr><td>Demo mistaken for real client data</td><td><span class="badge high">High</span></td><td><code>SYNTHETIC</code> prefixes + CUAD CC BY 4.0 attribution + disclaimers</td></tr>
      <tr><td>External app weakens governance</td><td><span class="badge high">High</span></td><td>Prefer Streamlit in Snowflake; if external, mandate External OAuth + per-user role</td></tr>
    </tbody>
  </table></div>
</section>

<section id="runbook">
  <div class="section-kicker">Do it</div>
  <h2>Walk it through</h2>
  <p>The full step-by-step runbook (load &rarr; normalize &rarr; synthetic layer &rarr; RBAC &rarr; risk &rarr; verify &rarr; teardown)
  is <code>docs/SNOWFLAKE_WALKTHROUGH.md</code>, with the consolidated SQL in
  <code>sql/full_dataset/06_full_dataset.sql</code>. It needs only a Snowflake trial account and Snowsight &mdash; no API.</p>
  <pre><code># transport shaping only (one JSON document per line)
python3 ingest/split_cuad_json.py --json CUADv1.json --out build/cuad_docs.jsonl
# then: upload to @RAW.cuad_stage and run sql/full_dataset/06_full_dataset.sql</code></pre>
</section>
"""
    page("full-dataset.html", "Full-dataset plan", header, content, [
        ("summary", "Recommendation"), ("state", "Gap analysis"), ("phase1", "Phase 1: normalize"),
        ("phase2", "Phase 2: RBAC & risk"), ("phase3", "Phase 3: web app"),
        ("decisions", "Approved decisions"), ("risks", "Risks"), ("runbook", "Walk it through"),
    ])


if __name__ == "__main__":
    build_index()
    build_data()
    build_architecture()
    build_security()
    build_identity()
    build_support()
    build_risk()
    build_audit()
    build_roadmap()
    build_poc()
    build_options()
    build_full_dataset()
    print("site build complete")
