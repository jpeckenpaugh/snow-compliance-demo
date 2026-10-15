# Snowflake Compliance Demo — Recommendations & Build Plan

Status: **proposal for board review**
Owner: CEO office
Review surface: https://jpeckenpaugh.github.io/snow-compliance-demo/

## 1. Purpose

Produce a demonstrable Snowflake capability in a legal-services context that exercises
the features a compliance audience cares about: governed ingestion, matter-level
confidentiality, contract-risk analytics, and provable audit. Deliberately scoped to be
built and shown quickly.

## 2. Data sources

- **CUAD (Contract Understanding Atticus Dataset)** — 510 real commercial contracts,
  41 expert-annotated clause categories. Public research data under **CC BY 4.0**;
  attribution required. Used as the factual spine of the demo.
- **Synthetic law-firm layer (Python Faker)** — clients, matters, employees,
  assignments, authorizations, approvals. Deterministic (fixed seed), obviously
  fictional, no real personal data.

Non-negotiable framing: public documents, fictional matters, **simulated** legal-review
criteria. Never imply real privilege or real client confidentiality.

## 3. Recommendations (summary)

1. Use CUAD as the factual spine (20–30 contracts in the demo core; scale to 510 optional).
2. Synthesize the business layer, not the legal text.
3. Model **matters** as the confidentiality boundary; key every access decision on `matter_id`.
4. Enforce with **row access policies** over a mapping table, not application SQL.
5. Centralize policy in a `SECURITY` schema owned by a compliance role.
6. Mask sensitive metadata by role; classify with tags.
7. Keep the risk rubric transparent and data-driven; label it simulated.
8. Prove governance with Snowflake's own query/access history.
9. Ship the review site from this repo (Pages from `main`).
10. Keep costs near zero (X-Small, 60s auto-suspend).

## 4. Architecture

Database `SNOW_COMPLIANCE_DEMO` with schemas:

| Schema | Contents |
| --- | --- |
| `RAW` | Landing JSON/CSVs, no logic |
| `CORE` | Dimensions, `fact_clause`, bridges, `matter_authorization` |
| `MARTS` | Curated risk views for the demo |
| `SECURITY` | Row access policies, masks, `matter_access_map`, tags |
| `GOV` | Audit views over Snowflake metadata |

Warehouses: `WH_LOAD`, `WH_ANALYTICS` (both X-Small, auto-suspend 60s).

Roles: `DEMO_ADMIN`, `COMPLIANCE_ADMIN`, `ATTORNEY`, `PARALEGAL`, `AUDITOR`
(hierarchy under `SYSADMIN`; `ACCOUNTADMIN` never used for demo work).

## 5. Logical data model

```
client 1---* matter *---* contract (bridge: contract_attachment)
matter 1---* fact_clause *---1 contract
matter 1---* matter_authorization *---1 employee
matter 1---* matter_assignment   *---1 employee
contract 1---* fact_clause *---1 clause_category
```

DDL: `sql/02_data_model.sql`. Loaders: `ingest/load_cuad.py`,
`ingest/generate_synthetic_data.py`.

## 6. Phase 2 — Matter confidentiality

- `SECURITY.matter_access_map(role_name, matter_id, access_level, valid_from, valid_to)`.
- `SECURITY.matter_access_policy` row access policy attached to **every** table carrying
  `matter_id` (facts, dimensions, bridges).
- `SECURITY.pii_mask` masking policy on client PII; classification tags on sensitive columns.
- Production upgrade path: map by `employee_id` resolved from the session instead of role.

SQL: `sql/03_row_access_and_masking.sql`.

## 7. Phase 3 — Contract risk

- `CORE.ref_risk_rule` stores rubric rules as data (PRESENT / ABSENT / KEYWORD signals + points).
- `MARTS.mart_matter_risk` scores per matter/contract; `mart_high_risk_register` bands them.
- Bands: High ≥ 60, Medium 30–59, Low < 30. **Simulated**, not legal advice.

SQL: `sql/04_risk_views.sql`.

## 8. Phase 4 — Verify & audit

Test matrix (same query per role): authorized matter → rows; other matter → 0 rows;
PII → masked; GOV views → denied for attorneys, allowed for auditor.

Evidence sources: `QUERY_HISTORY`, `ACCESS_HISTORY`, `POLICY_REFERENCES`,
`ROW_ACCESS_POLICIES`. Record results in `GOV.access_verification`.
Close-out report: high-risk clauses by authorized matter, run per attorney role.

SQL: `sql/05_audit_queries.sql`.

## 9. Roadmap & ownership

| Phase | Owner | Acceptance |
| --- | --- | --- |
| 0 Enablement | Platform | Account, DDL applied, site live |
| 1 Ingest & organize | Prototype | All FK checks pass |
| 2 Confidentiality | Platform + Prototype | Cross-matter query returns 0 rows |
| 3 Risk analytics | Prototype | Bands render for loaded contracts |
| 4 Verify & audit | Platform | Evidence pack produced |
| 5 Board review | CEO + Design | Site refreshed, decisions captured |

## 10. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Demo mistaken for real client data | High | Synthetic labeling + attribution + disclaimer |
| Permissions overstatement | High | Explicit public/fictional framing |
| Snowflake account not provisioned | Medium | Phase 0 first; trial works |
| CUAD license misuse | Medium | Retain CC BY 4.0 attribution |
| Row-policy gaps via joins | Medium | Attach to every `matter_id` table; test |
| Cost creep | Low | X-Small + auto-suspend |

## 11. Board decisions requested

1. Scope: full four-phase flow vs. narrower.
2. Data sourcing: CUAD + synthetic (recommended) vs. synthetic only.
3. Snowflake account: new isolated demo account vs. existing.
4. Review hosting: continue on this Pages repo.
5. Risk-rubric framing: simulated (recommended) vs. omit.
