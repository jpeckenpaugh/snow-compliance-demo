# Full-dataset CUAD → Snowflake — Report & Recommendation

Status: **approved 2026-10-16** · Owner: CEO office · Companion runbook:
[SNOWFLAKE_WALKTHROUGH.md](SNOWFLAKE_WALKTHROUGH.md) · Prior plan: [PLAN.md](PLAN.md)

## 1. The request

Load the **full CUAD dataset** into Snowflake — not via an API, but as a
documented, hands-on walkthrough a person can follow inside Snowflake. Then:

1. **Parse & normalize** the full CUAD source (as it exists today) into Snowflake.
2. Generate the **simulated RBAC and risk metadata**.
3. Discuss a **web application** that sources from Snowflake with user
   access/logins and basic admin/auditability.

Deliverable for this issue: a report/recommendation on how to proceed.

## 2. Executive summary

**Recommendation: proceed, in three gated phases, keeping everything inside
Snowflake and driven from worksheets — no external API, no separate ingestion
service.** The existing repository already contains the hard parts (DDL, access
model, risk rubric, an offline POC). What changes for the *full* dataset is
**scale** (510 contracts, 20,910 clause annotations) and the fact that the
walkthrough must be runnable by hand.

Headline calls:

1. **Normalize inside Snowflake.** Load `CUADv1.json` once into a `VARIANT`
   column, then parse it with `LATERAL FLATTEN` in SQL. This makes "parsing and
   normalizing into Snowflake" literally true and removes any dependency on a
   Python pipeline. (A pre-normalized CSV path stays available as fallback.)
2. **Keep CUAD + synthetic split.** CUAD is the factual spine; clients, matters,
   people, and authorizations are generated, deterministic, and obviously
   fictional.
3. **Scale matters to the dataset.** One matter per contract (510 matters), so
   the matter wall and risk register are exercised at realistic cardinality.
4. **Build the web app on Streamlit in Snowflake first.** It inherits Snowflake
   RBAC + row access policies natively, so no separate login system is needed
   for phase 3. An external portal is a later, deliberate step.
5. **Everything is verifiable with Snowflake's own metadata** — no bespoke
   audit stack required for the data layer.

Full-dataset numbers measured from `poc/.cuad_work/CUADv1.json`:

| Fact | Full dataset | Demo core today |
| --- | --- | --- |
| Contracts | **510** | 30 |
| Clause categories / doc | **41** | 41 |
| Clause annotations | **20,910** | 1,230 |
| Annotations present (Yes) | **6,702** | ~420 |
| Full text volume | **~27 MB** (median 33 KB/doc, max 338 KB) | ~0.9 MB |
| Distinct inferred `contract_type` | **249** (noisy) | 25 |

## 3. Where we are today

| Asset | State |
| --- | --- |
| `sql/01…05*.sql` | Snowflake DDL: database/roles, data model, row access + masking, risk views, audit queries. Idempotent, intended to run unchanged on a trial. |
| `ingest/load_cuad.py` | Parses CUAD JSON → RAW CSVs (a sample-oriented path). |
| `ingest/generate_synthetic_data.py` | Faker generator for the fictional law-firm layer (deterministic seed). |
| `poc/` | Working Python + SQLite POC (auth, enforcement point `access.py`, risk rubric `risk.py`, offline Snowflake simulator). |
| `poc/analysis/` | CUAD shape report (30 docs) + evidence pack (25/25 access-matrix cells pass). |
| `docs/OFFLINE_SQL.md` | fakesnow portability harness + CI gate (45 ok / 46 known-unsupported / 0 fail). |
| Site | Board-review site published from `main` (GitHub Pages). |

**Key constraint already recorded:** the Snowflake component is *simulated* until
a real trial account exists. Offline emulators run the SQL but do **not** enforce
row access policies or masking, so they cannot prove the matter wall.

## 4. Gap analysis: 30-doc demo → full dataset

| Area | Demo core | Full dataset | Action needed |
| --- | --- | --- | --- |
| Ingestion | `extract_cuad.py --limit 30` | 510 docs, 40 MB JSON | Add an in-Snowflake `VARIANT` load + flatten path. |
| `contract_type` | inferred from title (25 types) | 249 noisy distinct strings | Add a normalization/classification map (`ref_contract_type`). |
| Matter graph | 5 matters, 6 contracts each | 510 matters (1:1) | Scale synthetic generator + authorizations. |
| Roles | ATTORNEY_0/1, PARALEGAL, … | same model | Add more attorney buckets so the wall is non-trivial at scale. |
| Full text | snippets only | 27 MB available | Decide: store full text (recommended) vs snippets. |
| Risk register | 9 rules, 5 matters | 9 rules, 510 matters | Re-tune band thresholds against the real distribution. |
| Verification | 25-cell matrix | role × 510 matters | Sample matters + aggregate row-count checks. |

