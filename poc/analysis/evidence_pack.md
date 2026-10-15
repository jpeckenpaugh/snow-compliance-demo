# Evidence pack — POC verification matrix

_Generated 2026-10-15 from the Python + SQLite POC in `poc/` (phase 3 risk analytics +
phase 4 verify & audit). Provenance: CUAD v1 (`CUADv1.json`, CC BY 4.0) + a synthetic
law-firm layer. The Snowflake component is **simulated** (`poc/snowflake_sim.py`); the
governance behaviour below is enforced by the same logic that ports to Snowflake row
access policies and masking policies in `sql/03_row_access_and_masking.sql`._

## 1. Sample under test

| Fact | Value |
| --- | --- |
| Documents extracted | **30** of 510 CUAD contracts (`poc/data/cuad_sample.json`) |
| Clause categories per document | **41** (CUAD-wide: 41) |
| Total clause annotations | **1,230** |
| Matters | 5 (`SYN-1001` … `SYN-1005`), **6 contracts each** (round-robin) |
| Risk bands | High **4**, Medium **19**, Low **7** |
| Users / roles | `alice` ATTORNEY_ALICE, `bob` ATTORNEY_BOB, `carol` PARALEGAL_CAROL, `admin` COMPLIANCE_ADMIN, `auditor` AUDITOR |

Authorization map (source of truth: `matter_authorization` in `poc/schema.sql`, seeded by
`poc/seed.py`):

| User | Authorized matters |
| --- | --- |
| alice (ATTORNEY_ALICE) | SYN-1001, SYN-1003, SYN-1005 |
| bob (ATTORNEY_BOB) | SYN-1002, SYN-1003, SYN-1004 |
| carol (PARALEGAL_CAROL) | SYN-1001, SYN-1002, SYN-1005 |
| admin (COMPLIANCE_ADMIN) | all (oversight) |
| auditor (AUDITOR) | all (oversight) |

## 2. Matrix A — role × matter document visibility (row access policy)

Same query per role: `SELECT matter_id, matter_name, contract_id, contract_type
FROM marts.v_matter_documents;` (simulated row access policy on `matter_id`). Expected per
cell: **ROWS (6)** when the role is authorized for the matter or is an oversight role;
**ZERO_ROWS (0)** otherwise.

| Role | SYN-1001 | SYN-1002 | SYN-1003 | SYN-1004 | SYN-1005 |
| --- | --- | --- | --- | --- | --- |
| ATTORNEY_ALICE | ROWS (6) | ZERO_ROWS (0) | ROWS (6) | ZERO_ROWS (0) | ROWS (6) |
| ATTORNEY_BOB | ZERO_ROWS (0) | ROWS (6) | ROWS (6) | ROWS (6) | ZERO_ROWS (0) |
| PARALEGAL_CAROL | ROWS (6) | ROWS (6) | ZERO_ROWS (0) | ZERO_ROWS (0) | ROWS (6) |
| COMPLIANCE_ADMIN | ROWS (6) | ROWS (6) | ROWS (6) | ROWS (6) | ROWS (6) |
| AUDITOR | ROWS (6) | ROWS (6) | ROWS (6) | ROWS (6) | ROWS (6) |

**Result: 25/25 cells match expectation** (no cross-matter leakage, no oversight
under-exposure).

Cross-matter denial through the application enforcement point (`poc/access.py`, the same
rule the row access policy encodes):

| Attempt | Expected | Observed |
| --- | --- | --- |
| bob opens `CUAD-0000` (matter SYN-1001) | DENIED + audit row | `Denied: not authorized for this matter`, `view_document` recorded as `denied` |
| alice opens `CUAD-0000` (matter SYN-1001) | ALLOWED | allowed, 41 clause rows returned |

## 3. Matrix B — policy behaviour by role and statement

Every statement logged to `query_history` (`poc/snowflake_sim.py`, mirrors
`SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY`). Observed on a freshly seeded database in the
order documents → clauses → risk_register → clients → query_history.

| Role | documents (rows) | clauses (rows) | risk_register (rows) | client PII | query_history |
| --- | --- | --- | --- | --- | --- |
| ATTORNEY_ALICE | 18 / exp. 18 | 194 | 18 / exp. 18 | **MASKED** | **DENIED** |
| ATTORNEY_BOB | 18 / exp. 18 | 201 | 18 / exp. 18 | **MASKED** | **DENIED** |
| PARALEGAL_CAROL | 18 / exp. 18 | 221 | 18 / exp. 18 | **MASKED** | **DENIED** |
| COMPLIANCE_ADMIN | 30 / exp. 30 | 342 | 30 / exp. 30 | plain | SUCCESS (19 rows) |
| AUDITOR | 30 / exp. 30 | 342 | 30 / exp. 30 | plain | SUCCESS (24 rows) |

