# Offline SQL Portability Harness

**Scope:** everything in [`sql/`](../sql) — the Snowflake DDL for the
compliance demo (`01_database_and_roles.sql` … `05_audit_queries.sql`).

The Snowflake component of the demo is **simulated for now** (no Snowflake
account; see [PLAN.md](PLAN.md) §12). This harness proves the DDL *runs on a
Snowflake-flavoured engine* and keeps it from regressing, without an account.

- Harness: [`scripts/run_sql_offline.py`](../scripts/run_sql_offline.py)
- CI: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) → job **Offline SQL portability**

## What the harness does

[`fakesnow`](https://pypi.org/project/fakesnow/) implements the Snowflake
Python connector on top of **DuckDB**. The harness:

1. splits every `sql/*.sql` file into individual statements;
2. executes them in filename order on a single fakesnow session;
3. classifies each statement as `ok`, `unsupported`, or `FAIL`;
4. prints a per-statement report and a summary, and writes the same data as
   JSON with `--json`;
5. exits non-zero **only** when a statement fakesnow/DuckDB should support
   fails — so it is a usable CI gate.

### Important limitation

fakesnow runs SQL; it does **not** implement Snowflake's governance or
account administration. It cannot enforce a row access policy, mask a
column, resolve `CURRENT_ROLE()`, or read `SNOWFLAKE.ACCOUNT_USAGE`. Those
statements are therefore reported as *known-unsupported* (not failures).
Consequently this harness proves **syntactic/runtime portability of the
supported SQL**, not the matter wall itself. Proving the wall requires a
real Snowflake trial (see [Migration path](#migration-path-to-a-real-snowflake-trial)).

## Running it

```bash
# Execute sql/*.sql through fakesnow (default).
python3 scripts/run_sql_offline.py

# List statements without executing — no fakesnow needed.
python3 scripts/run_sql_offline.py --dry-run

# Also write a machine-readable report.
python3 scripts/run_sql_offline.py --json offline-sql-report.json

# Run a subset.
python3 scripts/run_sql_offline.py --files sql/04_risk_views.sql
```

### Installing fakesnow

```bash
python3 -m pip install "snowflake-connector-python<4" fakesnow
```

> **Version pin required.** fakesnow declares an *unpinned*
> `snowflake-connector-python` dependency, but `snowflake-connector-python`
> **5.x** relocated `snowflake.connector.converter`, which fakesnow imports,
> so the two are currently incompatible. Pin the connector to `<4` (3.18.1
> is known good with fakesnow 0.11.22). The CI workflow pins it too.

### Flags

| Flag | Effect |
| --- | --- |
| `--dry-run` | Split and list statements, execute nothing. Works without fakesnow. |
| `--allow-missing-fakesnow` | If fakesnow is missing, fall back to listing statements and exit `0` instead of erroring. |
| `--json PATH` | Write a JSON report (counts + every statement's status). |
| `--files PATH…` | Run specific `.sql` files instead of all of `sql/`. |
| `--sql-dir DIR` | Use a different SQL directory. |
| `-v`, `--verbose` | Print error detail for every non-`ok` statement. |

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | No unexpected failures (known-unsupported statements are fine). |
| `1` | An unexpected `FAIL` occurred, or no `.sql` files were found. |
| `2` | fakesnow is not installed and `--allow-missing-fakesnow` was not passed. |

## Known-unsupported constructs

Matched by `KNOWN_UNSUPPORTED` in the harness. Counts below are from the
current `sql/` set (91 statements: **45 `ok`, 46 known-unsupported, 0 FAIL**).

| Construct | Statements | Reason |
| --- | --- | --- |
| `GRANT` / `REVOKE` | 26 | RBAC is not emulated |
| `CREATE ROLE` | 5 | account-level DDL: roles |
| `ALTER TABLE … ADD ROW ACCESS POLICY` | 5 | governance: policy attachment |
| `SNOWFLAKE.ACCOUNT_USAGE.*` | 3 | account usage views not present offline |
| `CREATE WAREHOUSE` | 2 | account-level DDL: warehouses |
| `ALTER TABLE … SET MASKING POLICY` | 2 | governance: masking attachment |
| `CREATE ROW ACCESS POLICY` | 1 | governance: policy definition |
| `CREATE MASKING POLICY` | 1 | governance: masking definition |
| `INFORMATION_SCHEMA.POLICY_REFERENCES` | 1 | metadata view not present offline |

Everything fakesnow *can* run does run: database/schema creation, all `RAW`
and `CORE` tables (including `CREATE TABLE … AS SELECT`, `VARIANT`,
`TIMESTAMP_NTZ DEFAULT`), `INSERT OVERWRITE`, `CREATE TAG` and `SET TAG`,
and the two `MARTS` risk views (`SUM(CASE …)`, `ILIKE`, `||`).

If a construct that fakesnow *should* handle starts failing, the harness
exits `1`. To acknowledge a newly-unsupported construct, add it to
`KNOWN_UNSUPPORTED` **with a reason** — never widen the list silently.

## CI

`.github/workflows/ci.yml` runs on every push to `main` and on every pull
request:

- **Offline SQL portability** — Python 3.12, installs
  `snowflake-connector-python<4` + `fakesnow`, runs
  `python3 scripts/run_sql_offline.py --json offline-sql-report.json`, and
  uploads the report as a build artifact.
- **Python syntax check** — `python3 -m py_compile poc/*.py build_site.py`.

A change that breaks the supported DDL fails the workflow.

## Verification status (this environment)

What was verified **with fakesnow installed**:

- all 91 statements split correctly (91 == 91 across the five files);
- 45 statements execute successfully, 46 are classified known-unsupported,
  0 unexplained failures, exit code `0`;
- the regression path was exercised: a deliberately malformed file produced
  `unexpected FAIL` and exit code `1`;
- `--dry-run` works with no fakesnow present; the missing-fakesnow path exits
  `2` with install guidance, and `--allow-missing-fakesnow` falls back to the
  statement listing with exit `0`;
- the workflow YAML parses (`yaml.safe_load`) with two jobs and the expected
  steps; `python3 -m py_compile poc/*.py build_site.py` succeeds.

What could **not** be tested offline:

- row access policy / masking **enforcement** (fakesnow ignores them);
- RBAC resolution (`CURRENT_ROLE()`, `GRANT` semantics);
- the `SNOWFLAKE.ACCOUNT_USAGE` and `POLICY_REFERENCES` audit queries
  actually returning rows;
- the risk views evaluated *per role* (that is what the matter wall changes).

Environment notes: `pip3` is not on `PATH` and the interpreter is
`externally-managed` (PEP 668), and `venv` was created without `pip`. The
harness was therefore verified by installing fakesnow into a scratch
`--target` directory and running with `PYTHONPATH` set; no repository files
depend on that. `--dry-run` and `--allow-missing-fakesnow` cover constrained
environments.

## Migration path to a real Snowflake trial

1. **Sign up** for the free 30-day Snowflake trial (Enterprise Edition, $400
   credits, no credit card). Enterprise Edition is required for row access
   policies and masking. Use an isolated demo account.
2. **Run the DDL unchanged**, in order, as `ACCOUNTADMIN` (or a role with the
   needed `CREATE`/`GRANT` privileges): `01 → 02 → 03 → 04 → 05`. Snowsight
   worksheets or `snowsql -f <file>` both work.
3. **Expect every statement to succeed.** On a real account the constructs
   this harness marks unsupported — warehouses, roles, grants, row access and
   masking policies — execute for real.
4. **Prove the wall** (§12 of PLAN.md): run the `MARTS.mart_high_risk_register`
   query under `ATTORNEY_0` and `ATTORNEY_1` and confirm different row sets;
   confirm `dim_client.contact_email` is masked per role; query
   `INFORMATION_SCHEMA.POLICY_REFERENCES`, `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY`
   and `ACCESS_HISTORY` (allow ~45 min for `ACCOUNT_USAGE` latency).
5. **Keep the cost near zero:** warehouses are `XSMALL` with
   `AUTO_SUSPEND = 60`; `WH_LOAD`/`WH_ANALYTICS` start suspended.
6. **Tear down** when done: `DROP DATABASE SNOW_COMPLIANCE_DEMO;`,
   `DROP WAREHOUSE WH_LOAD;`, `DROP WAREHOUSE WH_ANALYTICS;`, and the demo
   roles. Store credentials in Paperclip secrets, never in the repo.

No SQL changes are required between the offline harness and the trial — the
same files are the source of truth. The harness remains useful afterwards as
a fast, account-free CI gate; the trial is the faithful end-to-end validation.
