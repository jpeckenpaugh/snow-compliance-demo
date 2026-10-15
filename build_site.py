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
    ("risk-analysis.html", "Risk analysis"),
    ("audit-verification.html", "Audit"),
    ("poc.html", "POC & findings"),
    ("demo/index.html", "Interactive demo"),
    ("snowflake-options.html", "Snowflake options"),
    ("roadmap.html", "Roadmap"),
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
    <span class="pill">Public research data only</span>
    <span class="pill">No real client or privileged material</span>
    <span class="pill">Reproducible SQL, no hidden steps</span>
    <span class="pill">Staged here for review</span>
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
  <p class="lead">The board asked for a simple login experience, an examination of the first 20 CUAD
  documents, and Python scaffolding adaptable to Snowflake. All three are done and staged here.</p>
  <div class="cards">
    <div class="card"><h3>Interactive demo</h3><p>Sign in as a hypothetical attorney and see only your
      documents; sign in as admin to review who accessed which files. <a href="demo/index.html">Open the demo &rarr;</a></p></div>
    <div class="card"><h3>Python + SQLite POC</h3><p>A real enforcement layer (<code>poc/access.py</code>)
      with a governed query path, a web server, and a functional audit log. <a href="poc.html">POC &amp; CUAD findings &rarr;</a></p></div>
    <div class="card"><h3>First 20 CUAD documents</h3><p>Extracted and analyzed. Two assumptions in the
      original plan needed correcting. <a href="poc.html#findings">See the findings &rarr;</a></p></div>
  </div>
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
  <div class="section-kicker">Ask</div>
  <h2>What we need from the board</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Decision</th><th>Options</th><th>Our recommendation</th></tr></thead>
    <tbody>
      <tr><td>Scope of the demo</td><td>4-phase flow as written / narrower / broader</td><td>Build all four phases against 20&ndash;30 contracts</td></tr>
      <tr><td>Data sourcing</td><td>CUAD + synthetic / synthetic only</td><td>CUAD + synthetic, with full attribution</td></tr>
      <tr><td>Snowflake account</td><td>New trial / existing account</td><td>Isolated demo account, X-Small warehouses</td></tr>
      <tr><td>Hosting of this review site</td><td>This Pages repo / other</td><td>Continue here on <code>main</code></td></tr>
      <tr><td>Risk rubric framing</td><td>Simulated / none</td><td>Simulated and prominently disclaimed</td></tr>
    </tbody>
  </table></div>
</section>
"""
    page("index.html", "Overview", header, content, [
        ("purpose", "Purpose"), ("outcomes", "Outcomes"), ("poc", "Working POC & demo"),
        ("why", "Why CUAD"), ("architecture-at-a-glance", "Architecture at a glance"),
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
  <ol class="timeline">
    <li data-step="0"><h4>Enablement &middot; Platform</h4><p>Snowflake demo account, database/role DDL, secrets wired, this review site live on <code>main</code>.</p></li>
    <li data-step="1"><h4>Ingest &amp; organize &middot; Prototype</h4><p>CUAD loader, Faker generator, CORE model, data-quality assertions. <em>Accept:</em> all FK checks pass.</p></li>
    <li data-step="2"><h4>Confidentiality &middot; Platform + Prototype</h4><p>Roles, mapping table, row access policy on every <code>matter_id</code> table, masking. <em>Accept:</em> cross-matter query returns 0 rows.</p></li>
    <li data-step="3"><h4>Risk analytics &middot; Prototype</h4><p>Risk-rule table, scoring view, high-risk register. <em>Accept:</em> bands render for loaded contracts.</p></li>
    <li data-step="4"><h4>Verify &amp; audit &middot; Platform</h4><p>Multi-role test run, query-history evidence capture, GOV views. <em>Accept:</em> evidence pack produced.</p></li>
    <li data-step="5"><h4>Review &middot; CEO + Design</h4><p>Publish refreshed site, walk the demo, collect board decisions.</p></li>
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
    <li>Snowflake demo rebuildable end-to-end from <code>sql/</code> + <code>ingest/</code>.</li>
    <li>Cross-matter access denied and demonstrated for at least two attorney roles.</li>
    <li>Audit evidence captured and linked from the audit page.</li>
    <li>High-risk-by-matter report produced.</li>
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
  <p class="lede">We extracted the first 20 CUAD documents, examined their real shape against the
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
      <tr><td>Seeder</td><td><code>poc/seed.py</code></td><td>Loads 20 contracts + synthetic users/matters; exports the static demo data</td></tr>
      <tr><td>Access layer</td><td><code>poc/access.py</code></td><td><strong>The enforcement point</strong> &mdash; authorization check + audit logging</td></tr>
      <tr><td>POC web server</td><td><code>poc/server.py</code></td><td>Standard-library HTTP server; real login, real denials, real audit</td></tr>
      <tr><td><strong>Simulated Snowflake</strong></td><td><code>poc/snowflake_sim.py</code></td><td>Emulates role context, row access policy, masking, and query history offline (see <a href="snowflake-options.html">Snowflake options</a>)</td></tr>
      <tr><td>Static demo</td><td><code>demo/index.html</code></td><td>Board-clickable login/audit demo + Snowflake console, hosted on Pages</td></tr>
      <tr><td>Shape report</td><td><code>poc/analysis/cuad_shape_report.md</code></td><td>Full statistics over the 20-document sample</td></tr>
    </tbody>
  </table></div>
  <pre><code>python3 poc/extract_cuad.py --limit 20   # fetch + normalize first 20 docs
python3 poc/seed.py                      # build SQLite DB + demo data
python3 poc/build_demo.py                # regenerate the static Pages demo
python3 poc/server.py                    # functional POC at http://localhost:8000</code></pre>
</section>

<section id="findings">
  <div class="section-kicker">Analysis</div>
  <h2>How the real data aligns with the plan</h2>
  <div class="kpis">
    <div class="kpi"><div class="n">20</div><div class="l">documents extracted</div></div>
    <div class="kpi"><div class="n">820</div><div class="l">annotations (20&times;41)</div></div>
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
  <p>Our footprint is tiny (20 contracts, X-Small warehouses, 60-second auto-suspend), so $400 of credits is
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


if __name__ == "__main__":
    build_index()
    build_data()
    build_architecture()
    build_security()
    build_risk()
    build_audit()
    build_roadmap()
    build_poc()
    build_options()
    print("site build complete")
