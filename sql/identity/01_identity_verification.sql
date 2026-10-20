-- ============================================================================
-- 01_identity_verification.sql
-- Proposed webcam-login identity schema for SNOW_COMPLIANCE_DEMO.
--
-- Run this manually on a Snowflake trial/account after sql/01..05. It is kept
-- out of the root sql/ directory because the offline fakesnow harness does not
-- emulate stages, VECTOR columns, masking policies, or row access policies.
-- Read docs/WEBCAM_LOGIN_RBAC.md before applying. Do not load real biometric
-- data into this demo account.
--
-- Idempotent: safe to re-run, except MERGE seed rows which are also idempotent.
-- Apply as a role that owns the database (for example DEMO_ADMIN) and then grant
-- the least privilege below. ACCOUNTADMIN is not required by the design.
-- ============================================================================

USE DATABASE SNOW_COMPLIANCE_DEMO;

CREATE SCHEMA IF NOT EXISTS IDENTITY
  COMMENT = 'Webcam login verification: templates, centroids, attempts, audit';

USE SCHEMA IDENTITY;

-- ---------------------------------------------------------------------------
-- Photo storage. Production should use an external stage backed by an
-- encrypted bucket with Object Lock / lifecycle rules. This internal stage is
-- acceptable only for synthetic pilot data.
-- ---------------------------------------------------------------------------
CREATE STAGE IF NOT EXISTS IDENTITY.PHOTO_STAGE
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Raw login/enrollment photos; short retention; restricted role access';

-- ---------------------------------------------------------------------------
-- Consent and identity state
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS IDENTITY.consent_record (
  consent_id      STRING        NOT NULL,
  employee_id     STRING        NOT NULL,
  snowflake_user  STRING        NOT NULL,
  consent_version STRING        NOT NULL,
  signed_at       TIMESTAMP_NTZ NOT NULL,
  method          STRING        NOT NULL,
  withdrawn_at    TIMESTAMP_NTZ,
  evidence_uri    STRING,
  PRIMARY KEY (consent_id)
);

CREATE TABLE IF NOT EXISTS IDENTITY.employee_identity (
  employee_id      STRING        NOT NULL,
  snowflake_user   STRING        NOT NULL,
  status           STRING        NOT NULL,
  consent_version  STRING,
  enrolled_at      TIMESTAMP_NTZ,
  model_id         STRING,
  centroid_version NUMBER,
  last_verified_at TIMESTAMP_NTZ,
  disabled_reason  STRING,
  updated_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  PRIMARY KEY (employee_id)
);

-- ---------------------------------------------------------------------------
-- Model and threshold registry. Never mix model versions silently.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS IDENTITY.model_registry (
  model_id          STRING        NOT NULL,
  pipeline_version  STRING        NOT NULL,
  embedding_dim     NUMBER        NOT NULL,
  thresholds        VARIANT       NOT NULL,
  artifact_sha256   STRING,
  activated_at      TIMESTAMP_NTZ,
  retired_at        TIMESTAMP_NTZ,
  notes             STRING,
  PRIMARY KEY (model_id)
);

-- ---------------------------------------------------------------------------
-- Templates and centroids. Vectors are biometric data: mask/restrict them.
-- ---------------------------------------------------------------------------
-- No primary keys on row-access-policy-protected tables: Snowflake rejects
-- some constraint combinations on protected tables. Enforce uniqueness in the
-- service layer and keep the natural keys indexed by clustering instead.
CREATE TABLE IF NOT EXISTS IDENTITY.face_template (
  template_id    STRING        NOT NULL,
  employee_id    STRING        NOT NULL,
  snowflake_user STRING        NOT NULL,
  model_id       STRING        NOT NULL,
  embedding      VECTOR(FLOAT, 512) NOT NULL,
  quality_score  FLOAT,
  liveness_score FLOAT,
  source_photo_id STRING,
  created_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  is_active      BOOLEAN       DEFAULT TRUE,
  superseded_by  STRING
);

CREATE TABLE IF NOT EXISTS IDENTITY.face_centroid (
  employee_id    STRING        NOT NULL,
  snowflake_user STRING        NOT NULL,
  model_id       STRING        NOT NULL,
  centroid       VECTOR(FLOAT, 512) NOT NULL,
  sample_count   NUMBER        NOT NULL,
  intra_p50      FLOAT,
  intra_p95      FLOAT,
  version        NUMBER        NOT NULL,
  updated_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  updated_by     STRING
);

CREATE TABLE IF NOT EXISTS IDENTITY.centroid_history (
  history_id     STRING        NOT NULL,
  employee_id    STRING        NOT NULL,
  model_id       STRING        NOT NULL,
  version        NUMBER        NOT NULL,
  centroid       VECTOR(FLOAT, 512) NOT NULL,
  sample_count   NUMBER        NOT NULL,
  reason_code    STRING        NOT NULL,
  actor          STRING,
  created_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  PRIMARY KEY (history_id)
);

