# snow-compliance-demo

Board-review staging for a **Snowflake legal-compliance demonstration** built on the
public [CUAD](https://github.com/The-Atticus-Project/cuad) dataset plus synthetic
law-firm records.

**Live site:** https://jpeckenpaugh.github.io/snow-compliance-demo/

Any push to `main` republishes the site (GitHub Pages, legacy build from `/`).

## What's here

| Path | Purpose |
| --- | --- |
| `index.html` … `poc.html` | The board-review site (generated). |
| `build_site.py` | Regenerates the HTML from embedded content. `python3 build_site.py` |
| `docs/PLAN.md` | Canonical Markdown plan (same content as the site). |
| `sql/01…05*.sql` | Snowflake DDL: setup, model, security, risk, audit. |
| `ingest/load_cuad.py` | Parses CUAD JSON into RAW CSVs. |
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
- `poc/analysis/cuad_shape_report.md` documents the real CUAD shape vs. the plan.

## Data & disclaimers

- CUAD is released under **CC BY 4.0**; attribution is retained here and on the site.
- All clients, matters, staff, and approvals are **synthetic**.
- The contract-risk rubric is **simulated** and is not legal advice.
- No secrets are stored in this repo; Snowflake credentials live in Paperclip secrets.

## Build the site

```bash
python3 build_site.py     # rewrites the *.html files in place
```