Nothing in the gap requires new architecture — it is scale, one normalization
table, and a documented manual path.

## 5. Recommended target architecture

Unchanged from `PLAN.md` §4 (database `SNOW_COMPLIANCE_DEMO`; schemas `RAW`,
`CORE`, `MARTS`, `SECURITY`, `GOV`; X-Small warehouses with 60 s auto-suspend),
with one addition for the full dataset:

- `RAW.raw_cuad_json` — single `VARIANT` table holding the raw CUAD document
  (the artifact the user loads by hand). Everything downstream is derived from
  it with SQL, so the "parse and normalize" step is visible and inspectable.
- `CORE.ref_contract_type` — a small mapping table that collapses the 249 noisy
  title-derived types into a controlled vocabulary.

## 6. Phase 1 — Parse & normalize the full CUAD dataset (recommended)

**Outcome:** `CUADv1.json` loaded into `RAW.raw_cuad_json`, then normalized by SQL
into `RAW.raw_cuad_contracts` (510 rows) and `RAW.raw_cuad_clauses` (20,910 rows),
with `CORE` dimensions built from them.

**Approach (recommended): SQL `VARIANT` flatten.**
1. Upload `CUADv1.json` to an internal stage with the Snowsight **Load Data**
   wizard (or `PUT` from SnowSQL — still a client, not the Snowflake API).
2. `COPY INTO RAW.raw_cuad_json (src) FILE_FORMAT = (TYPE = JSON);`
3. Normalize with `LATERAL FLATTEN` over `src:data[*].paragraphs[0].qas[*]`,
   deriving `contract_id` from the stable `FLATTEN` `INDEX`, `contract_type`
   from the title, `answer` from `is_impossible`, and `char_start/char_end` from
   `answer_start` + text length.
4. Build `CORE.dim_contract`, `CORE.dim_clause_category`, `CORE.fact_clause`.

Exact, copy-paste SQL is in the runbook
[SNOWFLAKE_WALKTHROUGH.md](SNOWFLAKE_WALKTHROUGH.md) §3–§5.

**Why this over the existing Python path:** it satisfies "rather than the API,
documentation to walk through the steps in Snowflake," it is fully auditable in
`QUERY_HISTORY`, and it keeps one source of truth. The Python path remains as a
fallback and for the offline POC.

**Data-quality gates (must pass before phase 2):**
- `SELECT COUNT(*) FROM RAW.raw_cuad_contracts;` → **510**
- `SELECT COUNT(*) FROM RAW.raw_cuad_clauses;` → **20,910**
- `SELECT COUNT(*) FROM RAW.raw_cuad_clauses WHERE answer='Yes';` → **6,702**
- Zero orphaned clauses; 41 distinct clause categories.

## 7. Phase 2 — Simulated RBAC + risk metadata

**Outcome:** the synthetic law-firm layer plus the governed access map and risk
rubric, at full scale.

- **RBAC / synthetic layer:** generate clients, employees, matters (510),
  `matter_authorization`, `matter_assignment`, `contract_attachment`, and
  `access_approval`. Recommended: a SQL-only `TABLE(GENERATOR(ROWCOUNT => 510))`
  seed so it runs in-worksheet (runbook §6), with the existing Faker CSV path as
  an alternative. Every record is prefixed `SYNTHETIC`.
- **Role buckets:** map employees into `ATTORNEY_0…N`, `PARALEGAL`,
  `COMPLIANCE_ADMIN`, `AUDITOR`; build `SECURITY.matter_access_map(role_name,
  matter_id, access_level, valid_from, valid_to)`. The access decision stays
  **data**, not code.
- **Row access policy + masking** (`sql/03`): attach `matter_access_policy` to
  every `matter_id` table; mask client PII by role; tag sensitive columns.
