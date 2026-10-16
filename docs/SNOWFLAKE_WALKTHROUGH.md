# Snowflake Walkthrough — Full CUAD dataset, by hand

A step-by-step, copy-paste runbook to load and normalize the **full CUAD dataset**
(510 contracts, 20,910 clause annotations) into Snowflake, generate the simulated
**RBAC + risk metadata**, and verify the matter wall — **without the Snowflake
API**. Everything below runs in **Snowsight worksheets** (plus one `PUT` from a
client). Companion report: [FULL_DATASET_ROADMAP.md](FULL_DATASET_ROADMAP.md).

- **Source of truth for DDL:** [`sql/01…05`](../sql). This runbook embeds the same
  statements so you can follow it end to end; keep the files authoritative.
- **Account:** a free 30-day **Enterprise** trial (row access policies + masking
  require Enterprise). Use an isolated demo account.
- **Cost:** X-Small warehouses with `AUTO_SUSPEND = 60`; idle cost ≈ 0.

Legend: 🖱️ = Snowsight action · ⌨️ = client shell (SnowSQL/terminal) · 🧾 = run in a
worksheet.

---

## 0. Get the source file (local, one-time)

CUAD ships as `data.zip`; the master file is `CUADv1.json` (`aok_v1.0`, CC BY 4.0).

```bash
# If you don't already have it:
curl -L -o data.zip https://github.com/The-Atticus-Project/cuad/raw/main/data.zip
unzip -o data.zip CUADv1.json
```

> **Why a small local step:** a single Snowflake `VARIANT` value is capped at
> ~16 MB, and `CUADv1.json` is ~40 MB. Split it into one JSON object per line
> (NDJSON) so each document loads as its own row. This is **transport shaping
> only** — all parsing/normalization still happens in SQL inside Snowflake.

```bash
python3 - <<'PY'
import json
docs = json.load(open("CUADv1.json"))["data"]
with open("cuad_docs.jsonl", "w") as fh:
    for i, d in enumerate(docs):
        # carry only what we normalize: an ordinal + title + paragraphs
        fh.write(json.dumps({"ord": i, "title": d.get("title"),
                             "paragraphs": d.get("paragraphs")}) + "\n")
print("wrote cuad_docs.jsonl")
PY
```

Expected: 510 lines. (This is the same as
[`ingest/split_cuad_json.py`](../ingest/split_cuad_json.py) — run
`python3 ingest/split_cuad_json.py --json CUADv1.json --out build/cuad_docs.jsonl`.)
Attribution is retained in `source_file` columns below.

---

## 1. Phase 0 — database, warehouses, roles

🧾 Run as `ACCOUNTADMIN` (or a role with `CREATE`/`GRANT`):

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS SNOW_COMPLIANCE_DEMO;
CREATE SCHEMA IF NOT EXISTS SNOW_COMPLIANCE_DEMO.RAW;
CREATE SCHEMA IF NOT EXISTS SNOW_COMPLIANCE_DEMO.CORE;
CREATE SCHEMA IF NOT EXISTS SNOW_COMPLIANCE_DEMO.MARTS;
CREATE SCHEMA IF NOT EXISTS SNOW_COMPLIANCE_DEMO.SECURITY;
CREATE SCHEMA IF NOT EXISTS SNOW_COMPLIANCE_DEMO.GOV;

CREATE WAREHOUSE IF NOT EXISTS WH_LOAD
  WAREHOUSE_SIZE='XSMALL' AUTO_SUSPEND=60 AUTO_RESUME=TRUE INITIALLY_SUSPENDED=TRUE;
CREATE WAREHOUSE IF NOT EXISTS WH_ANALYTICS
  WAREHOUSE_SIZE='XSMALL' AUTO_SUSPEND=60 AUTO_RESUME=TRUE INITIALLY_SUSPENDED=TRUE;

-- Build / governance roles
CREATE ROLE IF NOT EXISTS DEMO_ADMIN;
CREATE ROLE IF NOT EXISTS COMPLIANCE_ADMIN;
CREATE ROLE IF NOT EXISTS AUDITOR;
CREATE ROLE IF NOT EXISTS ATTORNEY;   -- parent of the attorney buckets
CREATE ROLE IF NOT EXISTS PARALEGAL;

