#!/usr/bin/env python3
"""Offline portability harness for the Snowflake compliance-demo DDL.

Runs every statement in ``sql/01_database_and_roles.sql`` ...
``sql/05_audit_queries.sql`` through `fakesnow
<https://pypi.org/project/fakesnow/>`_, which executes Snowflake SQL on
DuckDB. No Snowflake account is required.

Why this exists
---------------
The Snowflake component of the demo is simulated for now (see
``docs/PLAN.md`` section 12). fakesnow can prove that our DDL *parses and
runs* against a Snowflake-flavoured engine, but it does **not** implement
Snowflake governance or account administration. Constructs such as row
access policies, masking policies, warehouses, roles, grants and
``SNOWFLAKE.ACCOUNT_USAGE`` views are therefore expected to fail offline.

This harness runs each statement, classifies failures into:

* ``ok``          -- executed successfully;
* ``unsupported`` -- a construct fakesnow/DuckDB knowingly cannot run
                     (matched against :data:`KNOWN_UNSUPPORTED`);
* ``FAIL``        -- anything else, which is treated as a regression.

The process exits non-zero only when an unexpected ``FAIL`` appears, so it
is safe to use as a CI gate: SQL that fakesnow *can* run must keep running.

Usage
-----
    python3 scripts/run_sql_offline.py              # execute sql/*.sql
    python3 scripts/run_sql_offline.py --dry-run    # list statements only
    python3 scripts/run_sql_offline.py --json report.json
    python3 scripts/run_sql_offline.py --allow-missing-fakesnow

``--dry-run`` never imports fakesnow, so it works in constrained
environments where ``pip install`` is unavailable.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SQL_DIR = os.path.join(REPO_ROOT, "sql")

# Constructs that offline emulators (fakesnow -> DuckDB) cannot execute.
# Each entry is (compiled pattern, human-readable reason). Matching is done
# against the comment-stripped, whitespace-collapsed statement.
KNOWN_UNSUPPORTED: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"^CREATE\s+(OR\s+REPLACE\s+)?WAREHOUSE\b", re.I),
     "account-level DDL: warehouses"),
    (re.compile(r"^CREATE\s+(OR\s+REPLACE\s+)?ROLE\b", re.I),
     "account-level DDL: roles"),
    (re.compile(r"^(GRANT|REVOKE)\b", re.I),
     "privilege grants: RBAC is not emulated"),
    (re.compile(r"^CREATE\s+(OR\s+REPLACE\s+)?ROW\s+ACCESS\s+POLICY\b", re.I),
     "governance: row access policy definition"),
    (re.compile(r"^ALTER\s+TABLE\b.*\bROW\s+ACCESS\s+POLICY\b", re.I),
     "governance: row access policy attachment"),
    (re.compile(r"^CREATE\s+(OR\s+REPLACE\s+)?MASKING\s+POLICY\b", re.I),
     "governance: masking policy definition"),
    (re.compile(r"^ALTER\s+TABLE\b.*\bMASKING\s+POLICY\b", re.I),
     "governance: masking policy attachment"),
    (re.compile(r"\bSNOWFLAKE\.ACCOUNT_USAGE\b", re.I),
     "account usage views: not present offline"),
    (re.compile(r"\bINFORMATION_SCHEMA\.POLICY_REFERENCES\b", re.I),
     "policy-reference metadata view: not present offline"),
]

OK = "ok"
UNSUPPORTED = "unsupported"
FAIL = "FAIL"


@dataclass
class Statement:
    file: str
    index: int
    sql: str

    @property
    def preview(self) -> str:
        first = self.sql.strip().splitlines()[0] if self.sql.strip() else ""
        first = re.sub(r"\s+", " ", first).strip()
        return first if len(first) <= 72 else first[:69] + "..."


@dataclass
class Result:
    statement: Statement
    status: str
    reason: str = ""
    detail: str = ""


@dataclass
class Report:
    results: List[Result] = field(default_factory=list)
    files: List[str] = field(default_factory=list)

    def counts(self) -> Tuple[int, int, int]:
        ok = sum(1 for r in self.results if r.status == OK)
        unsupported = sum(1 for r in self.results if r.status == UNSUPPORTED)
        failed = sum(1 for r in self.results if r.status == FAIL)
        return ok, unsupported, failed


def split_statements(text: str) -> List[str]:
    """Split a SQL script into statements on ``;``.

    Handles ``--`` line comments, ``/* */`` block comments and single-quoted
    string literals (including the doubled ``''`` escape). Comments are
    dropped, so a statement is returned without its explanatory commentary.
    """
    statements: List[str] = []
    buf: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "-" and i + 1 < n and text[i + 1] == "-":
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        if c == "'":
            buf.append(c)
            i += 1
            while i < n:
                buf.append(text[i])
                if text[i] == "'":
                    if i + 1 < n and text[i + 1] == "'":
                        buf.append(text[i + 1])
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            continue
        if c == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    trailing = "".join(buf).strip()
    if trailing:
        statements.append(trailing)
    return statements


def discover_files(sql_dir: str, files: Optional[Iterable[str]]) -> List[str]:
    if files:
        return [os.path.abspath(f) for f in files]
    if not os.path.isdir(sql_dir):
        return []
    return sorted(
        os.path.join(sql_dir, name)
        for name in os.listdir(sql_dir)
        if name.endswith(".sql")
    )


def load_statements(paths: Iterable[str]) -> List[Statement]:
    statements: List[Statement] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        for idx, stmt in enumerate(split_statements(text), start=1):
            statements.append(Statement(os.path.basename(path), idx, stmt))
    return statements


def classify_unsupported(sql: str) -> Optional[str]:
    for pattern, reason in KNOWN_UNSUPPORTED:
        if pattern.search(sql):
            return reason
    return None


def _print_dry_run(statements: List[Statement]) -> None:
    print("Offline SQL harness -- dry run (no execution)")
    print(f"  sql directory : {DEFAULT_SQL_DIR}")
    print(f"  statements    : {len(statements)}")
    print()
    current = None
    for stmt in statements:
        if stmt.file != current:
            current = stmt.file
            print(f"[{current}]")
        first = stmt.sql.strip().splitlines()[0] if stmt.sql.strip() else ""
        first = re.sub(r"\s+", " ", first).strip()
        print(f"  {stmt.index:>3}  {first}")


def _import_fakesnow():
    """Import fakesnow, returning (fakesnow, connector) or raising ImportError."""
    import fakesnow  # noqa: F401
    import snowflake.connector  # noqa: F401

    return fakesnow, snowflake.connector


def run(statements: List[Statement]) -> Report:
    fakesnow, connector = _import_fakesnow()

    # fakesnow/sqlglot emit "unsupported syntax" warnings for the very
    # constructs we classify ourselves; keep the report readable.
    for name in ("fakesnow", "sqlglot"):
        logging.getLogger(name).setLevel(logging.CRITICAL)

    report = Report()
    with fakesnow.patch():
        conn = connector.connect()
        try:
            cursor = conn.cursor()
            try:
                for stmt in statements:
                    try:
                        cursor.execute(stmt.sql)
                        report.results.append(Result(stmt, OK))
                    except Exception as exc:  # noqa: BLE001 - report, never crash
                        reason = classify_unsupported(stmt.sql)
                        detail = re.sub(r"\s+", " ", str(exc)).strip()
                        if reason:
                            report.results.append(
                                Result(stmt, UNSUPPORTED, reason=reason, detail=detail)
                            )
                        else:
                            report.results.append(
                                Result(stmt, FAIL, detail=detail)
                            )
            finally:
                cursor.close()
        finally:
            conn.close()
    return report


def _emit(report: Report, verbose: bool) -> None:
    current = None
    for res in report.results:
        if res.statement.file != current:
            current = res.statement.file
            print(f"[{current}]")
        line = f"  {res.status:<11} {res.statement.index:>3}  {res.statement.preview}"
        if res.status == UNSUPPORTED:
            line += f"   ({res.reason})"
        print(line)
        if res.status == FAIL or (verbose and res.detail):
            print(f"      -> {res.detail}")
    print()

    ok, unsupported, failed = report.counts()
    print("Summary")
    print(f"  files             : {len({r.statement.file for r in report.results})}")
    print(f"  statements        : {len(report.results)}")
    print(f"  ok                : {ok}")
    print(f"  known-unsupported : {unsupported}")
    print(f"  unexpected FAIL   : {failed}")
    print()
    if failed:
        print(
            f"{failed} statement(s) failed that fakesnow/DuckDB should support. "
            "Inspect the FAIL lines above."
        )
    else:
        print(
            "No unexpected failures. Offline portability check passed "
            f"({unsupported} construct(s) expected unsupported offline)."
        )


def _write_json(path: str, report: Report) -> None:
    payload = {
        "counts": dict(zip(("ok", "unsupported", "unexpected_fail"), report.counts())),
        "results": [
            {
                "file": r.statement.file,
                "index": r.statement.index,
                "status": r.status,
                "reason": r.reason,
                "detail": r.detail,
                "sql": r.statement.sql,
            }
            for r in report.results
        ],
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Snowflake DDL through fakesnow (DuckDB) offline.",
    )
    parser.add_argument("--sql-dir", default=DEFAULT_SQL_DIR,
                        help="directory of .sql files (default: <repo>/sql)")
    parser.add_argument("--files", nargs="+", metavar="PATH",
                        help="explicit .sql files to run (overrides --sql-dir)")
    parser.add_argument("--dry-run", action="store_true",
                        help="split and list statements without executing; "
                             "does not require fakesnow")
    parser.add_argument("--allow-missing-fakesnow", action="store_true",
                        help="if fakesnow is unavailable, fall back to listing "
                             "statements and exit 0 instead of erroring")
    parser.add_argument("--json", metavar="PATH",
                        help="also write a machine-readable JSON report")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show error detail for every non-ok statement")
    args = parser.parse_args(argv)

    paths = discover_files(args.sql_dir, args.files)
    statements = load_statements(paths)

    if not statements:
        print(f"No .sql files found under {args.sql_dir}", file=sys.stderr)
        return 1

    if args.dry_run:
        _print_dry_run(statements)
        return 0

    try:
        report = run(statements)
    except ImportError as exc:
        print("fakesnow is not available in this environment.", file=sys.stderr)
        print(f"  reason: {exc}", file=sys.stderr)
        print(file=sys.stderr)
        print("Install it with:", file=sys.stderr)
        print("  python3 -m pip install 'snowflake-connector-python<4' fakesnow",
              file=sys.stderr)
        print("Note: snowflake-connector-python 5.x is not yet compatible with "
              "fakesnow (it removed snowflake.connector.converter).", file=sys.stderr)
        print("Or run without executing: python3 scripts/run_sql_offline.py --dry-run",
              file=sys.stderr)
        if args.allow_missing_fakesnow:
            print(file=sys.stderr)
            print("--allow-missing-fakesnow set: listing statements instead.",
                  file=sys.stderr)
            _print_dry_run(statements)
            return 0
        return 2

    _emit(report, args.verbose)
    if args.json:
        _write_json(args.json, report)

    _, _, failed = report.counts()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