- **Risk metadata** (`sql/04`): `CORE.ref_risk_rule` (9 transparent rules over
  CUAD's real categories), `MARTS.mart_matter_risk`,
  `MARTS.mart_high_risk_register`. Re-tune bands (High ≥ 60 / Medium 30–59 /
  Low < 30) against the 510-contract distribution and label it **simulated**.

**Acceptance:** an `ATTORNEY_k` role sees rows only for its matters; a
cross-matter query returns 0 rows; PII is masked for non-oversight roles;
`AUDITOR` reads `GOV` views that attorneys cannot.

## 8. Phase 3 — Web application sourcing from Snowflake

**Recommendation: build on Streamlit in Snowflake (SiS) first.**

| Option | Auth / login | Governance | Effort | Verdict |
| --- | --- | --- | --- | --- |
| **Streamlit in Snowflake** | Snowflake SSO/MFA; the app runs as the caller's role | **Inherits** RBAC + row access + masking automatically | Low (days) | **Recommended first** |
| External portal (Python/React + connector) | Must build login/SSO, session→role mapping | Duplicates Snowflake governance unless OAuth is used | High (weeks) | Later, if a standalone portal is required |
| Snowpark Container Services / Native App | Snowflake auth | Inherits governance | Medium–High | Overkill for the demo |

If/when an **external portal** is required, the correct pattern is:
- **Snowflake External OAuth / SSO** so the app passes the *user's* identity, and
- a **dedicated app service role** for the connection, with per-request role via
  session context, plus `CURRENT_USER`/session tags for attribution, and
- an **app-level `audit_log`** for UI actions (login, open, deny) mirroring
  `poc/access.py`, alongside Snowflake's native `QUERY_HISTORY` /
  `ACCESS_HISTORY` / `LOGIN_HISTORY` for data touches.

**Admin/auditability (either option):**
- Data-level audit: `SNOWFLAKE.ACCOUNT_USAGE.{QUERY_HISTORY, ACCESS_HISTORY,
  LOGIN_HISTORY}`, `INFORMATION_SCHEMA.POLICY_REFERENCES` (`sql/05`).
- Access administration: grant/revoke is a change to `matter_access_map`
  (governed by `COMPLIANCE_ADMIN`), with an approval record — matches the
  `access_approval` table and the POC's seeded audit history.
- Add a **session policy** (idle timeout, MFA), a **network policy**, and
  object **tags** for classification.

## 9. Cross-cutting concerns

- **Licensing/provenance:** CUAD is CC BY 4.0 — retain attribution in
  `source_file` and on any UI. Keep the public/fictional framing prominent.
- **Cost:** X-Small warehouses, `AUTO_SUSPEND=60`, `INITIALLY_SUSPENDED=TRUE`.
  27 MB of text and 20,910 rows are trivial; a free 30-day Enterprise trial
  ($400 credits) is ample.
- **Secrets:** credentials live in Paperclip secrets, never in the repo.
- **Reproducibility:** keep a copy of `CUADv1.json` hash in the load log.

## 10. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Manual steps drift from `sql/*.sql` | Medium | Runbook embeds the same DDL; keep files the source of truth. |
| `contract_type` noise (249 types) | Medium | `CORE.ref_contract_type` normalization map; report unmapped. |
| Unstable `contract_id` across loads | Medium | Derive from `FLATTEN` `INDEX`; document load order. |
| Row-policy gaps via joins | High | Attach policy to every `matter_id` object; run the verification matrix. |
| Demo mistaken for real client data | High | `SYNTHETIC` prefixes everywhere + attribution + disclaimers. |
| Risk rubric read as legal advice | Medium | Label **simulated**; keep rules transparent data. |
| External app weakens governance | High | Prefer SiS; if external, mandate OAuth + per-user role. |

## 11. Suggested sequence & effort

| Phase | Deliverable | Effort | Gate |
| --- | --- | --- | --- |
| 0 | Trial account (Enterprise), DDL applied | 0.5 day | Account approved |
| 1 | Full CUAD normalized in Snowflake + DQ gates pass | 1–2 days | 510 / 20,910 / 6,702 |
| 2 | Full synthetic RBAC + risk metadata enforcing | 1 day | Wall matrix passes |
| 3a | Streamlit-in-Snowflake app (login via SSO, doc view, admin/audit) | 3–5 days | Demo walkthrough |
| 3b | (Optional) External portal with OAuth | 2–3 weeks | Only if required |

## 12. Decisions (approved 2026-10-16)

1. **Account** — **new isolated Snowflake trial (Enterprise)** account. ✅
2. **Normalization location** — **in-Snowflake `VARIANT` flatten**. ✅
3. **Synthetic scale** — **1 matter per contract (510)**. ✅
4. **Full text storage** — **store the full contract text** (~27 MB). ✅
5. **Web app approach** — **Streamlit in Snowflake** first. ✅
6. **Publishing** — roadmap published as the **Full-dataset plan** page. ✅
