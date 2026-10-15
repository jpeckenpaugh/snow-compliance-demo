#!/usr/bin/env python3
"""Generate deterministic, obviously-fictional law-firm records with Faker.

Everything here is synthetic. Names are prefixed so screenshots cannot be mistaken
for real client or privileged material. A fixed seed makes rebuilds reproducible.

Usage:
    python ingest/generate_synthetic_data.py --contracts 30 --seed 42 --out build
"""
import argparse
import csv
import pathlib
import random

from faker import Faker

LEVELS = ["Public", "Confidential", "Highly Confidential"]
TITLES = ["Partner", "Counsel", "Associate", "Paralegal", "Compliance Officer"]
PRACTICES = ["Corporate", "Litigation", "IP", "Employment", "Real Estate", "Privacy"]
ACCESS = ["READ", "WRITE"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contracts", type=int, default=30)
    ap.add_argument("--clients", type=int, default=8)
    ap.add_argument("--employees", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("build"))
    args = ap.parse_args()

    random.seed(args.seed)
    fake = Faker()
    Faker.seed(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    def writer(name, header):
        fh = (args.out / f"{name}.csv").open("w", newline="")
        w = csv.writer(fh)
        w.writerow(header)
        return fh, w

    clients_fh, clients = writer(
        "raw_synthetic_clients",
        ["client_id", "client_name", "industry", "region", "contact_name", "contact_email", "contact_phone"],
    )
    for i in range(1, args.clients + 1):
        clients.writerow([
            f"CL-{i:03d}",
            f"SYNTHETIC {fake.company()}",
            fake.bs().title(),
            fake.state(),
            fake.name(),
            fake.company_email(),
            fake.phone_number(),
        ])

    employees_fh, employees = writer(
        "raw_synthetic_employees",
        ["employee_id", "full_name", "title", "practice", "role"],
    )
    for i in range(1, args.employees + 1):
        title = random.choice(TITLES)
        employees.writerow([
            f"EMP-{i:03d}",
            f"SYNTHETIC {fake.name()}",
            title,
            random.choice(PRACTICES),
            "attorney" if title in ("Partner", "Counsel", "Associate") else "staff",
        ])

    matters_fh, matters = writer(
        "raw_synthetic_matters",
        ["matter_id", "client_id", "matter_name", "confidentiality_level", "opened_on", "lead_attorney_id"],
    )
    matter_count = args.contracts  # roughly one matter per contract
    for i in range(1, matter_count + 1):
        matters.writerow([
            f"SYN-{1000 + i}",
            f"CL-{random.randint(1, args.clients):03d}",
            f"SYNTHETIC {random.choice(['M&A', 'Licensing', 'Vendor', 'Employment', 'IP', 'Data'])} matter {i}",
            random.choice(LEVELS),
            fake.date_between(start_date="-3y", end_date="today").isoformat(),
            f"EMP-{random.randint(1, args.employees):03d}",
        ])

    auth_fh, auth = writer(
        "raw_synthetic_matter_authorization",
        ["matter_id", "employee_id", "access_level", "valid_from", "valid_to"],
    )
    assigns_fh, assigns = writer(
        "raw_synthetic_matter_assignment",
        ["matter_id", "employee_id", "assignment_role"],
    )
    for i in range(1, matter_count + 1):
        matter_id = f"SYN-{1000 + i}"
        # One lead + one additional authorized attorney/paralegal.
        chosen = random.sample(range(1, args.employees + 1), k=min(2, args.employees))
        for emp in chosen:
            auth.writerow([matter_id, f"EMP-{emp:03d}", random.choice(ACCESS),
                           "2024-01-01", ""])
        assigns.writerow([matter_id, f"EMP-{chosen[0]:03d}", "lead"])

    attach_fh, attach = writer(
        "raw_synthetic_contract_attachment",
        ["matter_id", "contract_id", "executed_on"],
    )
    for i in range(1, args.contracts + 1):
        attach.writerow([
            f"SYN-{1000 + i}",
            f"CUAD-{i - 1:04d}",
            fake.date_between(start_date="-3y", end_date="today").isoformat(),
        ])

    approval_fh, approval = writer(
        "raw_synthetic_access_approval",
        ["matter_id", "employee_id", "approved_by", "approved_on"],
    )
    for i in range(1, matter_count + 1):
        approval.writerow([
            f"SYN-{1000 + i}",
            f"EMP-{random.randint(1, args.employees):03d}",
            f"EMP-{random.randint(1, args.employees):03d}",
            fake.date_between(start_date="-1y", end_date="today").isoformat(),
        ])

    for fh in (clients_fh, employees_fh, matters_fh, auth_fh, assigns_fh, attach_fh, approval_fh):
        fh.close()
    print(f"wrote synthetic CSVs to {args.out}")


if __name__ == "__main__":
    main()
