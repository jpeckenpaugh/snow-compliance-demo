#!/usr/bin/env python3
"""Simulated Snowflake engine for the demo.

No Snowflake account is required. This module emulates the parts of Snowflake
that matter for the demo, on top of SQLite:

  * session role context           (USE ROLE)
  * a row access policy            (sec.matter_access_policy over matter_id)
  * a masking policy               (sec.pii_mask over client contact columns)
  * a query history                (mirrors SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY)
  * policy references              (mirrors INFORMATION_SCHEMA.POLICY_REFERENCES)

It is a simulation, not an emulator of Snowflake SQL. The real DDL lives in
sql/*.sql and ports to a Snowflake trial account unchanged. What this file makes
demonstrable offline is the *governance behaviour*: rows filtered by role,
columns masked by role, and every statement logged.
"""
import sqlite3
import uuid
from datetime import datetime, timezone

try:
    from risk import score_contract
except ImportError:  # imported as a package (poc.snowflake_sim)
    from poc.risk import score_contract

OVERSIGHT_ROLES = {"COMPLIANCE_ADMIN", "AUDITOR", "ACCOUNTADMIN", "SYSADMIN"}
MASKED_ROLES = {"ATTORNEY_ALICE", "ATTORNEY_BOB", "PARALEGAL_CAROL"}

# role -> employee_id (oversight roles see everything)
ROLE_EMPLOYEE = {
    "ATTORNEY_ALICE": "EMP-001",
    "ATTORNEY_BOB": "EMP-002",
    "PARALEGAL_CAROL": "EMP-003",
    "COMPLIANCE_ADMIN": None,
    "AUDITOR": None,
}

MASK = "***REDACTED***"

