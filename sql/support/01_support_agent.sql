-- ============================================================================
-- 01_support_agent.sql
-- Proposed SUPPORT schema for the bounded customer-support agent described in
-- docs/SUPPORT_AGENT_INTEGRATION.md.
--
-- Run manually after sql/01..05 and sql/identity/01_identity_verification.sql.
-- Kept out of the root sql/ glob because the offline fakesnow harness does not
-- emulate roles, grants, VECTOR columns, row access policies, or masking.
--
-- The support service NEVER reads IDENTITY biometric tables, raw photos, or
-- embeddings. Only redacted conversation text and workflow metadata live here.
-- Idempotent: safe to re-run.
-- ============================================================================

USE DATABASE SNOW_COMPLIANCE_DEMO;

CREATE SCHEMA IF NOT EXISTS SUPPORT
  COMMENT = 'Bounded support agent: conversations, intents, tools, escalations, KB';

USE SCHEMA SUPPORT;

-- ---------------------------------------------------------------------------
-- Roles. Map these to IdP groups in production; do not reuse admin roles.
-- ---------------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS SUPPORT_AGENT
  COMMENT = 'Service principal for the support orchestrator; no IDENTITY access';
CREATE ROLE IF NOT EXISTS SUPPORT_HUMAN
  COMMENT = 'Human support queue; reads assigned conversations, no policy changes';

GRANT ROLE SUPPORT_AGENT TO ROLE SYSADMIN;
GRANT ROLE SUPPORT_HUMAN TO ROLE SYSADMIN;

GRANT USAGE ON DATABASE SNOW_COMPLIANCE_DEMO TO ROLE SUPPORT_AGENT;
GRANT USAGE ON DATABASE SNOW_COMPLIANCE_DEMO TO ROLE SUPPORT_HUMAN;
GRANT USAGE ON WAREHOUSE WH_ANALYTICS TO ROLE SUPPORT_AGENT;
GRANT USAGE ON WAREHOUSE WH_ANALYTICS TO ROLE SUPPORT_HUMAN;

-- ---------------------------------------------------------------------------
-- Release and knowledge base
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS SUPPORT.agent_release (
  agent_id       STRING        NOT NULL,
  version        STRING        NOT NULL,
  model_id       STRING        NOT NULL,
  prompt_sha256  STRING        NOT NULL,
  config         VARIANT,
  activated_at   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  retired_at     TIMESTAMP_NTZ,
  notes          STRING,
  PRIMARY KEY (agent_id, version)
);

CREATE TABLE IF NOT EXISTS SUPPORT.kb_article (
  article_id    STRING        NOT NULL,
  title         STRING        NOT NULL,
  body          STRING        NOT NULL,
  owner         STRING        NOT NULL,
  status        STRING        NOT NULL,
  version       NUMBER        NOT NULL,
  effective_at  TIMESTAMP_NTZ,
  review_due    TIMESTAMP_NTZ,
  source_url    STRING,
  PRIMARY KEY (article_id, version)
);

CREATE TABLE IF NOT EXISTS SUPPORT.kb_chunk (
  chunk_id      STRING        NOT NULL,
  article_id    STRING        NOT NULL,
  article_version NUMBER      NOT NULL,
  chunk_index   NUMBER        NOT NULL,
  chunk_text    STRING        NOT NULL,
  embedding     VECTOR(FLOAT, 1024),
  model_id      STRING,
  PRIMARY KEY (chunk_id)
);

-- ---------------------------------------------------------------------------
-- Conversations and evidence. snowflake_user is denormalized so row access
-- and secure views do not need to join through another protected table.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS SUPPORT.conversation (
  conversation_id STRING        NOT NULL,
  employee_id     STRING        NOT NULL,
  snowflake_user  STRING        NOT NULL,
  channel         STRING        NOT NULL,
  release_version STRING        NOT NULL,
  started_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  ended_at        TIMESTAMP_NTZ,
  status          STRING        NOT NULL,
  csat            NUMBER
);

