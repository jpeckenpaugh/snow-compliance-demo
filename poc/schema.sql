-- SQLite POC schema. Deliberately mirrors the Snowflake model in sql/*.sql:
--   dimensions + fact + bridge + authorization mapping + audit.
-- Row-level access is enforced in application code (poc/access.py) exactly the
-- way a Snowflake row access policy would enforce it, so the same access map
-- ports directly.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS fact_clause;
DROP TABLE IF EXISTS bridge_matter_contract;
DROP TABLE IF EXISTS matter_authorization;
DROP TABLE IF EXISTS dim_contract;
DROP TABLE IF EXISTS dim_matter;
DROP TABLE IF EXISTS dim_client;
DROP TABLE IF EXISTS dim_employee;

-- People who can sign in. password is simulated (stored in clear for the demo).
CREATE TABLE dim_employee (
  employee_id   TEXT PRIMARY KEY,
  username      TEXT UNIQUE NOT NULL,
  password      TEXT NOT NULL,
  full_name     TEXT NOT NULL,
  role          TEXT NOT NULL,          -- attorney | paralegal | compliance_admin | auditor
  practice      TEXT
);

CREATE TABLE dim_client (
  client_id   TEXT PRIMARY KEY,
  client_name TEXT NOT NULL,
  industry    TEXT,
  region      TEXT,
  contact_email TEXT,
  contact_phone TEXT
);

CREATE TABLE dim_matter (
  matter_id             TEXT PRIMARY KEY,
  client_id             TEXT NOT NULL REFERENCES dim_client(client_id),
  matter_name           TEXT NOT NULL,
  confidentiality_level TEXT NOT NULL,
  opened_on             TEXT
);

CREATE TABLE dim_contract (
  contract_id   TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  contract_type TEXT NOT NULL,
  context_chars INTEGER
);

-- Which employees may see which matters (source of truth for row access).
CREATE TABLE matter_authorization (
  matter_id    TEXT NOT NULL REFERENCES dim_matter(matter_id),
  employee_id  TEXT NOT NULL REFERENCES dim_employee(employee_id),
  access_level TEXT NOT NULL DEFAULT 'READ',
  valid_from   TEXT,
  valid_to     TEXT,
  PRIMARY KEY (matter_id, employee_id)
);

CREATE TABLE bridge_matter_contract (
  matter_id   TEXT NOT NULL REFERENCES dim_matter(matter_id),
  contract_id TEXT NOT NULL REFERENCES dim_contract(contract_id),
  executed_on TEXT,
  PRIMARY KEY (matter_id, contract_id)
);

CREATE TABLE fact_clause (
  contract_id TEXT NOT NULL REFERENCES dim_contract(contract_id),
  category    TEXT NOT NULL,
  present     INTEGER NOT NULL,     -- 0/1
  snippet     TEXT,
  answer_start INTEGER,
  PRIMARY KEY (contract_id, category)
);

-- Every document access is recorded here (functional audit).
CREATE TABLE audit_log (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  occurred_at TEXT NOT NULL,
  username    TEXT NOT NULL,
  role        TEXT NOT NULL,
  action      TEXT NOT NULL,        -- login | view_document | view_audit | denied
  target      TEXT,                 -- document id / matter id
  outcome     TEXT NOT NULL         -- allowed | denied
);
