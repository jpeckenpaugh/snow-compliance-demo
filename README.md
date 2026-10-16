# snow-compliance-demo

Board-review staging for a **Snowflake legal-compliance demonstration** built on the
public [CUAD](https://github.com/The-Atticus-Project/cuad) dataset plus synthetic
law-firm records.

**Live site:** https://jpeckenpaugh.github.io/snow-compliance-demo/

Any push to `main` republishes the site (GitHub Pages, legacy build from `/`).

## What's here

| Path | Purpose |
| --- | --- |
| `index.html` … `full-dataset.html` | The board-review site (generated). |
| `build_site.py` | Regenerates the HTML from embedded content. `python3 build_site.py` |
| `docs/PLAN.md` | Canonical Markdown plan (same content as the site). |
| `docs/FULL_DATASET_ROADMAP.md` | Approved full-dataset report & recommendation. |
| `docs/SNOWFLAKE_WALKTHROUGH.md` | Manual, no-API Snowsight runbook for the full dataset. |
| `sql/01…05*.sql` | Snowflake DDL: setup, model, security, risk, audit. |
| `sql/full_dataset/06_full_dataset.sql` | Consolidated full-dataset load/normalize/RBAC/risk SQL. |
| `ingest/load_cuad.py` | Parses CUAD JSON into RAW CSVs. |
| `ingest/split_cuad_json.py` | Splits the full CUAD JSON into NDJSON for the Snowflake `VARIANT` load. |
| `ingest/generate_synthetic_data.py` | Faker generator for fictional firm records. |
| `poc/` | **Working Python + SQLite proof of concept** (see below). |
| `demo/index.html` | Board-clickable interactive login/audit demo (static). |

## Proof of concept (`poc/`)

A functional POC that enforces matter-level access control and records an audit log,
built to port directly to Snowflake.

```bash
python3 poc/extract_cuad.py --limit 20   # fetch + normalize the first 20 CUAD docs
python3 poc/seed.py                      # build the SQLite DB + demo data
python3 poc/build_demo.py                # regenerate demo/index.html
python3 poc/server.py                    # functional POC at http://localhost:8000
```

Users: `alice`, `bob`, `carol`, `admin`, `auditor` — password `demo`.

- `poc/access.py` is the enforcement point (authorization check + audit).
- `poc/snowflake_sim.py` simulates Snowflake role context, row access policy, masking,
  and query history offline — no Snowflake account required.
- `poc/analysis/cuad_shape_report.md` documents the real CUAD shape vs. the plan.

The Snowflake component is **simulated for now** (see `snowflake-options.html` on the site):
offline emulators (fakesnow, LocalStack, snowflake-emulator, DuckDB) run SQL but do *not*
enforce governance; a free 30-day Snowflake trial is the only faithful way to validate row
access policies and masking. We simulate now and validate on a trial when approved.

## Full dataset (`full-dataset.html`, `docs/`)

Approved 2026-10-16: scale to all **510 CUAD contracts / 20,910 clause annotations**, normalized
**inside Snowflake with no API**, with the simulated RBAC + risk metadata at 510 matters and a
Streamlit-in-Snowflake app on a trial account.

1. `python3 ingest/split_cuad_json.py --json CUADv1.json --out build/cuad_docs.jsonl`
2. Upload to `@RAW.cuad_stage` and run `sql/full_dataset/06_full_dataset.sql`.
3. Follow `docs/SNOWFLAKE_WALKTHROUGH.md` end to end (load → normalize → synthetic layer →
   RBAC → risk → verify → teardown). `docs/FULL_DATASET_ROADMAP.md` is the report/recommendation.

## Data & disclaimers

- CUAD is released under **CC BY 4.0**; attribution is retained here and on the site.
- All clients, matters, staff, and approvals are **synthetic**.
- The contract-risk rubric is **simulated** and is not legal advice.
- No secrets are stored in this repo; Snowflake credentials live in Paperclip secrets.

## Build the site

```bash
python3 build_site.py     # rewrites the *.html files in place
```
