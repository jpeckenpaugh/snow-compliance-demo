-- ============================================================================
-- 05_audit_queries.sql
-- Phase 4: verification & audit. Prove the wall using Snowflake's own metadata.
-- Note: ACCOUNT_USAGE views have up to ~45 minutes of latency.
-- ============================================================================

USE DATABASE SNOW_COMPLIANCE_DEMO;
USE SCHEMA GOV;

-- --- 1. Which policies are attached where (ground truth for the demo) --------
SELECT policy_name, ref_column_name, ref_entity_name, ref_entity_domain
FROM SNOW_COMPLIANCE_DEMO.INFORMATION_SCHEMA.POLICY_REFERENCES
ORDER BY ref_entity_name;

-- --- 2. Row access policies currently defined --------------------------------
SELECT policy_name, policy_kind, policy_owner, created
FROM SNOWFLAKE.ACCOUNT_USAGE.ROW_ACCESS_POLICIES
WHERE policy_name = 'MATTER_ACCESS_POLICY';

-- --- 3. What did each role query, and when? ---------------------------------
CREATE OR REPLACE VIEW GOV.audit_role_queries AS
SELECT query_id, user_name, role_name, start_time, query_type,
       rows_produced, query_text
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_text ILIKE '%FACT_CLAUSE%' OR query_text ILIKE '%MART_MATTER_RISK%';

-- --- 4. Record the multi-role verification matrix ----------------------------
CREATE OR REPLACE TABLE GOV.access_verification (
  tested_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  role_name    STRING,
  target_matter STRING,
  expected     STRING,   -- ROWS | ZERO_ROWS | DENIED | MASKED
  observed_rows INT,
  observed_value STRING,
  query_id     STRING
);

-- Populate by running the same statement under each role and capturing
-- QUERY_ID() plus the result. Example procedure per role is documented in
-- docs/PLAN.md (Phase 4).

-- --- 5. Denied access log ----------------------------------------------------
CREATE OR REPLACE VIEW GOV.denied_access_log AS
SELECT query_id, user_name, role_name, start_time, error_code, error_message,
       query_text
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE error_code IS NOT NULL
  AND (error_message ILIKE '%insufficient%' OR error_message ILIKE '%not authorized%');

-- --- 6. The close-out report: high-risk clauses by authorized matter ---------
-- Run as ATTORNEY_0 and ATTORNEY_1; results differ by design.
SELECT matter_id, matter_name, contract_type, risk_score, risk_band
FROM MARTS.mart_high_risk_register
WHERE risk_band = 'High'
ORDER BY risk_score DESC;