# Predefined statements, each tagged with the policy it exercises.
QUERIES = {
    "documents": {
        "label": "Documents per matter",
        "sql": ("SELECT matter_id, matter_name, contract_id, contract_type\n"
                "FROM marts.v_matter_documents;"),
        "policy": "row access: sec.matter_access_policy ON (matter_id)",
    },
    "clauses": {
        "label": "Clause categories present",
        "sql": ("SELECT contract_id, matter_id, category\n"
                "FROM core.fact_clause WHERE present = 1;"),
        "policy": "row access: sec.matter_access_policy ON (matter_id)",
    },
    "risk_register": {
        "label": "Risk register (high-risk clauses by matter)",
        "sql": ("SELECT matter_id, matter_name, contract_id, contract_type,\n"
                "       risk_score, risk_band, high_risk_clauses\n"
                "FROM marts.mart_high_risk_register\n"
                "ORDER BY risk_score DESC;"),
        "policy": "row access: sec.matter_access_policy ON (matter_id)",
    },
    "clients": {
        "label": "Client contacts (masked)",
        "sql": ("SELECT client_id, client_name, contact_email, contact_phone\n"
                "FROM core.dim_client;"),
        "policy": "masking: sec.pii_mask ON (contact_email, contact_phone)",
    },
    "query_history": {
        "label": "Query history",
        "sql": ("SELECT query_id, role_name, query_text, rows_produced, status\n"
                "FROM snowflake.account_usage.query_history ORDER BY start_time DESC;"),
        "policy": "governed view: oversight roles only",
    },
}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_history(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
          query_id TEXT PRIMARY KEY, start_time TEXT, role_name TEXT, query_text TEXT,
          rows_produced INTEGER, status TEXT, error_message TEXT
        )""")
    con.commit()


def _allowed_matters(con, role):
    if role in OVERSIGHT_ROLES or ROLE_EMPLOYEE.get(role) is None:
        return [r[0] for r in con.execute("SELECT matter_id FROM dim_matter")]
    emp = ROLE_EMPLOYEE[role]
    return [r[0] for r in con.execute(
        "SELECT matter_id FROM matter_authorization WHERE employee_id=?", (emp,))]


def _record(con, role, sql, rows, status, err=None):
    qid = str(uuid.uuid4())
    con.execute("INSERT INTO query_history VALUES (?,?,?,?,?,?,?)",
                (qid, _now(), role, sql, rows, status, err))
    con.commit()
    return qid


def list_roles():
    return list(ROLE_EMPLOYEE.keys())


def list_queries():
    return [{"key": k, "label": v["label"], "sql": v["sql"], "policy": v["policy"]}
            for k, v in QUERIES.items()]


def run(con, role, key):
    """Execute a predefined statement under a simulated role. Returns a result dict."""
    _ensure_history(con)
    if role not in ROLE_EMPLOYEE:
        return {"status": "DENIED", "error": f"unknown role {role}", "columns": [], "rows": []}
    if key not in QUERIES:
        return {"status": "DENIED", "error": f"unknown query {key}", "columns": [], "rows": []}
    spec = QUERIES[key]
    sql = spec["sql"]

    # --- governed view: query history requires oversight ---
    if key == "query_history":
        if role not in OVERSIGHT_ROLES:
            qid = _record(con, role, sql, 0, "DENIED", "insufficient privileges")
            return {"status": "DENIED", "error": "insufficient privileges to operate on view 'QUERY_HISTORY'",
                    "query_id": qid, "sql": sql, "policy": spec["policy"], "columns": [], "rows": []}
        cols = ["query_id", "role_name", "query_text", "rows_produced", "status"]
        rows = con.execute("SELECT query_id, role_name, query_text, rows_produced, status "
                           "FROM query_history ORDER BY start_time DESC").fetchall()
        rows = [list(r) for r in rows]
        qid = _record(con, role, sql, len(rows), "SUCCESS")
        return {"status": "SUCCESS", "query_id": qid, "sql": sql, "policy": spec["policy"],
                "columns": cols, "rows": rows}

    matters = _allowed_matters(con, role)
    mset = set(matters)

    if key == "documents":
        cols = ["matter_id", "matter_name", "contract_id", "contract_type"]
        raw = con.execute(
            "SELECT m.matter_id, m.matter_name, c.contract_id, c.contract_type "
            "FROM dim_matter m JOIN bridge_matter_contract b ON b.matter_id=m.matter_id "
            "JOIN dim_contract c ON c.contract_id=b.contract_id").fetchall()
        rows = [list(r) for r in raw if r[0] in mset]        # matter_id at index 0
    elif key == "clauses":
        cols = ["contract_id", "matter_id", "category"]
        raw = con.execute(
            "SELECT f.contract_id, b.matter_id, f.category FROM fact_clause f "
            "JOIN bridge_matter_contract b ON b.contract_id=f.contract_id WHERE f.present=1").fetchall()
        rows = [list(r) for r in raw if r[1] in mset]        # matter_id at index 1
    elif key == "risk_register":
        cols = ["matter_id", "matter_name", "contract_id", "contract_type",
                "risk_score", "risk_band", "high_risk_clauses"]
        present = {}
        for cid, cat in con.execute("SELECT contract_id, category FROM fact_clause WHERE present=1"):
            present.setdefault(cid, set()).add(cat)
        raw = con.execute(
            "SELECT m.matter_id, m.matter_name, c.contract_id, c.contract_type "
            "FROM dim_matter m JOIN bridge_matter_contract b ON b.matter_id=m.matter_id "
            "JOIN dim_contract c ON c.contract_id=b.contract_id").fetchall()
        rows = []
        for mid, mname, cid, ctype in raw:
            if mid not in mset:                              # row access at matter_id (index 0)
                continue
            score, band, drivers = score_contract(present.get(cid, set()))
            rows.append([mid, mname, cid, ctype, score, band, ", ".join(drivers)])
        rows.sort(key=lambda r: (-r[4], r[0], r[2]))
    elif key == "clients":
        cols = ["client_id", "client_name", "contact_email", "contact_phone"]
        rows = [list(r) for r in con.execute(
            "SELECT client_id, client_name, contact_email, contact_phone FROM dim_client")]
        if role in MASKED_ROLES:
            for r in rows:
                r[2] = MASK
                r[3] = MASK
    else:
        return {"status": "ERROR", "error": "unhandled query", "columns": [], "rows": []}

    qid = _record(con, role, sql, len(rows), "SUCCESS")
    return {"status": "SUCCESS", "query_id": qid, "sql": sql, "policy": spec["policy"],
            "columns": cols, "rows": [list(r) for r in rows],
            "row_access_applied": role not in OVERSIGHT_ROLES}


def policy_references(con):
    return [
        {"policy_name": "MATTER_ACCESS_POLICY", "policy_kind": "ROW_ACCESS_POLICY",
         "ref_entity_name": "CORE.FACT_CLAUSE", "ref_column_name": "MATTER_ID"},
        {"policy_name": "MATTER_ACCESS_POLICY", "policy_kind": "ROW_ACCESS_POLICY",
         "ref_entity_name": "CORE.DIM_MATTER", "ref_column_name": "MATTER_ID"},
        {"policy_name": "MATTER_ACCESS_POLICY", "policy_kind": "ROW_ACCESS_POLICY",
         "ref_entity_name": "CORE.BRIDGE_MATTER_CONTRACT", "ref_column_name": "MATTER_ID"},
        {"policy_name": "PII_MASK", "policy_kind": "MASKING_POLICY",
         "ref_entity_name": "CORE.DIM_CLIENT", "ref_column_name": "CONTACT_EMAIL"},
        {"policy_name": "PII_MASK", "policy_kind": "MASKING_POLICY",
         "ref_entity_name": "CORE.DIM_CLIENT", "ref_column_name": "CONTACT_PHONE"},
    ]


def connect(db_path="poc/db/poc.db"):
    return sqlite3.connect(db_path)
