#!/usr/bin/env python3
"""Data-access layer for the POC.

This module is the single enforcement point. It plays the role that Snowflake row
access policies + a governed query path will play in production:
  * an access decision is made against matter_authorization, not by the caller
  * every attempt (allowed or denied) is written to audit_log
  * results are filtered before they leave the layer

The rule is intentionally identical to sql/03_row_access_and_masking.sql:
  allow if role is an oversight role, else allow if the employee is authorized
  for the matter that owns the row.
"""
import sqlite3
from datetime import datetime, timezone

OVERSIGHT_ROLES = {"compliance_admin", "auditor"}


class AuthError(Exception):
    pass


class Denied(Exception):
    pass


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(con, user, action, target, outcome):
    con.execute(
        "INSERT INTO audit_log(occurred_at,username,role,action,target,outcome) VALUES (?,?,?,?,?,?)",
        (_now(), user["username"], user["role"], action, target, outcome),
    )
    con.commit()


def authenticate(con, username, password):
    row = con.execute(
        "SELECT employee_id, username, full_name, role, practice FROM dim_employee WHERE username=?",
        (username,),
    ).fetchone()
    if row is None:
        return None
    stored = con.execute("SELECT password FROM dim_employee WHERE username=?", (username,)).fetchone()[0]
    if stored != password:
        return None
    user = {"employee_id": row[0], "username": row[1], "name": row[2], "role": row[3], "practice": row[4]}
    _log(con, user, "login", None, "allowed")
    return user


def allowed_matters(con, user):
    if user["role"] in OVERSIGHT_ROLES:
        return [r[0] for r in con.execute("SELECT matter_id FROM dim_matter")]
    return [r[0] for r in con.execute(
        "SELECT matter_id FROM matter_authorization WHERE employee_id=?", (user["employee_id"],))]


def _doc_rows(con, matter_ids):
    if not matter_ids:
        return []
    ph = ",".join("?" * len(matter_ids))
    rows = con.execute(f"""
        SELECT c.contract_id, c.title, c.contract_type, m.matter_id, m.matter_name,
               cl.client_name, m.confidentiality_level
        FROM dim_contract c
        JOIN bridge_matter_contract b ON b.contract_id = c.contract_id
        JOIN dim_matter m ON m.matter_id = b.matter_id
        JOIN dim_client cl ON cl.client_id = m.client_id
        WHERE m.matter_id IN ({ph})
        ORDER BY m.matter_name, c.title
    """, matter_ids).fetchall()
    return [{
        "contract_id": r[0], "title": r[1], "contract_type": r[2], "matter_id": r[3],
        "matter_name": r[4], "client_name": r[5], "confidentiality": r[6],
    } for r in rows]


def list_documents(con, user):
    return _doc_rows(con, allowed_matters(con, user))


def get_document(con, user, contract_id):
    doc = con.execute("""
        SELECT c.contract_id, c.title, c.contract_type, m.matter_id, m.matter_name,
               cl.client_name, m.confidentiality_level
        FROM dim_contract c
        JOIN bridge_matter_contract b ON b.contract_id = c.contract_id
        JOIN dim_matter m ON m.matter_id = b.matter_id
        JOIN dim_client cl ON cl.client_id = m.client_id
        WHERE c.contract_id = ?
    """, (contract_id,)).fetchone()
    if doc is None:
        raise Denied("unknown document")
    if doc[3] not in allowed_matters(con, user):
        _log(con, user, "view_document", contract_id, "denied")
        raise Denied("not authorized for this matter")
    _log(con, user, "view_document", contract_id, "allowed")
    clauses = con.execute(
        "SELECT category, present, snippet FROM fact_clause WHERE contract_id=? ORDER BY category",
        (contract_id,),
    ).fetchall()
    return {
        "contract_id": doc[0], "title": doc[1], "contract_type": doc[2],
        "matter_id": doc[3], "matter_name": doc[4], "client_name": doc[5],
        "confidentiality": doc[6],
        "clauses": [{"category": c[0], "present": bool(c[1]), "snippet": c[2]} for c in clauses],
    }


def get_audit(con, user, limit=200):
    if user["role"] not in OVERSIGHT_ROLES:
        _log(con, user, "view_audit", None, "denied")
        raise Denied("audit requires an oversight role")
    _log(con, user, "view_audit", None, "allowed")
    rows = con.execute(
        "SELECT occurred_at, username, role, action, target, outcome FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [{"at": r[0], "user": r[1], "role": r[2], "action": r[3], "target": r[4], "outcome": r[5]} for r in rows]


def connect(db_path="poc/db/poc.db"):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row if False else None  # tuples are fine here
    return con
