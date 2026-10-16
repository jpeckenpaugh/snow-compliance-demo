#!/usr/bin/env python3
"""Split the full CUAD master JSON into newline-delimited documents (NDJSON).

A single Snowflake ``VARIANT`` value is capped at ~16 MB, and ``CUADv1.json`` is
~40 MB, so the whole file cannot land as one row. This step reshapes the file for
transport only: one JSON object per line, each carrying an ordinal plus the two
fields the in-Snowflake normalization reads (``title``, ``paragraphs``). All
parsing/normalization still happens in SQL (see ``sql/06_full_dataset.sql``).

CUAD (https://github.com/The-Atticus-Project/cuad) is CC BY 4.0; attribution is
retained in the ``source_file`` column of the loaded tables.

Usage:
    python3 ingest/split_cuad_json.py --json CUADv1.json --out build/cuad_docs.jsonl
"""
import argparse
import json
import pathlib


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, type=pathlib.Path,
                    help="Path to CUADv1.json (the 'data' array holds the documents).")
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path("build/cuad_docs.jsonl"))
    args = ap.parse_args()

    payload = json.loads(args.json.read_text())
    docs = payload["data"]
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("w") as fh:
        for i, doc in enumerate(docs):
            fh.write(json.dumps({
                "ord": i,
                "title": doc.get("title"),
                "paragraphs": doc.get("paragraphs"),
            }) + "\n")

    print(f"wrote {args.out} ({len(docs)} documents)")
    if len(docs) != 510:
        print(f"warning: expected 510 documents, found {len(docs)}")


if __name__ == "__main__":
    main()
