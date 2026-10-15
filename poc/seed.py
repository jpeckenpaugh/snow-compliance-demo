#!/usr/bin/env python3
"""Build the SQLite POC database and export the static demo dataset.

Reads poc/data/cuad_sample.json (produced by extract_cuad.py), generates the
synthetic law-firm layer, and writes:
  - poc/db/poc.db        (functional POC backend)
  - demo/demo_data.json  (compact dataset for the static Pages demo)

All synthetic people and matters are fictional. A fixed structure keeps the
demo reproducible. Run:  python3 poc/seed.py
"""
import json
import pathlib
import sqlite3

try:
    from risk import score_contract
except ImportError:  # imported as a package (poc.seed)
    from poc.risk import score_contract

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "poc" / "data" / "cuad_sample.json"
DB_PATH = ROOT / "poc" / "db" / "poc.db"
SCHEMA = ROOT / "poc" / "schema.sql"
DEMO_JSON = ROOT / "demo" / "demo_data.json"

USERS = [
    ("EMP-001", "alice", "demo", "Alice Norton", "attorney", "Litigation"),
    ("EMP-002", "bob", "demo", "Bob Mercier", "attorney", "Corporate"),
    ("EMP-003", "carol", "demo", "Carol Danvers", "paralegal", "Corporate"),
    ("EMP-004", "admin", "demo", "Dana Reyes", "compliance_admin", "Compliance"),
    ("EMP-005", "auditor", "demo", "Sam Okafor", "auditor", "Risk"),
]

CLIENTS = [
    ("CL-001", "SYNTHETIC Northwind Pharma", "Pharmaceuticals", "MA", "not.real@example.invalid", "+1-555-0100"),
    ("CL-002", "SYNTHETIC Helios Energy", "Energy", "TX", "not.real@example.invalid", "+1-555-0101"),
    ("CL-003", "SYNTHETIC Blue Harbor Bank", "Financial Services", "NY", "not.real@example.invalid", "+1-555-0102"),
    ("CL-004", "SYNTHETIC Vector Robotics", "Manufacturing", "CA", "not.real@example.invalid", "+1-555-0103"),
    ("CL-005", "SYNTHETIC Cedar Health", "Healthcare", "IL", "not.real@example.invalid", "+1-555-0104"),
]

# matter_id, client_id, name, confidentiality, opened
MATTERS = [
    ("SYN-1001", "CL-001", "Northwind distribution agreements", "Highly Confidential", "2024-02-11"),
    ("SYN-1002", "CL-002", "Helios licensing & supply", "Confidential", "2024-03-04"),
    ("SYN-1003", "CL-003", "Blue Harbor vendor contracts", "Highly Confidential", "2024-04-19"),
    ("SYN-1004", "CL-004", "Vector strategic alliances", "Confidential", "2024-05-27"),
    ("SYN-1005", "CL-005", "Cedar employment & endorsement", "Public", "2024-06-30"),
]

# Authorization: which users may see which matters.
AUTHORIZATIONS = [
    ("SYN-1001", "EMP-001"), ("SYN-1001", "EMP-003"),
    ("SYN-1002", "EMP-002"), ("SYN-1002", "EMP-003"),
    ("SYN-1003", "EMP-001"), ("SYN-1003", "EMP-002"),
    ("SYN-1004", "EMP-002"),
    ("SYN-1005", "EMP-001"), ("SYN-1005", "EMP-003"),
]

