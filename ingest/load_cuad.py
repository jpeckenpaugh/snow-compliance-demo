#!/usr/bin/env python3
"""Load CUAD contracts and clause annotations into RAW.

CUAD (https://github.com/The-Atticus-Project/cuad) is released under CC BY 4.0.
Attribution is retained in the source_file column and in the site footer.

Usage:
    python ingest/load_cuad.py --cuad-root /path/to/cuad --limit 30 --out build/cuad.csv
"""
import argparse
import csv
import json
import pathlib


def iter_contracts(cuad_root: pathlib.Path):
    """CUAD_v1.json holds a top-level 'data' list of contract documents."""
    master = cuad_root / "CUAD_v1" / "CUAD_v1.json"
    if not master.exists():
        master = cuad_root / "CUAD_v1.json"
    with master.open() as fh:
        yield from json.load(fh)["data"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cuad-root", required=True, type=pathlib.Path)
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("build"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    contracts_path = args.out / "raw_cuad_contracts.csv"
    clauses_path = args.out / "raw_cuad_clauses.csv"

    with contracts_path.open("w", newline="") as cf, clauses_path.open("w", newline="") as lf:
        cw = csv.writer(cf)
        lw = csv.writer(lf)
        cw.writerow(["contract_id", "contract_name", "contract_type", "source_file"])
        lw.writerow(["contract_id", "clause_category", "answer", "clause_text", "char_start", "char_end"])

        for i, doc in enumerate(iter_contracts(args.cuad_root)):
            if i >= args.limit:
                break
            contract_id = f"CUAD-{i:04d}"
            paragraphs = doc.get("paragraphs", [])
            title = next((p.get("context") for p in paragraphs if p.get("context")), contract_id)
            ctype = doc.get("type") or "UNKNOWN"
            source = "The Atticus Project CUAD, CC BY 4.0"
            cw.writerow([contract_id, title.strip()[:500], ctype, source])

            for qa in doc.get("qas", []):
                category = qa.get("id", "").split("__")[-1] or qa.get("id", "")
                answers = qa.get("answers", [])
                answer = (qa.get("answers") or [{}])[0].get("text", "No") if answers else "No"
                if answers:
                    a = answers[0]
                    lw.writerow([contract_id, category, "Yes", a.get("text", ""),
                                 a.get("answer_start", ""), a.get("answer_start", 0) + len(a.get("text", ""))])
                else:
                    lw.writerow([contract_id, category, "No", "", "", ""])

    print(f"wrote {contracts_path} and {clauses_path}")


if __name__ == "__main__":
    main()