GRANT ROLE DEMO_ADMIN       TO ROLE SYSADMIN;
GRANT ROLE COMPLIANCE_ADMIN TO ROLE SYSADMIN;
GRANT ROLE AUDITOR          TO ROLE SYSADMIN;
GRANT ROLE ATTORNEY         TO ROLE COMPLIANCE_ADMIN;
GRANT ROLE PARALEGAL        TO ROLE ATTORNEY;

-- Attorney buckets used by the row access policy at full scale
CREATE ROLE IF NOT EXISTS ATTORNEY_0;
CREATE ROLE IF NOT EXISTS ATTORNEY_1;
CREATE ROLE IF NOT EXISTS ATTORNEY_2;
GRANT ROLE ATTORNEY_0 TO ROLE ATTORNEY;
GRANT ROLE ATTORNEY_1 TO ROLE ATTORNEY;
GRANT ROLE ATTORNEY_2 TO ROLE ATTORNEY;

GRANT USAGE ON DATABASE SNOW_COMPLIANCE_DEMO TO ROLE DEMO_ADMIN;
GRANT USAGE ON DATABASE SNOW_COMPLIANCE_DEMO TO ROLE COMPLIANCE_ADMIN;
GRANT USAGE ON DATABASE SNOW_COMPLIANCE_DEMO TO ROLE ATTORNEY;
GRANT USAGE ON DATABASE SNOW_COMPLIANCE_DEMO TO ROLE PARALEGAL;
GRANT USAGE ON DATABASE SNOW_COMPLIANCE_DEMO TO ROLE AUDITOR;

GRANT USAGE ON WAREHOUSE WH_ANALYTICS TO ROLE ATTORNEY_0;
GRANT USAGE ON WAREHOUSE WH_ANALYTICS TO ROLE ATTORNEY_1;
GRANT USAGE ON WAREHOUSE WH_ANALYTICS TO ROLE ATTORNEY_2;
GRANT USAGE ON WAREHOUSE WH_ANALYTICS TO ROLE PARALEGAL;
GRANT USAGE ON WAREHOUSE WH_ANALYTICS TO ROLE AUDITOR;

GRANT ALL  ON SCHEMA SNOW_COMPLIANCE_DEMO.RAW      TO ROLE DEMO_ADMIN;
GRANT ALL  ON SCHEMA SNOW_COMPLIANCE_DEMO.CORE     TO ROLE DEMO_ADMIN;
GRANT ALL  ON SCHEMA SNOW_COMPLIANCE_DEMO.MARTS    TO ROLE DEMO_ADMIN;
GRANT ALL  ON SCHEMA SNOW_COMPLIANCE_DEMO.SECURITY TO ROLE COMPLIANCE_ADMIN;
GRANT USAGE ON SCHEMA SNOW_COMPLIANCE_DEMO.CORE     TO ROLE ATTORNEY;
GRANT USAGE ON SCHEMA SNOW_COMPLIANCE_DEMO.MARTS    TO ROLE ATTORNEY;
GRANT USAGE ON SCHEMA SNOW_COMPLIANCE_DEMO.GOV      TO ROLE AUDITOR;
```

> This mirrors `sql/01_database_and_roles.sql` with the addition of the
> `ATTORNEY_0/1/2` buckets. When the plan is approved, fold those additions back
> into `sql/01` so the offline harness (`scripts/run_sql_offline.py`) covers them.

---

## 2. Load the raw CUAD JSON (transport only)

🧾 Create the stage and the landing table:

```sql
USE ROLE DEMO_ADMIN;
USE DATABASE SNOW_COMPLIANCE_DEMO;
USE SCHEMA RAW;
USE WAREHOUSE WH_LOAD;

CREATE OR REPLACE FILE FORMAT RAW.json_ff TYPE = JSON;

CREATE OR REPLACE STAGE RAW.cuad_stage FILE_FORMAT = RAW.json_ff;