CREATE TABLE IF NOT EXISTS SUPPORT.message (
  message_id         STRING        NOT NULL,
  conversation_id    STRING        NOT NULL,
  snowflake_user     STRING        NOT NULL,
  message_role       STRING        NOT NULL,
  content_redacted   STRING        NOT NULL,
  content_sha256     STRING        NOT NULL,
  citations          VARIANT,
  confidence         FLOAT,
  created_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS SUPPORT.intent_event (
  intent_id          STRING        NOT NULL,
  conversation_id    STRING        NOT NULL,
  snowflake_user     STRING        NOT NULL,
  situation_code     STRING        NOT NULL,
  confidence         FLOAT         NOT NULL,
  classifier_version STRING        NOT NULL,
  ambiguous          BOOLEAN       DEFAULT FALSE,
  created_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS SUPPORT.tool_invocation (
  invocation_id   STRING        NOT NULL,
  conversation_id STRING        NOT NULL,
  snowflake_user  STRING        NOT NULL,
  tool_name       STRING        NOT NULL,
  args_redacted   VARIANT,
  result_code     STRING        NOT NULL,
  requires_human  BOOLEAN       DEFAULT FALSE,
  approved_by     STRING,
  created_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS SUPPORT.escalation (
  escalation_id  STRING        NOT NULL,
  conversation_id STRING       NOT NULL,
  snowflake_user STRING        NOT NULL,
  queue          STRING        NOT NULL,
  reason_code    STRING        NOT NULL,
  priority       STRING        NOT NULL,
  summary        STRING,
  sla_due        TIMESTAMP_NTZ,
  assigned_to    STRING,
  resolved_at    TIMESTAMP_NTZ,
  created_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS SUPPORT.feedback (
  feedback_id    STRING        NOT NULL,
  conversation_id STRING       NOT NULL,
  rating         NUMBER,
  comment        STRING,
  created_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  PRIMARY KEY (feedback_id)
);

CREATE TABLE IF NOT EXISTS SUPPORT.access_log (
  access_id      STRING        NOT NULL,
  conversation_id STRING       NOT NULL,
  viewer         STRING        NOT NULL,
  role_name      STRING        NOT NULL,
  reason         STRING        NOT NULL,
  viewed_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  PRIMARY KEY (access_id)
);

-- No primary keys on row-access-policy-protected tables: Snowflake rejects
-- some constraint combinations on protected tables. Enforce natural-key
-- uniqueness in the service layer.
-- ---------------------------------------------------------------------------
-- Row access and secure views. Employees see only their own conversations;
-- support, compliance, and audit roles can see queue/audit rows.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE ROW ACCESS POLICY SUPPORT.self_or_support
  AS (snowflake_user STRING) RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('SUPPORT_AGENT', 'SUPPORT_HUMAN', 'COMPLIANCE_ADMIN', 'AUDITOR')
    OR snowflake_user = CURRENT_USER();

ALTER TABLE SUPPORT.conversation
  ADD ROW ACCESS POLICY SUPPORT.self_or_support ON (snowflake_user);

ALTER TABLE SUPPORT.message
  ADD ROW ACCESS POLICY SUPPORT.self_or_support ON (snowflake_user);

ALTER TABLE SUPPORT.intent_event
  ADD ROW ACCESS POLICY SUPPORT.self_or_support ON (snowflake_user);

ALTER TABLE SUPPORT.tool_invocation
  ADD ROW ACCESS POLICY SUPPORT.self_or_support ON (snowflake_user);

ALTER TABLE SUPPORT.escalation
  ADD ROW ACCESS POLICY SUPPORT.self_or_support ON (snowflake_user);

CREATE OR REPLACE SECURE VIEW SUPPORT.v_my_conversations AS
SELECT conversation_id, channel, release_version, started_at, ended_at, status, csat
FROM SUPPORT.conversation
WHERE snowflake_user = CURRENT_USER();

CREATE OR REPLACE SECURE VIEW SUPPORT.v_my_messages AS
SELECT m.conversation_id, m.message_role, m.content_redacted, m.citations,
       m.confidence, m.created_at
FROM SUPPORT.message m
JOIN SUPPORT.conversation c
  ON c.conversation_id = m.conversation_id
WHERE c.snowflake_user = CURRENT_USER();

CREATE OR REPLACE SECURE VIEW SUPPORT.v_support_queue AS
SELECT escalation_id, conversation_id, queue, reason_code, priority,
       sla_due, assigned_to, resolved_at, created_at
FROM SUPPORT.escalation
WHERE resolved_at IS NULL;

CREATE OR REPLACE SECURE VIEW SUPPORT.v_support_metrics AS
SELECT queue,
       COUNT(*) AS open_cases,
       COUNT_IF(priority = 'URGENT') AS urgent_cases,
       COUNT_IF(sla_due < CURRENT_TIMESTAMP()) AS overdue_cases
FROM SUPPORT.escalation
WHERE resolved_at IS NULL
GROUP BY queue;

-- ---------------------------------------------------------------------------
-- Privileges. The service can write conversations and read published KB, but
-- it has no grant on IDENTITY, raw photos, templates, centroids, or embeddings.
-- ---------------------------------------------------------------------------
GRANT USAGE ON SCHEMA SUPPORT TO ROLE SUPPORT_AGENT;
GRANT USAGE ON SCHEMA SUPPORT TO ROLE SUPPORT_HUMAN;

GRANT INSERT ON TABLE SUPPORT.conversation TO ROLE SUPPORT_AGENT;
GRANT INSERT ON TABLE SUPPORT.message TO ROLE SUPPORT_AGENT;
GRANT INSERT ON TABLE SUPPORT.intent_event TO ROLE SUPPORT_AGENT;
GRANT INSERT ON TABLE SUPPORT.tool_invocation TO ROLE SUPPORT_AGENT;
GRANT INSERT ON TABLE SUPPORT.escalation TO ROLE SUPPORT_AGENT;
GRANT INSERT ON TABLE SUPPORT.feedback TO ROLE SUPPORT_AGENT;
GRANT SELECT ON TABLE SUPPORT.kb_article TO ROLE SUPPORT_AGENT;
GRANT SELECT ON TABLE SUPPORT.kb_chunk TO ROLE SUPPORT_AGENT;
GRANT SELECT ON VIEW SUPPORT.v_support_queue TO ROLE SUPPORT_AGENT;

-- Queue assignment is enforced by the human console. Before production,
-- replace broad table reads with an assignment-scoped secure view.
GRANT SELECT ON TABLE SUPPORT.conversation TO ROLE SUPPORT_HUMAN;
GRANT SELECT ON TABLE SUPPORT.message TO ROLE SUPPORT_HUMAN;
GRANT SELECT ON TABLE SUPPORT.intent_event TO ROLE SUPPORT_HUMAN;
GRANT SELECT ON TABLE SUPPORT.tool_invocation TO ROLE SUPPORT_HUMAN;
GRANT SELECT ON TABLE SUPPORT.escalation TO ROLE SUPPORT_HUMAN;
GRANT UPDATE (assigned_to, resolved_at) ON TABLE SUPPORT.escalation TO ROLE SUPPORT_HUMAN;
GRANT INSERT ON TABLE SUPPORT.access_log TO ROLE SUPPORT_HUMAN;
GRANT SELECT ON VIEW SUPPORT.v_support_queue TO ROLE SUPPORT_HUMAN;
GRANT SELECT ON VIEW SUPPORT.v_support_metrics TO ROLE SUPPORT_HUMAN;

GRANT ALL ON SCHEMA SUPPORT TO ROLE COMPLIANCE_ADMIN;
GRANT SELECT ON TABLE SUPPORT.intent_event TO ROLE AUDITOR;
GRANT SELECT ON TABLE SUPPORT.tool_invocation TO ROLE AUDITOR;
GRANT SELECT ON TABLE SUPPORT.escalation TO ROLE AUDITOR;
GRANT SELECT ON TABLE SUPPORT.access_log TO ROLE AUDITOR;
GRANT SELECT ON VIEW SUPPORT.v_support_metrics TO ROLE AUDITOR;

-- ---------------------------------------------------------------------------
-- Operational notes
-- ---------------------------------------------------------------------------
-- 1. Publish only approved KB articles. The retrieval service must filter to
--    status = 'published' and cite article_id + version.
-- 2. Store conversation text after redact_pii; keep content_sha256 for
--    tamper evidence. Never store raw photos, embeddings, or credentials.
-- 3. The tool gateway, not the model, enforces the allowlist and derives
--    employee_id from the verified session. Do not trust request-body IDs.
-- 4. High-risk situations (consent withdrawal, photo access, appeal,
--    accommodation, fraud, break-glass) require a human decision.
-- 5. Schedule transcript retention and access reviews. Every human transcript
--    view writes SUPPORT.access_log.
-- 6. Keep SUPPORT_AGENT out of IDENTITY and out of the photo stage. Verify with
--    SHOW GRANTS and ACCESS_HISTORY before launch.
