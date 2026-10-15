# snow-compliance-demo

Board-review staging for a **Snowflake legal-compliance demonstration** built on the
public [CUAD](https://github.com/The-Atticus-Project/cuad) dataset plus synthetic
law-firm records.

**Live site:** https://jpeckenpaugh.github.io/snow-compliance-demo/

Any push to `main` republishes the site (GitHub Pages, legacy build from `/`).

## What's here

| Path | Purpose |
| --- | --- |
| `index.html` … `roadmap.html` | The board-review site (generated). |
| `build_site.py` | Regenerates the HTML from embedded content. `python3 build_site.py` |
| `docs/PLAN.md` | Canonical Markdown plan (same content as the site). |
| `sql/01…05*.sql` | Snowflake DDL: setup, model, security, risk, audit. |
| `ingest/load_cuad.py` | Parses CUAD JSON into RAW CSVs. |
| `ingest/generate_synthetic_data.py` | Faker generator for fictional firm records. |

## Data & disclaimers

- CUAD is released under **CC BY 4.0**; attribution is retained here and on the site.
- All clients, matters, staff, and approvals are **synthetic**.
- The contract-risk rubric is **simulated** and is not legal advice.
- No secrets are stored in this repo; Snowflake credentials live in Paperclip secrets.

## Build the site

```bash
python3 build_site.py     # rewrites the *.html files in place
```
