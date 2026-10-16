-- ============================================================================
-- 06_full_dataset.sql
-- Full CUAD dataset (510 contracts / 20,910 clause annotations) into Snowflake.
--
-- Board-approved 2026-10-16. Runs AFTER sql/01…05 in a Snowsight worksheet.
-- The manual, step-by-step version (with Snowsight/`PUT` instructions and the
-- verification walkthrough) is docs/SNOWFLAKE_WALKTHROUGH.md; this file is the
-- canonical consolidated SQL for that runbook.
--
-- This script is intentionally NOT under sql/ top level: scripts/run_sql_offline.py
-- runs sql/*.sql through fakesnow, which cannot execute stages/COPY INTO or
-- LATERAL FLATTEN over VARIANT. Load it separately and run it on a real account.
--
-- Order of run: 01 (database/roles) -> 02 (model) -> 03 (security) ->
--               04 (risk) -> 05 (audit) -> this file.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Attorney role buckets used by the full-scale row access policy
--    (adds to the roles created in sql/01; PARALEGAL / COMPLIANCE_ADMIN /
--     AUDITOR already exist there).
-- ---------------------------------------------------------------------------
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS ATTORNEY_0;
CREATE ROLE IF NOT EXISTS ATTORNEY_1;
CREATE ROLE IF NOT EXISTS ATTORNEY_2;
GRANT ROLE ATTORNEY_0 TO ROLE ATTORNEY;
GRANT ROLE ATTORNEY_1 TO ROLE ATTORNEY;
GRANT ROLE ATTORNEY_2 TO ROLE ATTORNEY;
GRANT USAGE ON WAREHOUSE WH_ANALYTICS TO ROLE ATTORNEY_0;
GRANT USAGE ON WAREHOUSE WH_ANALYTICS TO ROLE ATTORNEY_1;
GRANT USAGE ON WAREHOUSE WH_ANALYTICS TO ROLE ATTORNEY_2;

-- ---------------------------------------------------------------------------
-- 2. Land the raw CUAD JSON (one document per row).
--    Produce the file first (transport shaping only):
--        python3 ingest/split_cuad_json.py --json CUADv1.json --out build/cuad_docs.jsonl
--    then upload it to @RAW.cuad_stage (SnowSQL PUT or the Snowsight Load Data
--    wizard) before running the COPY below.
-- ---------------------------------------------------------------------------
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

COPY INTO RAW.raw_cuad_json (src, source_file)
FROM (SELECT $1, METADATA$FILENAME FROM @RAW.cuad_stage)
FILE_FORMAT = RAW.json_ff
PATTERN = '.*cuad_docs.*'
ON_ERROR = 'ABORT_STATEMENT';
-- expect 510 rows
SELECT COUNT(*) AS loaded_documents FROM RAW.raw_cuad_json;

-- ---------------------------------------------------------------------------
-- 3. Normalize CUAD inside Snowflake (parsing stays in SQL).
-- ---------------------------------------------------------------------------
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

-- Data-quality gates (expected: 510 / 20910 / 6702 / 41 / 0)
SELECT COUNT(*) AS contracts             FROM RAW.raw_cuad_contracts;
SELECT COUNT(*) AS annotations           FROM RAW.raw_cuad_clauses;
SELECT COUNT(*) AS present               FROM RAW.raw_cuad_clauses WHERE answer = 'Yes';
SELECT COUNT(DISTINCT clause_category) AS categories FROM RAW.raw_cuad_clauses;
SELECT COUNT(*) AS orphaned
FROM RAW.raw_cuad_clauses c
LEFT JOIN RAW.raw_cuad_contracts k USING (contract_id)
WHERE k.contract_id IS NULL;

-- ---------------------------------------------------------------------------
-- 4. `contract_type` normalization: 249 noisy title-derived strings -> a
--    controlled vocabulary. Raw value is retained on CORE.dim_contract.
-- ---------------------------------------------------------------------------
USE SCHEMA CORE;
CREATE OR REPLACE TABLE CORE.dim_contract AS
SELECT contract_id, contract_name, contract_type FROM RAW.raw_cuad_contracts;
CREATE OR REPLACE TABLE CORE.dim_clause_category AS
SELECT DISTINCT clause_category AS clause_category_id, clause_category
FROM RAW.raw_cuad_clauses;

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
SELECT c.contract_id, c.contract_name,
       c.contract_type AS contract_type_raw,
       COALESCE(r.contract_type, 'Other') AS contract_type
FROM CORE.dim_contract c
LEFT JOIN CORE.ref_contract_type r ON REGEXP_LIKE(c.contract_type, r.pattern);

-- ---------------------------------------------------------------------------
-- 5. Simulated law-firm layer: 510 matters (one per contract), 12 employees,
--    8 clients. Deterministic, SQL-only, obviously fictional.
-- ---------------------------------------------------------------------------
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

CREATE OR REPLACE TABLE RAW.raw_synthetic_contract_attachment AS
WITH g AS (SELECT SEQ4() AS n FROM TABLE(GENERATOR(ROWCOUNT => 510)))
SELECT 'SYN-' || (1000+n+1)::string AS matter_id,
       'CUAD-' || LPAD(n::string,4,'0') AS contract_id,
       DATEADD('day', -1*MOD(n,900), CURRENT_DATE()) AS executed_on
FROM g;

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
SELECT a.matter_id, a.employee_id, m.lead_attorney_id AS approved_by,
       DATEADD('day', -30, CURRENT_DATE()) AS approved_on
FROM RAW.raw_synthetic_matter_authorization a
JOIN RAW.raw_synthetic_matters m USING (matter_id);

-- ---------------------------------------------------------------------------
-- 6. CORE dimensions, bridges, and the fact (matter_id denormalized onto it
--    so the row access policy scopes it directly).
-- ---------------------------------------------------------------------------
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

CREATE OR REPLACE TABLE CORE.fact_clause AS
SELECT b.matter_id, c.contract_id, c.contract_type, r.clause_category,
       c.contract_name, r.answer, r.clause_text, r.char_start, r.char_end
FROM RAW.raw_cuad_clauses r
JOIN CORE.dim_contract c ON c.contract_id = r.contract_id
JOIN CORE.bridge_matter_contract b ON b.contract_id = c.contract_id;

-- ---------------------------------------------------------------------------
-- 7. RBAC: access map derived from employee role buckets, then re-attach the
--    row access policy (CREATE OR REPLACE TABLE above dropped prior attaches).
-- ---------------------------------------------------------------------------
USE ROLE COMPLIANCE_ADMIN;
USE SCHEMA SECURITY;

INSERT OVERWRITE INTO SECURITY.matter_access_map
SELECT DISTINCT e.demo_role AS role_name, a.matter_id, a.access_level,
       a.valid_from, a.valid_to
FROM RAW.raw_synthetic_matter_authorization a
JOIN RAW.raw_synthetic_employees e USING (employee_id);

ALTER TABLE CORE.fact_clause            ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.dim_matter             ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.bridge_matter_contract ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.matter_authorization   ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.matter_assignment      ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);

-- Extend the mask to the ATTORNEY_2 bucket (sql/03 defines ATTORNEY_0/1).
CREATE OR REPLACE MASKING POLICY SECURITY.pii_mask
  AS (val STRING) RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('COMPLIANCE_ADMIN','ACCOUNTADMIN','AUDITOR') THEN val
      WHEN CURRENT_ROLE() IN ('ATTORNEY_0','ATTORNEY_1','ATTORNEY_2','PARALEGAL') THEN '***REDACTED***'
      ELSE NULL
    END;

ALTER TABLE CORE.dim_client MODIFY COLUMN contact_email SET MASKING POLICY SECURITY.pii_mask;
ALTER TABLE CORE.dim_client MODIFY COLUMN contact_phone SET MASKING POLICY SECURITY.pii_mask;

GRANT SELECT ON ALL TABLES IN SCHEMA CORE  TO ROLE ATTORNEY;
GRANT SELECT ON ALL TABLES IN SCHEMA MARTS TO ROLE ATTORNEY;
GRANT SELECT ON ALL TABLES IN SCHEMA CORE  TO ROLE PARALEGAL;
GRANT SELECT ON ALL TABLES IN SCHEMA CORE  TO ROLE AUDITOR;

-- ---------------------------------------------------------------------------
-- 8. Risk metadata at full scale (rules identical to sql/04; re-created here so
--    the full-dataset run is self-contained).
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- 9. Phase 4 verification entry points (see docs/SNOWFLAKE_WALKTHROUGH.md).
--    Run under each attorney role and compare row sets:
-- ---------------------------------------------------------------------------
-- USE ROLE ATTORNEY_0;
-- SELECT matter_id, matter_name, contract_type, risk_score, risk_band
-- FROM MARTS.mart_high_risk_register
-- WHERE risk_band = 'High'
-- ORDER BY risk_score DESC;
