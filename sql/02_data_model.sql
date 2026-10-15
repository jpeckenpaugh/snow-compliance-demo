-- ============================================================================
-- 02_data_model.sql
-- RAW -> CORE model for the CUAD + synthetic law-firm demo.
-- Run as DEMO_ADMIN after 01_database_and_roles.sql.
-- ============================================================================

USE DATABASE SNOW_COMPLIANCE_DEMO;
USE SCHEMA RAW;

-- --- RAW landing ------------------------------------------------------------
CREATE OR REPLACE TABLE RAW.raw_cuad_contracts (
  contract_id   STRING,
  contract_name STRING,
  contract_type STRING,
  parties       VARIANT,
  source_file   STRING,
  loaded_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE RAW.raw_cuad_clauses (
  contract_id      STRING,
  clause_category  STRING,
  answer           STRING,        -- Yes / No / NA
  clause_text      STRING,
  char_start       NUMBER,
  char_end         NUMBER,
  loaded_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Synthetic records are landed here by ingest/generate_synthetic_data.py.
CREATE OR REPLACE TABLE RAW.raw_synthetic_clients (
  client_id STRING, client_name STRING, industry STRING, region STRING,
  contact_name STRING, contact_email STRING, contact_phone STRING
);
CREATE OR REPLACE TABLE RAW.raw_synthetic_employees (
  employee_id STRING, full_name STRING, title STRING, practice STRING, role STRING
);
CREATE OR REPLACE TABLE RAW.raw_synthetic_matters (
  matter_id STRING, client_id STRING, matter_name STRING,
  confidentiality_level STRING, opened_on DATE, lead_attorney_id STRING
);
CREATE OR REPLACE TABLE RAW.raw_synthetic_matter_authorization (
  matter_id STRING, employee_id STRING, access_level STRING, valid_from DATE, valid_to DATE
);
CREATE OR REPLACE TABLE RAW.raw_synthetic_matter_assignment (
  matter_id STRING, employee_id STRING, assignment_role STRING
);
CREATE OR REPLACE TABLE RAW.raw_synthetic_contract_attachment (
  matter_id STRING, contract_id STRING, executed_on DATE
);
CREATE OR REPLACE TABLE RAW.raw_synthetic_access_approval (
  matter_id STRING, employee_id STRING, approved_by STRING, approved_on DATE
);

USE SCHEMA CORE;

-- --- Dimensions -------------------------------------------------------------
CREATE OR REPLACE TABLE CORE.dim_client AS
SELECT client_id, client_name, industry, region,
       contact_name, contact_email, contact_phone
FROM RAW.raw_synthetic_clients;

CREATE OR REPLACE TABLE CORE.dim_employee AS
SELECT employee_id, full_name, title, practice, role
FROM RAW.raw_synthetic_employees;

CREATE OR REPLACE TABLE CORE.dim_matter AS
SELECT matter_id, client_id, matter_name, confidentiality_level,
       opened_on, lead_attorney_id
FROM RAW.raw_synthetic_matters;

CREATE OR REPLACE TABLE CORE.dim_contract AS
SELECT contract_id, contract_name, contract_type
FROM RAW.raw_cuad_contracts;

CREATE OR REPLACE TABLE CORE.dim_clause_category AS
SELECT DISTINCT clause_category AS clause_category_id, clause_category AS clause_category
FROM RAW.raw_cuad_clauses;

-- --- Bridges / relationships -------------------------------------------------
CREATE OR REPLACE TABLE CORE.bridge_matter_contract AS
SELECT a.matter_id, a.contract_id, a.executed_on
FROM RAW.raw_synthetic_contract_attachment a;

-- Governs row access. access_level: READ | WRITE
CREATE OR REPLACE TABLE CORE.matter_authorization AS
SELECT matter_id, employee_id, access_level, valid_from, valid_to
FROM RAW.raw_synthetic_matter_authorization;

CREATE OR REPLACE TABLE CORE.matter_assignment AS
SELECT matter_id, employee_id, assignment_role
FROM RAW.raw_synthetic_matter_assignment;

-- --- Fact --------------------------------------------------------------------
-- One row per (contract, clause category). matter_id is denormalized onto the
-- fact so the row access policy can scope it directly.
CREATE OR REPLACE TABLE CORE.fact_clause AS
SELECT b.matter_id,
       c.contract_id,
       c.contract_type,
       r.clause_category,
       c.contract_name,
       r.answer,
       r.clause_text,
       r.char_start,
       r.char_end
FROM RAW.raw_cuad_clauses r
JOIN CORE.dim_contract c ON c.contract_id = r.contract_id
JOIN CORE.bridge_matter_contract b ON b.contract_id = c.contract_id;

-- --- Data-quality assertions -------------------------------------------------
-- Orphaned clauses (no contract). Expect 0 rows.
-- SELECT COUNT(*) FROM CORE.fact_clause f
--   LEFT JOIN CORE.dim_contract c USING (contract_id) WHERE c.contract_id IS NULL;
-- Matters with no authorized attorney. Expect 0 rows.
-- SELECT m.matter_id FROM CORE.dim_matter m
--   LEFT JOIN CORE.matter_authorization a USING (matter_id) WHERE a.matter_id IS NULL;
