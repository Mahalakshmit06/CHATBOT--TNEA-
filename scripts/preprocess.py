"""Preprocess the raw TNEA 2025 dataset into a normalized, ready-to-serve form.

Input : backend/data/tnea_2025_raw.csv
Outputs: backend/data/tnea_2025_cleaned.csv
         backend/data/tnea_2025_processed.json
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "backend" / "data"
RAW = BASE / "tnea_2025_raw.csv"
OUT_CSV = BASE / "tnea_2025_cleaned.csv"
OUT_JSON = BASE / "tnea_2025_processed.json"

COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]

# Pincode -> district, inferred from college addresses in the dataset.
PINCODE_DISTRICT = {
    "602025": "TIRUVALLUR",
    "624401": "DINDIGUL",
    "637018": "NAMAKKAL",
    "641021": "COIMBATORE",
    "641105": "COIMBATORE",
}

# Known district aliases (common misspellings / variants).
DISTRICT_ALIASES = {
    "MADRAS": "CHENNAI",
    "CHENNAI CITY": "CHENNAI",
    "MADRAS CITY": "CHENNAI",
    "KOVAI": "COIMBATORE",
    "TRICHY": "TIRUCHIRAPPALLI",
    "TIRUCHI": "TIRUCHIRAPPALLI",
    "TIRUCHIRAPALLI": "TIRUCHIRAPPALLI",
    "TIRUCHCHIRAPPALLI": "TIRUCHIRAPPALLI",
    "NELLAI": "TIRUNELVELI",
    "TANJORE": "THANJAVUR",
    "TUTICORIN": "THOOTHUKUDI",
    "KANYAKUMARI": "KANNIYAKUMARI",
    "KANNIYAKUMARY": "KANNIYAKUMARI",
    "NAGERCOIL": "KANNIYAKUMARI",
    "NAGARCOIL": "KANNIYAKUMARI",
    "KANCHEEPURAM": "KANCHIPURAM",
    "KANCHI": "KANCHIPURAM",
    "KANCHEPURAM": "KANCHIPURAM",
    "VILLUPURAM": "VILUPPURAM",
    "VILLIPURAM": "VILUPPURAM",
    "VILLUPURAM": "VILUPPURAM",
    "KALLAKURUCHI": "KALLAKURICHI",
    "KALLAKURICHII": "KALLAKURICHI",
    "NAGAPATTINAM": "NAGAPATTINAM",
    "NAGAI": "NAGAPATTINAM",
    "THENKASI": "TENKASI",
    "TIRUPATTUR": "TIRUPATHUR",
    "SIVAGANGA": "SIVAGANGAI",
    "RAMANATHAPURAM": "RAMANATHAPURAM",
    "MAYILADUTHURAI": "MAYILADUTHURAI",
    "MAYILADUTURAI": "MAYILADUTHURAI",
    "THOOTHOOKUDI": "THOOTHUKUDI",
    "PERAMBALUR": "PERAMBALUR",
    "TIRUVALLUR": "TIRUVALLUR",
    "THIRUVALLUR": "TIRUVALLUR",
    "TIRUVANNAMALAI": "TIRUVANNAMALAI",
    "THIRUVANNAMALAI": "TIRUVANNAMALAI",
    "THIRUVARUR": "TIRUVARUR",
}

# Branch aliases -> canonical normalized branch name (used in NLP + dedupe).
BRANCH_ALIASES = {
    "CSE": "COMPUTER SCIENCE AND ENGINEERING",
    "COMPUTER SCIENCE AND ENGINEERING (AI AND ML)": "COMPUTER SCIENCE AND ENGINEERING (AI AND MACHINE LEARNING)",
    "CSE (CYBER SECURITY)": "COMPUTER SCIENCE AND ENGINEERING (CYBER SECURITY)",
    "COMPUTER SCIENCE AND ENGINEERING (CS)": "COMPUTER SCIENCE AND ENGINEERING",
    "CSBS": "COMPUTER SCIENCE AND BUSSINESS SYSTEM",
    "COMPUTER SCIENCE AND BUSSINESS": "COMPUTER SCIENCE AND BUSSINESS SYSTEM",
    "COMPUTER SCIENCE AND BUSINESS": "COMPUTER SCIENCE AND BUSSINESS SYSTEM",
    "ECE": "ELECTRONICS AND COMMUNICATION ENGINEERING",
    "EEE": "ELECTRICAL AND ELECTRONICS ENGINEERING",
    "MECH": "MECHANICAL ENGINEERING",
    "IT": "INFORMATION TECHNOLOGY",
    "CIVIL": "CIVIL ENGINEERING",
    "AID": "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE",
    "AIDS": "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE",
    "AI DS": "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE",
    "AIML": "ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING",
    "AI ML": "ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING",
    "BIO TECHNOLOGY AND BIO CHEMICAL": "BIO TECHNOLOGY AND BIO CHEMICAL ENGINEERING",
    "VLSI": "ELECTRONICS ENGINEERING (VLSI DESIGN AND TECHNOLOGY)",
}


def clean_text(value: str) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    value = value.replace("\u00a0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def clean_district(raw: str, college_name: str) -> str:
    value = clean_text(raw).upper()
    if not value:
        value = infer_district_from_college(college_name)
        return value or "UNKNOWN"

    if value in PINCODE_DISTRICT:
        return PINCODE_DISTRICT[value]

    # Strip stray tokens appended after district names, e.g. "CHENGALPATTU f".
    value = re.sub(r"\s*(F|FR|FROM|F\s*R)\s*$", "", value).strip()

    return DISTRICT_ALIASES.get(value, value)


def infer_district_from_college(college_name: str) -> str:
    name = clean_text(college_name).upper()
    for token, district in [
        ("TIRUVALLUR", "TIRUVALLUR"),
        ("THIRUVALLUR", "TIRUVALLUR"),
        ("KANYAKUMARI", "KANNIYAKUMARI"),
        ("NAGAPPATTINAM", "NAGAPATTINAM"),
        ("NAGAPATTINAM", "NAGAPATTINAM"),
        ("DINDIGUL", "DINDIGUL"),
        ("COIMBATORE", "COIMBATORE"),
        ("NAMAKKAL", "NAMAKKAL"),
        ("MADURAI", "MADURAI"),
        ("CHENNAI", "CHENNAI"),
        ("SALEM", "SALEM"),
        ("KANCHIPURAM", "KANCHIPURAM"),
        ("TIRUCHIRAPPALLI", "TIRUCHIRAPPALLI"),
        ("TRICHY", "TIRUCHIRAPPALLI"),
    ]:
        if token in name:
            return district
    return "UNKNOWN"


def canonical_branch(raw: str) -> str:
    name = clean_text(raw)
    upper = name.upper()

    for alias, target in BRANCH_ALIASES.items():
        if upper == alias:
            return target

    # Title-case known full branch names while preserving acronym tokens.
    title = name.title()
    title = re.sub(r"\bOf\b", "of", title)
    title = re.sub(r"\bAnd\b", "and", title)
    title = re.sub(r"\bA\b", "a", title)
    title = re.sub(r"\bAI\b", "AI", title)
    title = re.sub(r"\bML\b", "ML", title)
    title = re.sub(r"\bIoT\b", "IoT", title)
    title = re.sub(r"\bCS\b", "CS", title)
    title = re.sub(r"\bB\.Plan\b", "B.Plan", title, flags=re.I)
    return title


def parse_cutoff(value: str) -> float | None:
    v = clean_text(value).upper()
    if not v or v == "NOT AVAILABLE":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def main() -> None:
    with open(RAW, encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = [dict(r) for r in reader]

    colleges = {}
    records = []
    for row in rows:
        college_name = clean_text(row.get("COLLEGE_NAME", ""))
        college_code = clean_text(row.get("COLLEGE_CODE", ""))
        district = clean_district(row.get("DISTRICT", ""), college_name)
        branch = canonical_branch(row.get("BRANCH_NAME", ""))
        branch_code = clean_text(row.get("BRANCH_CODE", ""))

        cutoffs = {}
        for c in COMMUNITIES:
            val = parse_cutoff(row.get(c, ""))
            if val is not None:
                cutoffs[c] = val

        record = {
            "record_id": clean_text(row.get("RECORD_ID", "")),
            "college_code": college_code,
            "college_name": college_name,
            "district": district,
            "branch": branch,
            "branch_code": branch_code,
            "cutoffs": cutoffs,
        }
        records.append(record)

        key = (college_code, college_name, district)
        colleges.setdefault(key, []).append(branch)

    colleges_list = []
    for (code, name, district), branches in colleges.items():
        colleges_list.append(
            {
                "college_code": code,
                "college_name": name,
                "district": district,
                "branches": sorted(set(branches)),
                "branch_count": len(branches),
            }
        )

    colleges_list.sort(key=lambda c: (c["college_code"], c["college_name"]))
    records.sort(key=lambda r: (r["college_code"], r["branch"], r["record_id"]))

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["RECORD_ID", "COLLEGE_CODE", "COLLEGE_NAME", "DISTRICT",
                        "BRANCH_NAME", "BRANCH_CODE", *COMMUNITIES],
        )
        writer.writeheader()
        for r in records:
            writer.writerow(
                {
                    "RECORD_ID": r["record_id"],
                    "COLLEGE_CODE": r["college_code"],
                    "COLLEGE_NAME": r["college_name"],
                    "DISTRICT": r["district"],
                    "BRANCH_NAME": r["branch"],
                    "BRANCH_CODE": r["branch_code"],
                    **{c: (str(r["cutoffs"][c]) if c in r["cutoffs"] else "Not Available")
                       for c in COMMUNITIES},
                }
            )

    payload = {
        "meta": {
            "record_count": len(records),
            "college_count": len(colleges_list),
            "district_count": len({c["district"] for c in colleges_list if c["district"] != "UNKNOWN"}),
            "communities": COMMUNITIES,
            "formula": "Mathematics + Physics/2 + Chemistry/2",
            "source_file": RAW.name,
        },
        "colleges": colleges_list,
        "records": records,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"Raw records:      {len(rows)}")
    print(f"Clean records:    {len(records)}")
    print(f"Unique colleges:  {len(colleges_list)}")
    print(f"Districts:        {payload['meta']['district_count']}")
    unknown = sum(1 for c in colleges_list if c["district"] == "UNKNOWN")
    print(f"Unknown district: {unknown}")
    print("Outputs:", OUT_CSV, OUT_JSON)


if __name__ == "__main__":
    main()