def main() -> None:
    payload = json.loads(DATA.read_text())
    contracts = payload["contracts"]
    annotations = payload["annotations"]

    ann_by_contract = {}
    for a in annotations:
        ann_by_contract.setdefault(a["contract_id"], []).append(a)

    # Assign contracts to matters round-robin over the 5 matters.
    matter_ids = [m[0] for m in MATTERS]
    attachment = {}
    for i, c in enumerate(contracts):
        attachment[c["contract_id"]] = matter_ids[i % len(matter_ids)]

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA.read_text())

    con.executemany("INSERT INTO dim_employee VALUES (?,?,?,?,?,?)", USERS)
    con.executemany("INSERT INTO dim_client VALUES (?,?,?,?,?,?)", CLIENTS)
    con.executemany("INSERT INTO dim_matter VALUES (?,?,?,?,?)", MATTERS)
    con.executemany("INSERT INTO matter_authorization(matter_id,employee_id,access_level,valid_from,valid_to) VALUES (?,?,'READ','2024-01-01',NULL)", AUTHORIZATIONS)
    con.executemany(
        "INSERT INTO dim_contract(contract_id,title,contract_type,context_chars) VALUES (?,?,?,?)",
        [(c["contract_id"], c["title"], c["contract_type"], c["context_chars"]) for c in contracts],
    )
    con.executemany(
        "INSERT INTO bridge_matter_contract(matter_id,contract_id,executed_on) VALUES (?,?,?)",
        [(attachment[c["contract_id"]], c["contract_id"], "2024-06-01") for c in contracts],
    )
    con.executemany(
        "INSERT INTO fact_clause(contract_id,category,present,snippet,answer_start) VALUES (?,?,?,?,?)",
        [(a["contract_id"], a["category"], 1 if a["present"] else 0, a["snippet"], a["answer_start"]) for a in annotations],
    )
    con.commit()

    # --- Export compact dataset for the static Pages demo -------------------
    matter_by_id = {m[0]: m for m in MATTERS}
    client_by_id = {c[0]: c for c in CLIENTS}
    present_by_contract = {
        cid: {a["category"] for a in anns if a["present"]}
        for cid, anns in ann_by_contract.items()
    }
    docs = []
    for c in contracts:
        mid = attachment[c["contract_id"]]
        cats = sorted(present_by_contract.get(c["contract_id"], set()))
        score, band, drivers = score_contract(cats)
        clauses = sorted(
            ({"category": a["category"], "snippet": a["snippet"].strip()}
             for a in ann_by_contract.get(c["contract_id"], [])
             if a["present"] and (a["snippet"] or "").strip()),
            key=lambda x: x["category"],
        )
        docs.append({
            "contract_id": c["contract_id"],
            "title": c["title"],
            "contract_type": c["contract_type"],
            "matter_id": mid,
            "matter_name": matter_by_id[mid][2],
            "client_name": client_by_id[matter_by_id[mid][1]][1],
            "confidentiality": matter_by_id[mid][3],
            "risk_score": score,
            "risk_band": band,
            "risk_drivers": drivers,
            "present_categories": cats,
            "clauses": clauses,
        })

    # A small pre-seeded audit history so the admin view is meaningful on first load.
    seed_audit = [
        ("2026-10-15T09:12:04Z", "alice", "attorney", "login", None, "allowed"),
        ("2026-10-15T09:12:19Z", "alice", "attorney", "view_document", "CUAD-0000", "allowed"),
        ("2026-10-15T09:13:02Z", "bob", "attorney", "login", None, "allowed"),
        ("2026-10-15T09:13:20Z", "bob", "attorney", "view_document", "CUAD-0000", "denied"),
        ("2026-10-15T09:20:41Z", "carol", "paralegal", "login", None, "allowed"),
        ("2026-10-15T09:21:07Z", "carol", "paralegal", "view_document", "CUAD-0006", "allowed"),
        ("2026-10-15T09:30:00Z", "admin", "compliance_admin", "view_audit", None, "allowed"),
    ]
    DEMO_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEMO_JSON.write_text(json.dumps({
        "generated_from": payload["source"],
        "users": [{"username": u[1], "name": u[3], "role": u[4], "practice": u[5]} for u in USERS],
        "matters": [{"matter_id": m[0], "name": m[2], "client": client_by_id[m[1]][1],
                     "confidentiality": m[3]} for m in MATTERS],
        "authorizations": {u[1]: [a[0] for a in AUTHORIZATIONS if a[1] == u[0]] for u in USERS},
        "clients": [{"client_id": c[0], "client_name": c[1], "industry": c[2],
                     "contact_email": c[4], "contact_phone": c[5]} for c in CLIENTS],
        "documents": docs,
        "seed_audit": [{"at": a[0], "user": a[1], "role": a[2], "action": a[3],
                        "target": a[4], "outcome": a[5]} for a in seed_audit],
    }, indent=1))

    con.close()
    print(f"wrote {DB_PATH} and {DEMO_JSON}")
    print(f"contracts={len(contracts)} matters={len(MATTERS)} users={len(USERS)}")


if __name__ == "__main__":
    main()