- Row counts for `clauses` differ by role because the clause fact is filtered by the set of
  authorized matters (194 + 201 + 221 ≠ 342: the three attorneys' union is the full set,
  with SYN-1003 clauses counted for alice and bob).
- **MASKED** = `contact_email` and `contact_phone` returned as `***REDACTED***` for the
  masked roles (`sec.pii_mask`); oversight roles see the (synthetic) values.
- **DENIED** = `insufficient privileges to operate on view 'QUERY_HISTORY'`, and the denied
  attempt is itself written to query history.
- The `query_history` row counts grow as statements are executed (each run is logged), so
  they are order-dependent by design.

## 4. Risk register detail (phase 3 → phase 4 close-out)

`risk_register` resolves per-matter high-risk clauses from the shared rubric
(`poc/risk.py`, mirrors `CORE.ref_risk_rule` in `sql/04_risk_views.sql`). Bands:
High ≥ 60, Medium 30–59, Low < 30. High-band contracts observed:

| Matter | Matter name | Contract | Type | Score | High-risk clauses (drivers) |
| --- | --- | --- | --- | --- | --- |
| SYN-1004 | Vector strategic alliances | CUAD-0008 | 10.2_PROMOTION AGREEMENT | 90 | Uncapped liability, Termination for convenience, Anti-assignment, Change of control, Minimum commitment, Restrictive covenant |
| SYN-1005 | Cedar employment & endorsement | CUAD-0009 | A_R STRATEGIC LICENSING… | 80 | Uncapped liability, Termination for convenience, Anti-assignment, Change of control, Restrictive covenant |
| SYN-1002 | Helios licensing & supply | CUAD-0001 | PROMOTION AND DISTRIBUTION AGREEMENT | 60 | Uncapped liability, Anti-assignment, Change of control |
| SYN-1002 | Helios licensing & supply | CUAD-0016 | 10.18_SUPPLY AGREEMENT | 60 | Uncapped liability, Anti-assignment, Change of control |

Because the register is itself subject to the row access policy, each role sees only the
high-risk clauses for matters it may access (e.g. carol sees SYN-1005 but not SYN-1004).

## 5. Reproduction steps

```bash
# from the repository root
python3 poc/extract_cuad.py --limit 30   # CUAD -> poc/data/cuad_sample.json (+ shape report)
python3 poc/seed.py                      # SQLite POC DB + demo/demo_data.json
python3 poc/build_demo.py                # regenerate demo/index.html

# functional POC server (optional): http://localhost:8000
python3 poc/server.py                    # users: alice, bob, carol, admin, auditor / demo
```

To reproduce the matrices, run the simulator across roles:

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, "poc")
import sqlite3, snowflake_sim as sf
con = sqlite3.connect("poc/db/poc.db")
for role in sf.list_roles():
    for key in ("documents", "clauses", "risk_register", "clients", "query_history"):
        r = sf.run(con, role, key)
        print(role, key, r["status"], len(r["rows"]))
PY
```

The board-facing static demo (`demo/index.html`, rebuilt by `poc/build_demo.py`) is the
browser analogue: the **Snowflake console** tab runs `documents`, `clauses`,
`risk_register`, `clients`, and `query_history` per role, the **Risk register** tab renders
the per-matter register, the document viewer shows real CUAD clause snippets, and the
**Audit log** supports filters by user, action, and outcome.

## 6. Findings & limitations

- Governance behaviour is consistent and reproducible across all five roles and all five
  matters; the enforcement rule is defined once (`poc/access.py`, `poc/risk.py`) and shared
  by the functional POC, the simulator, and the static demo.
- The Snowflake deliverable remains **simulated** for now (no account). The real DDL lives
  in `sql/*.sql` and is intended to run unchanged on a Snowflake trial; offline emulators
  run the SQL but do **not** enforce access control, so they cannot replace this matrix — a
  trial is the faithful end-to-end validation.
- The risk rubric is **simulated** and is not legal advice. It encodes nine transparent
  rules over CUAD's actual clause categories.