CREATE OR REPLACE TABLE RAW.raw_cuad_json (
  src         VARIANT,
  source_file STRING,
  loaded_at   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

⌨️ Upload `cuad_docs.jsonl` to the stage (No-API path: **SnowSQL `PUT`**, or the
Snowsight **Load Data → Stage files** wizard). With SnowSQL:

```bash
snowsql -a <account> -u <user> -d SNOW_COMPLIANCE_DEMO -s RAW \
  -q "PUT file://$PWD/cuad_docs.jsonl @RAW.cuad_stage AUTO_COMPRESS=TRUE;"
```

🧾 Load it (each line becomes one row):

```sql
COPY INTO RAW.raw_cuad_json (src, source_file)
FROM (SELECT $1, METADATA$FILENAME FROM @RAW.cuad_stage)
FILE_FORMAT = RAW.json_ff
PATTERN = '.*cuad_docs.*'
ON_ERROR = 'ABORT_STATEMENT';

SELECT COUNT(*) FROM RAW.raw_cuad_json;   -- expect 510
```

---

## 3. Normalize CUAD inside Snowflake (`LATERAL FLATTEN`)

🧾 Contracts (510 rows). `contract_type` is **not** a CUAD field — it is inferred
from the title (see §5 for cleanup):

```sql
CREATE OR REPLACE TABLE RAW.raw_cuad_contracts AS
SELECT
  'CUAD-' || LPAD(src:ord::string, 4, '0')                 AS contract_id,
  src:title::string                                        AS contract_name,
  UPPER(TRIM(SPLIT_PART(src:title::string, '-', -1)))      AS contract_type,
  src:paragraphs[0]:context::string                        AS contract_text,
  'The Atticus Project CUAD, CC BY 4.0'                    AS source_file,
  'aok_v1.0'                                               AS cuad_version,
  CURRENT_TIMESTAMP()                                      AS loaded_at
FROM RAW.raw_cuad_json;
```

🧾 Clause annotations (20,910 rows). Presence is derived from `is_impossible`;
`char_start`/`char_end` come from `answer_start` + text length:

```sql
CREATE OR REPLACE TABLE RAW.raw_cuad_clauses AS
SELECT
  'CUAD-' || LPAD(j.src:ord::string, 4, '0')                       AS contract_id,
  SPLIT_PART(q.value:id::string, '__', -1)                          AS clause_category,
  IFF(q.value:is_impossible::boolean = FALSE
        AND COALESCE(NULLIF(ARRAY_SIZE(q.value:answers), 0), 0) > 0,
      'Yes', 'No')                                                  AS answer,
  COALESCE(q.value:answers[0]:text::string, '')                     AS clause_text,
  TRY_TO_NUMBER(q.value:answers[0]:answer_start::string)            AS char_start,
  IFF(q.value:answers[0]:answer_start IS NOT NULL,
      TRY_TO_NUMBER(q.value:answers[0]:answer_start::string)
        + LENGTH(COALESCE(q.value:answers[0]:text::string, '')), NULL) AS char_end,
  CURRENT_TIMESTAMP()                                              AS loaded_at
FROM RAW.raw_cuad_json j,
LATERAL FLATTEN(input => j.src:paragraphs) p,
LATERAL FLATTEN(input => p.value:qas) q;
```

### Data-quality gates (all must pass before continuing)

```sql
SELECT COUNT(*) AS contracts             FROM RAW.raw_cuad_contracts;                -- 510
SELECT COUNT(*) AS annotations           FROM RAW.raw_cuad_clauses;                  -- 20910
SELECT COUNT(*) AS present               FROM RAW.raw_cuad_clauses WHERE answer='Yes'; -- 6702
SELECT COUNT(DISTINCT clause_category) AS categories
  FROM RAW.raw_cuad_clauses;                                                          -- 41
SELECT COUNT(*) AS orphaned
  FROM RAW.raw_cuad_clauses c
  LEFT JOIN RAW.raw_cuad_contracts k USING (contract_id)
  WHERE k.contract_id IS NULL;                                                        -- 0
```

---

## 4. Build the CORE model

🧾 Same as [`sql/02_data_model.sql`](../sql/02_data_model.sql) (dimensions,
bridges, `matter_authorization`, and the `fact_clause` that denormalizes
`matter_id` for the row access policy):

```sql
USE SCHEMA CORE;

CREATE OR REPLACE TABLE CORE.dim_contract AS
SELECT contract_id, contract_name, contract_type FROM RAW.raw_cuad_contracts;

CREATE OR REPLACE TABLE CORE.dim_clause_category AS
SELECT DISTINCT clause_category AS clause_category_id, clause_category
FROM RAW.raw_cuad_clauses;

-- (dim_client / dim_employee / dim_matter / bridges / matter_authorization are
--  built in §6 after the synthetic layer lands, then fact_clause is built here.)
```

---

## 5. Normalize `contract_type` (249 raw strings → controlled vocabulary)

🧾 CUAD titles are noisy (e.g. `10.16_SUPPLY AGREEMENT`, `A_R STRATEGIC
LICENSING…`). Collapse to a controlled vocabulary and keep the raw value:

```sql
CREATE OR REPLACE TABLE CORE.ref_contract_type AS
SELECT * FROM VALUES
  ('STRATEGIC ALLIANCE','Strategic Alliance Agreement'),
  ('SPONSORSHIP','Sponsorship Agreement'),
  ('BRANDING','Branding Agreement'),
  ('DISTRIBUTOR','Distributor Agreement'),
  ('OUTSOURCING','Outsourcing Agreement'),
  ('JOINT FILING','Joint Filing Agreement'),
  ('COOPERATION|COLLABORATION','Cooperation Agreement'),
  ('SUPPLY','Supply Agreement'),
  ('ENDORSEMENT|PROMOTION','Endorsement/Promotion Agreement'),
  ('CONSULTING|ADVISORY|SERVICE','Services Agreement'),
  ('LICENSE|LICENSING','License Agreement'),
  ('HOSTING','Hosting Agreement'),
  ('FRANCHISE','Franchise Agreement'),
  ('JOINT VENTURE','Joint Venture Agreement'),
  ('EMPLOYMENT','Employment Agreement'),
  ('LEASE','Lease Agreement'),
  ('LOAN|CREDIT','Finance Agreement'),
  ('SETTLEMENT','Settlement Agreement')
  AS t(pattern, contract_type);

CREATE OR REPLACE TABLE CORE.dim_contract_normalized AS
SELECT c.contract_id,
       c.contract_name,
       c.contract_type AS contract_type_raw,
       COALESCE(r.contract_type, 'Other') AS contract_type
FROM CORE.dim_contract c
LEFT JOIN CORE.ref_contract_type r
  ON REGEXP_LIKE(c.contract_type, r.pattern);

-- See what remains unmapped; extend the map until this list is acceptable.
SELECT contract_type_raw, COUNT(*) n
FROM CORE.dim_contract_normalized
WHERE contract_type = 'Other'
GROUP BY 1 ORDER BY n DESC;
```

---

## 6. Generate the simulated law-firm layer (RBAC + matters)

Everything here is **synthetic** and prefixed `SYNTHETIC`. This runs entirely in
a worksheet (`TABLE(GENERATOR(...))`). Clients and employees are fixed sets;
there is **one matter per contract (510 matters)**.

```sql
USE SCHEMA RAW;

CREATE OR REPLACE TABLE RAW.raw_synthetic_clients AS
WITH g AS (SELECT SEQ4()+1 AS n FROM TABLE(GENERATOR(ROWCOUNT => 8)))
SELECT 'CL-' || LPAD(n::string,3,'0')                                   AS client_id,
       'SYNTHETIC ' || (ARRAY_CONSTRUCT('Northwind Pharma','Helios Energy',
          'Blue Harbor Bank','Vector Robotics','Cedar Health','Orion Foods',
          'Atlas Logistics','Summit Media'))[MOD(n,8)]::string          AS client_name,
       (ARRAY_CONSTRUCT('Pharmaceuticals','Energy','Financial Services','Manufacturing',
          'Healthcare','Consumer','Logistics','Media'))[MOD(n,8)]::string AS industry,
       (ARRAY_CONSTRUCT('MA','TX','NY','CA','IL','GA','WA','CO'))[MOD(n,8)]::string AS region,
       'SYNTHETIC Contact ' || n::string                                 AS contact_name,
       'not.real+' || n::string || '@example.invalid'                    AS contact_email,
       '+1-555-01' || LPAD(n::string,2,'0')                              AS contact_phone
FROM g;

CREATE OR REPLACE TABLE RAW.raw_synthetic_employees AS
WITH g AS (SELECT SEQ4()+1 AS n FROM TABLE(GENERATOR(ROWCOUNT => 12)))
SELECT 'EMP-' || LPAD(n::string,3,'0')                                  AS employee_id,
       'SYNTHETIC Employee ' || n::string                               AS full_name,
       (ARRAY_CONSTRUCT('Partner','Counsel','Associate','Paralegal','Compliance Officer'))[MOD(n,5)]::string AS title,
       (ARRAY_CONSTRUCT('Corporate','Litigation','IP','Employment','Privacy','Real Estate'))[MOD(n,6)]::string AS practice,
       IFF(MOD(n,5) < 3, 'attorney', IFF(MOD(n,5)=3, 'paralegal', 'staff')) AS role,
       -- role bucket consumed by SECURITY.matter_access_map:
       CASE WHEN MOD(n,5) < 3 THEN 'ATTORNEY_' || MOD(n,5)::string
            WHEN MOD(n,5) = 3 THEN 'PARALEGAL'
            ELSE 'COMPLIANCE_ADMIN' END                                 AS demo_role
FROM g;

CREATE OR REPLACE TABLE RAW.raw_synthetic_matters AS
WITH g AS (SELECT SEQ4() AS n FROM TABLE(GENERATOR(ROWCOUNT => 510)))
SELECT 'SYN-' || (1000+n+1)::string                                    AS matter_id,
       'CL-' || LPAD((MOD(n,8)+1)::string,3,'0')                        AS client_id,
       'SYNTHETIC matter ' || (n+1)::string                             AS matter_name,
       (ARRAY_CONSTRUCT('Public','Confidential','Highly Confidential'))[MOD(n,3)]::string AS confidentiality_level,
       DATEADD('day', -1*MOD(n,900), CURRENT_DATE())                    AS opened_on,
       'EMP-' || LPAD((MOD(n,12)+1)::string,3,'0')                      AS lead_attorney_id
FROM g;

-- One contract per matter: matter SYN-1001+n  <->  CUAD-0000+n
CREATE OR REPLACE TABLE RAW.raw_synthetic_contract_attachment AS
WITH g AS (SELECT SEQ4() AS n FROM TABLE(GENERATOR(ROWCOUNT => 510)))
SELECT 'SYN-' || (1000+n+1)::string AS matter_id,
       'CUAD-' || LPAD(n::string,4,'0') AS contract_id,
       DATEADD('day', -1*MOD(n,900), CURRENT_DATE()) AS executed_on
FROM g;

-- Two authorized employees per matter (lead + a rotating second).
CREATE OR REPLACE TABLE RAW.raw_synthetic_matter_authorization AS
WITH g AS (SELECT SEQ4() AS n FROM TABLE(GENERATOR(ROWCOUNT => 510)))
SELECT 'SYN-' || (1000+n+1)::string AS matter_id,
       e.employee_id, 'READ' AS access_level,
       DATE '2024-01-01' AS valid_from, NULL::DATE AS valid_to
FROM g
JOIN RAW.raw_synthetic_employees e
  ON e.employee_id IN ('EMP-' || LPAD((MOD(n,12)+1)::string,3,'0'),
                       'EMP-' || LPAD((MOD(n+5,12)+1)::string,3,'0'));

CREATE OR REPLACE TABLE RAW.raw_synthetic_matter_assignment AS
SELECT matter_id, employee_id, 'lead' AS assignment_role
FROM RAW.raw_synthetic_matter_authorization
QUALIFY ROW_NUMBER() OVER (PARTITION BY matter_id ORDER BY employee_id) = 1;

CREATE OR REPLACE TABLE RAW.raw_synthetic_access_approval AS
SELECT a.matter_id, a.employee_id,
       m.lead_attorney_id AS approved_by,
       DATEADD('day', -30, CURRENT_DATE()) AS approved_on
FROM RAW.raw_synthetic_matter_authorization a
JOIN RAW.raw_synthetic_matters m USING (matter_id);
```

🧾 Build the CORE dimensions/bridges from these (extends `sql/02`):

```sql
USE SCHEMA CORE;
CREATE OR REPLACE TABLE CORE.dim_client AS
SELECT client_id, client_name, industry, region, contact_name, contact_email, contact_phone
FROM RAW.raw_synthetic_clients;
CREATE OR REPLACE TABLE CORE.dim_employee AS
SELECT employee_id, full_name, title, practice, role FROM RAW.raw_synthetic_employees;
CREATE OR REPLACE TABLE CORE.dim_matter AS
SELECT matter_id, client_id, matter_name, confidentiality_level, opened_on, lead_attorney_id
FROM RAW.raw_synthetic_matters;
CREATE OR REPLACE TABLE CORE.bridge_matter_contract AS
SELECT matter_id, contract_id, executed_on FROM RAW.raw_synthetic_contract_attachment;
CREATE OR REPLACE TABLE CORE.matter_authorization AS
SELECT matter_id, employee_id, access_level, valid_from, valid_to
FROM RAW.raw_synthetic_matter_authorization;
CREATE OR REPLACE TABLE CORE.matter_assignment AS
SELECT matter_id, employee_id, assignment_role FROM RAW.raw_synthetic_matter_assignment;

-- fact_clause now that the matter graph exists
CREATE OR REPLACE TABLE CORE.fact_clause AS
SELECT b.matter_id, c.contract_id, c.contract_type, r.clause_category,
       c.contract_name, r.answer, r.clause_text, r.char_start, r.char_end
FROM RAW.raw_cuad_clauses r
JOIN CORE.dim_contract c ON c.contract_id = r.contract_id
JOIN CORE.bridge_matter_contract b ON b.contract_id = c.contract_id;
```

**Note on role buckets:** the access map below is derived from
`raw_synthetic_employees.demo_role`, so the wall maps to the three
`ATTORNEY_0/1/2` buckets, `PARALEGAL`, and the oversight roles. This replaces the
`HASH(employee_id)` bucketing currently in `sql/03`, which was sized for a small
employee set.

---

## 7. RBAC + masking (Phase 2)

🧾 Run as `COMPLIANCE_ADMIN` (`sql/03_row_access_and_masking.sql`):

```sql
USE ROLE COMPLIANCE_ADMIN;
USE DATABASE SNOW_COMPLIANCE_DEMO;
USE SCHEMA SECURITY;

CREATE OR REPLACE TABLE SECURITY.matter_access_map (
  role_name STRING, matter_id STRING, access_level STRING,
  valid_from DATE, valid_to DATE
);

INSERT OVERWRITE INTO SECURITY.matter_access_map
SELECT DISTINCT e.demo_role AS role_name, a.matter_id, a.access_level,
       a.valid_from, a.valid_to
FROM RAW.raw_synthetic_matter_authorization a
JOIN RAW.raw_synthetic_employees e USING (employee_id);

CREATE OR REPLACE ROW ACCESS POLICY SECURITY.matter_access_policy
  AS (matter_id STRING) RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('ACCOUNTADMIN','SYSADMIN','COMPLIANCE_ADMIN','AUDITOR')
    OR EXISTS (
        SELECT 1 FROM SECURITY.matter_access_map m
        WHERE m.role_name = CURRENT_ROLE()
          AND m.matter_id  = matter_id
          AND CURRENT_DATE() BETWEEN m.valid_from
                                 AND COALESCE(m.valid_to, '9999-12-31'));

ALTER TABLE CORE.fact_clause            ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.dim_matter             ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.bridge_matter_contract ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.matter_authorization   ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.matter_assignment      ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);

CREATE OR REPLACE MASKING POLICY SECURITY.pii_mask
  AS (val STRING) RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('COMPLIANCE_ADMIN','ACCOUNTADMIN','AUDITOR') THEN val
      WHEN CURRENT_ROLE() IN ('ATTORNEY_0','ATTORNEY_1','ATTORNEY_2','PARALEGAL') THEN '***REDACTED***'
      ELSE NULL
    END;

ALTER TABLE CORE.dim_client MODIFY COLUMN contact_email SET MASKING POLICY SECURITY.pii_mask;
ALTER TABLE CORE.dim_client MODIFY COLUMN contact_phone SET MASKING POLICY SECURITY.pii_mask;

CREATE TAG IF NOT EXISTS SECURITY.data_classification
  ALLOWED_VALUES 'PII','CONFIDENTIAL','ATTORNEY_WORK_PRODUCT','PUBLIC';
ALTER TABLE CORE.dim_client MODIFY COLUMN contact_email SET TAG SECURITY.data_classification='PII';
ALTER TABLE CORE.fact_clause MODIFY COLUMN clause_text SET TAG SECURITY.data_classification='CONFIDENTIAL';

GRANT SELECT ON ALL TABLES IN SCHEMA CORE TO ROLE ATTORNEY;
GRANT SELECT ON ALL TABLES IN SCHEMA MARTS TO ROLE ATTORNEY;
```

---

## 8. Risk metadata (Phase 2)

🧾 Run as `DEMO_ADMIN` (`sql/04_risk_views.sql`) — 9 transparent rules over
CUAD's **actual** categories; labelled **simulated**, not legal advice:

```sql
USE ROLE DEMO_ADMIN;
USE SCHEMA CORE;

CREATE OR REPLACE TABLE CORE.ref_risk_rule (
  rule_id STRING, clause_category STRING, signal STRING,
  pattern STRING, points INT, rationale STRING);

INSERT OVERWRITE INTO CORE.ref_risk_rule VALUES
  ('R1','Uncapped Liability','PRESENT',NULL,40,'Uncapped liability exposure'),
  ('R2','Cap On Liability','ABSENT',NULL,20,'No cap on liability'),
  ('R3','Termination For Convenience','PRESENT',NULL,15,'Counterparty may exit at will'),
  ('R4','Anti-Assignment','PRESENT',NULL,10,'Assignment restricted'),
  ('R5','Change Of Control','PRESENT',NULL,10,'Change-of-control provision'),
  ('R6','Minimum Commitment','PRESENT',NULL,10,'Minimum purchase/volume commitment'),
  ('R7','Governing Law','ABSENT',NULL,10,'No governing law found'),
  ('R8','Non-Compete','PRESENT',NULL,5,'Restrictive covenant present'),
  ('R9','Exclusivity','PRESENT',NULL,5,'Exclusivity provision present');

CREATE OR REPLACE VIEW MARTS.mart_matter_risk AS
SELECT m.matter_id, m.matter_name, c.contract_id, c.contract_type,
       SUM(CASE
             WHEN r.signal='ABSENT'  AND f.answer='No'  THEN r.points
             WHEN r.signal='PRESENT' AND f.answer='Yes' THEN r.points
             WHEN r.signal='KEYWORD' AND f.clause_text ILIKE '%'||r.pattern||'%' THEN r.points
             ELSE 0 END) AS risk_score
FROM CORE.dim_matter m
JOIN CORE.bridge_matter_contract b ON b.matter_id = m.matter_id
JOIN CORE.dim_contract c ON c.contract_id = b.contract_id
JOIN CORE.fact_clause  f ON f.contract_id = c.contract_id
JOIN CORE.ref_risk_rule r ON r.clause_category = f.clause_category
GROUP BY 1,2,3,4;

CREATE OR REPLACE VIEW MARTS.mart_high_risk_register AS
SELECT matter_id, matter_name, contract_type, risk_score,
       CASE WHEN risk_score >= 60 THEN 'High'
            WHEN risk_score >= 30 THEN 'Medium' ELSE 'Low' END AS risk_band
FROM MARTS.mart_matter_risk;

-- Sanity-check the band distribution across all 510 matters, then re-tune
-- thresholds if the demo needs a more even split.
SELECT risk_band, COUNT(*) FROM MARTS.mart_high_risk_register GROUP BY 1;
```

---

## 9. Verify the wall (Phase 4) — by hand

The row access policy does the work; you prove it by **switching roles** in
Snowsight and re-running the same query:

| # | Action | Expected |
| --- | --- | --- |
| 1 | 🖱️ Switch role to `ATTORNEY_0`, run the query below | only authorized matters (rows > 0) |
| 2 | Switch to `ATTORNEY_1` | a **different** matter set |
| 3 | Switch to `COMPLIANCE_ADMIN` | all 510 matters |
| 4 | As `ATTORNEY_0`, `SELECT contact_email FROM CORE.dim_client LIMIT 1` | `***REDACTED***` |
| 5 | As `AUDITOR`, `SELECT contact_email FROM CORE.dim_client LIMIT 1` | plain (synthetic) value |

```sql
USE ROLE ATTORNEY_0;
SELECT matter_id, matter_name, contract_type, risk_score, risk_band
FROM MARTS.mart_high_risk_register
WHERE risk_band = 'High'
ORDER BY risk_score DESC;
```

🧾 Prove it from Snowflake's own metadata (`sql/05_audit_queries.sql`; note
`ACCOUNT_USAGE` has up to ~45 min latency):