-- ---------------------------------------------------------------------------
-- Login evidence and audit
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS IDENTITY.login_attempt (
  attempt_id      STRING        NOT NULL,
  request_id      STRING        NOT NULL,
  employee_id     STRING,
  snowflake_user  STRING,
  occurred_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  outcome         STRING        NOT NULL,
  reason_code     STRING,
  similarity      FLOAT,
  threshold_used  FLOAT,
  liveness_score  FLOAT,
  quality_score   FLOAT,
  model_id        STRING,
  centroid_version NUMBER,
  photo_id        STRING,
  assurance_level STRING,
  ip_address      STRING,
  user_agent      STRING,
  device_result   STRING,
  session_id      STRING
);

CREATE TABLE IF NOT EXISTS IDENTITY.photo_audit (
  photo_id        STRING        NOT NULL,
  employee_id     STRING        NOT NULL,
  snowflake_user  STRING        NOT NULL,
  attempt_id      STRING,
  stage_uri       STRING        NOT NULL,
  sha256          STRING        NOT NULL,
  captured_at     TIMESTAMP_NTZ NOT NULL,
  retention_until TIMESTAMP_NTZ NOT NULL,
  legal_hold      BOOLEAN       DEFAULT FALSE,
  key_id          STRING,
  deleted_at      TIMESTAMP_NTZ,
  deletion_reason STRING
);

CREATE TABLE IF NOT EXISTS IDENTITY.photo_access_log (
  access_id   STRING        NOT NULL,
  photo_id    STRING        NOT NULL,
  viewer      STRING        NOT NULL,
  role_name   STRING        NOT NULL,
  reason      STRING        NOT NULL,
  ticket      STRING,
  approved_by STRING,
  viewed_at   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  PRIMARY KEY (access_id)
);

CREATE TABLE IF NOT EXISTS IDENTITY.verification_event (
  event_id         STRING        NOT NULL,
  event_index      NUMBER        NOT NULL,
  event_type       STRING        NOT NULL,
  occurred_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  actor            STRING,
  payload_canonical STRING       NOT NULL,
  prev_hash        STRING        NOT NULL,
  event_hash       STRING        NOT NULL,
  PRIMARY KEY (event_id)
);

-- ---------------------------------------------------------------------------
-- Assurance policy: the bridge from verification strength to RBAC.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS IDENTITY.role_assurance_policy (
  role_name          STRING NOT NULL,
  required_assurance STRING NOT NULL,
  step_up_for_level  STRING,
  rationale          STRING,
  PRIMARY KEY (role_name)
);

MERGE INTO IDENTITY.role_assurance_policy AS target
USING (
  SELECT 'PARALEGAL' AS role_name, 'AAL2' AS required_assurance, 'HIGH' AS step_up_for_level,
         'Matter-scoped reads; step up for High confidentiality' AS rationale
  UNION ALL
  SELECT 'ATTORNEY', 'AAL2', 'HIGH',
         'Matter-scoped reads; step up for High confidentiality'
  UNION ALL
  SELECT 'AUDITOR', 'AAL2', 'NONE',
         'Audit metadata; raw photos require break-glass approval'
  UNION ALL
  SELECT 'COMPLIANCE_ADMIN', 'AAL3', 'ALWAYS',
         'Policy authority; fresh verification for policy changes'
  UNION ALL
  SELECT 'DEMO_ADMIN', 'AAL3', 'ALWAYS',
         'Build/administration on a managed device'
) AS source
ON target.role_name = source.role_name
WHEN MATCHED THEN UPDATE SET
  required_assurance = source.required_assurance,
  step_up_for_level = source.step_up_for_level,
  rationale = source.rationale
WHEN NOT MATCHED THEN INSERT
  (role_name, required_assurance, step_up_for_level, rationale)
  VALUES (source.role_name, source.required_assurance, source.step_up_for_level, source.rationale);

-- ---------------------------------------------------------------------------
-- Protection: mask photo locations and restrict row visibility to self or
-- compliance/audit. Vectors are protected by grants and secure views rather
-- than a masking policy, so the application service can still write them.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE MASKING POLICY IDENTITY.photo_uri_mask
  AS (val STRING) RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('COMPLIANCE_ADMIN', 'AUDITOR') THEN val
      ELSE '***RESTRICTED***'
    END;

ALTER TABLE IDENTITY.photo_audit
  MODIFY COLUMN stage_uri SET MASKING POLICY IDENTITY.photo_uri_mask;

CREATE OR REPLACE ROW ACCESS POLICY IDENTITY.self_or_oversight
  AS (snowflake_user STRING) RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('COMPLIANCE_ADMIN', 'AUDITOR')
    OR snowflake_user = CURRENT_USER();

ALTER TABLE IDENTITY.login_attempt
  ADD ROW ACCESS POLICY IDENTITY.self_or_oversight ON (snowflake_user);

ALTER TABLE IDENTITY.photo_audit
  ADD ROW ACCESS POLICY IDENTITY.self_or_oversight ON (snowflake_user);

ALTER TABLE IDENTITY.face_template
  ADD ROW ACCESS POLICY IDENTITY.self_or_oversight ON (snowflake_user);

ALTER TABLE IDENTITY.face_centroid
  ADD ROW ACCESS POLICY IDENTITY.self_or_oversight ON (snowflake_user);

