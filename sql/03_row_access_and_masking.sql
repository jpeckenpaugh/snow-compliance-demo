-- ============================================================================
-- 03_row_access_and_masking.sql
-- Phase 2: matter confidentiality via row access policies + masking + tags.
-- Run as COMPLIANCE_ADMIN after 02_data_model.sql.
-- ============================================================================

USE DATABASE SNOW_COMPLIANCE_DEMO;
USE SCHEMA SECURITY;

-- --- Role -> matter mapping (the access decision is DATA, not code) ----------
CREATE OR REPLACE TABLE SECURITY.matter_access_map (
  role_name    STRING,
  matter_id    STRING,
  access_level STRING,
  valid_from   DATE,
  valid_to     DATE
);

-- Populate from authorization by convening role buckets for the demo.
-- In production this maps employee_id (resolved from the session) instead.
INSERT OVERWRITE INTO SECURITY.matter_access_map
SELECT 'ATTORNEY_' || MOD(ABS(HASH(employee_id)), 2) AS role_name,
       matter_id, access_level, valid_from, valid_to
FROM CORE.matter_authorization;

-- --- Row access policy -------------------------------------------------------
CREATE OR REPLACE ROW ACCESS POLICY SECURITY.matter_access_policy
  AS (matter_id STRING) RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('ACCOUNTADMIN','SYSADMIN','COMPLIANCE_ADMIN','AUDITOR')
    OR EXISTS (
        SELECT 1
        FROM SECURITY.matter_access_map m
        WHERE m.role_name = CURRENT_ROLE()
          AND m.matter_id  = matter_id
          AND CURRENT_DATE() BETWEEN m.valid_from AND COALESCE(m.valid_to, '9999-12-31')
    );

-- Attach to EVERY object carrying matter_id (base tables AND bridges).
ALTER TABLE CORE.fact_clause                 ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.dim_matter                  ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.bridge_matter_contract      ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.matter_authorization        ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);
ALTER TABLE CORE.matter_assignment           ADD ROW ACCESS POLICY SECURITY.matter_access_policy ON (matter_id);

-- --- Masking -----------------------------------------------------------------
CREATE OR REPLACE MASKING POLICY SECURITY.pii_mask
  AS (val STRING) RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('COMPLIANCE_ADMIN','ACCOUNTADMIN','AUDITOR') THEN val
      WHEN CURRENT_ROLE() IN ('ATTORNEY_0','ATTORNEY_1','PARALEGAL') THEN '***REDACTED***'
      ELSE NULL
    END;

ALTER TABLE CORE.dim_client MODIFY COLUMN contact_email SET MASKING POLICY SECURITY.pii_mask;
ALTER TABLE CORE.dim_client MODIFY COLUMN contact_phone SET MASKING POLICY SECURITY.pii_mask;

-- --- Classification tags (self-documenting protection) -----------------------
CREATE TAG IF NOT EXISTS SECURITY.data_classification
  ALLOWED_VALUES 'PII','CONFIDENTIAL','ATTORNEY_WORK_PRODUCT','PUBLIC';

ALTER TABLE CORE.dim_client MODIFY COLUMN contact_email SET TAG SECURITY.data_classification = 'PII';
ALTER TABLE CORE.dim_client MODIFY COLUMN contact_phone SET TAG SECURITY.data_classification = 'PII';
ALTER TABLE CORE.fact_clause MODIFY COLUMN clause_text  SET TAG SECURITY.data_classification = 'CONFIDENTIAL';

-- --- Consumer grants (reads through policy-protected objects) ----------------
GRANT SELECT ON ALL TABLES IN SCHEMA CORE  TO ROLE ATTORNEY;
GRANT SELECT ON ALL TABLES IN SCHEMA MARTS TO ROLE ATTORNEY;
GRANT SELECT ON ALL TABLES IN SCHEMA CORE  TO ROLE PARALEGAL;
GRANT SELECT ON ALL TABLES IN SCHEMA CORE  TO ROLE AUDITOR;
GRANT SELECT ON ALL TABLES IN SCHEMA GOV   TO ROLE AUDITOR;