```sql
SELECT policy_name, ref_column_name, ref_entity_name
FROM SNOW_COMPLIANCE_DEMO.INFORMATION_SCHEMA.POLICY_REFERENCES
ORDER BY ref_entity_name;

SELECT query_id, user_name, role_name, start_time, query_type, rows_produced
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_text ILIKE '%MART_MATTER_RISK%'
ORDER BY start_time DESC LIMIT 50;
```

Record the role × matter result in `GOV.access_verification` (created in `sql/05`).

---

## 10. Web application (Phase 3) — pointer

**Recommended first build: Streamlit in Snowflake.** It runs as the *caller's*
Snowflake role, so the row access policy and masking from §7 apply with no
separate login store. Auth is Snowflake SSO/MFA.

Outline:
1. Create a Streamlit app in `SNOW_COMPLIANCE_DEMO.MARTS` (Snowsight → Streamlit).
2. The app issues `SELECT …` against `MARTS.mart_matter_risk` / `CORE.fact_clause`;
   the caller's role scopes rows automatically.
3. Admin screen: show `SECURITY.matter_access_map` and let `COMPLIANCE_ADMIN`
   edit grants (all changes audited).
4. Audit screen: read `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` for data access
   (visible to `AUDITOR`/`COMPLIANCE_ADMIN`) plus an app-level `audit_log` table
   for UI actions, mirroring `poc/access.py`.