-- ---------------------------------------------------------------------------
-- Secure views for the application and the audit console
-- ---------------------------------------------------------------------------
CREATE OR REPLACE SECURE VIEW IDENTITY.v_my_login_attempts AS
SELECT attempt_id, employee_id, occurred_at, outcome, reason_code,
       assurance_level, model_id, centroid_version
FROM IDENTITY.login_attempt
WHERE snowflake_user = CURRENT_USER();

CREATE OR REPLACE SECURE VIEW IDENTITY.v_my_enrollment_status AS
SELECT employee_id, status, consent_version, enrolled_at, model_id,
       centroid_version, last_verified_at
FROM IDENTITY.employee_identity
WHERE snowflake_user = CURRENT_USER();

CREATE OR REPLACE SECURE VIEW IDENTITY.v_role_assurance AS
SELECT role_name, required_assurance, step_up_for_level, rationale
FROM IDENTITY.role_assurance_policy;

CREATE OR REPLACE SECURE VIEW IDENTITY.v_audit_anomalies AS
SELECT employee_id, occurred_at, outcome, reason_code, similarity,
       liveness_score, quality_score, model_id, request_id
FROM IDENTITY.login_attempt
WHERE outcome <> 'accept'
   OR reason_code ILIKE 'LIVENESS:%'
   OR reason_code ILIKE 'QUALITY:%';

-- ---------------------------------------------------------------------------
-- Privileges. The application service should have INSERT/UPDATE on the
-- identity tables it owns, but no SELECT on raw photos or vectors. Human
-- access goes through the secure views. Adjust role names to the deployment.
-- ---------------------------------------------------------------------------
GRANT USAGE ON SCHEMA IDENTITY TO ROLE COMPLIANCE_ADMIN;
GRANT USAGE ON SCHEMA IDENTITY TO ROLE AUDITOR;
GRANT USAGE ON SCHEMA IDENTITY TO ROLE ATTORNEY;
GRANT USAGE ON SCHEMA IDENTITY TO ROLE PARALEGAL;

GRANT SELECT ON VIEW IDENTITY.v_my_login_attempts TO ROLE ATTORNEY;
GRANT SELECT ON VIEW IDENTITY.v_my_login_attempts TO ROLE PARALEGAL;
GRANT SELECT ON VIEW IDENTITY.v_my_login_attempts TO ROLE AUDITOR;
GRANT SELECT ON VIEW IDENTITY.v_my_login_attempts TO ROLE COMPLIANCE_ADMIN;

GRANT SELECT ON VIEW IDENTITY.v_my_enrollment_status TO ROLE ATTORNEY;
GRANT SELECT ON VIEW IDENTITY.v_my_enrollment_status TO ROLE PARALEGAL;

GRANT SELECT ON VIEW IDENTITY.v_role_assurance TO ROLE COMPLIANCE_ADMIN;
GRANT SELECT ON VIEW IDENTITY.v_role_assurance TO ROLE AUDITOR;

GRANT SELECT ON VIEW IDENTITY.v_audit_anomalies TO ROLE COMPLIANCE_ADMIN;
GRANT SELECT ON VIEW IDENTITY.v_audit_anomalies TO ROLE AUDITOR;

GRANT SELECT ON TABLE IDENTITY.login_attempt TO ROLE AUDITOR;
GRANT SELECT ON TABLE IDENTITY.verification_event TO ROLE AUDITOR;
GRANT SELECT ON TABLE IDENTITY.photo_access_log TO ROLE AUDITOR;

GRANT SELECT ON TABLE IDENTITY.role_assurance_policy TO ROLE COMPLIANCE_ADMIN;
GRANT SELECT ON TABLE IDENTITY.model_registry TO ROLE COMPLIANCE_ADMIN;
GRANT SELECT ON TABLE IDENTITY.face_template TO ROLE COMPLIANCE_ADMIN;
GRANT SELECT ON TABLE IDENTITY.face_centroid TO ROLE COMPLIANCE_ADMIN;

GRANT READ ON STAGE IDENTITY.PHOTO_STAGE TO ROLE COMPLIANCE_ADMIN;

-- ---------------------------------------------------------------------------
-- Operational notes
-- ---------------------------------------------------------------------------
-- 1. Create a dedicated service role (for example IDENTITY_SERVICE) with
--    INSERT on login_attempt, photo_audit, verification_event and UPDATE on
--    face_centroid/centroid_history. Do not grant it SELECT on photo_audit or
--    face_template.
-- 2. Replace the internal stage with an external stage backed by an encrypted
--    bucket with Object Lock and a 90-day lifecycle rule. Pre-sign short-lived
--    URLs in the verification service; never hand out stage credentials.
-- 3. Schedule retention jobs to set photo_audit.deleted_at and remove objects,
--    skipping legal_hold = TRUE. Retain hashes and audit rows after deletion.
-- 4. Anchor verification_event.event_hash periodically in immutable storage.
-- 5. Add classification tags (BIOMETRIC, PII) and include IDENTITY tables in
--    the access-review and ACCESS_HISTORY evidence queries.