If a standalone external portal is later required, use **Snowflake External
OAuth/SSO** (pass the user identity), a dedicated service role per request, and
session tags for attribution — see the report §8.

---

## 11. Tear down

```sql
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS SNOW_COMPLIANCE_DEMO;
DROP WAREHOUSE IF EXISTS WH_LOAD;
DROP WAREHOUSE IF EXISTS WH_ANALYTICS;
DROP ROLE IF EXISTS ATTORNEY_0;
DROP ROLE IF EXISTS ATTORNEY_1;
DROP ROLE IF EXISTS ATTORNEY_2;
DROP ROLE IF EXISTS PARALEGAL;
DROP ROLE IF EXISTS ATTORNEY;
DROP ROLE IF EXISTS AUDITOR;
DROP ROLE IF EXISTS COMPLIANCE_ADMIN;
DROP ROLE IF EXISTS DEMO_ADMIN;
```

Store credentials in Paperclip secrets — never in the repo.

---

## 12. Repo assets for this runbook

Approved 2026-10-16 and added to the repo:

1. [`sql/full_dataset/06_full_dataset.sql`](../sql/full_dataset/06_full_dataset.sql) —
   the consolidated DDL for this walkthrough (roles, load, normalize, synthetic
   layer, RBAC, risk). It lives in a subdirectory because
   `scripts/run_sql_offline.py` runs top-level `sql/*.sql` through fakesnow, which
   cannot execute stages/`COPY INTO` or `LATERAL FLATTEN` over `VARIANT`.
2. [`ingest/split_cuad_json.py`](../ingest/split_cuad_json.py) — the NDJSON
   splitter from §0.
3. The review site page **Full-dataset plan** (`full-dataset.html`).

The `sql/01…05` sample-scale files are unchanged; this runbook supersedes their
sample-sized synthetic bucketing for the full-dataset run.
