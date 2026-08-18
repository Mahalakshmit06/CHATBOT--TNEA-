"""Build the self-contained preview HTML with the dataset embedded."""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "backend" / "data" / "tnea_2025_processed.json"
TEMPLATE = BASE / "preview" / "template.html"
OUT = BASE / "preview" / "index.html"

with open(DATA, encoding="utf-8") as fh:
    payload = json.load(fh)

# Build a compact records array: {code,name,district,branch,branch_code,closing:<comm->val>}
records = []
for r in payload["records"]:
    records.append(
        {
            "c": r["college_code"],
            "n": r["college_name"],
            "d": r["district"],
            "b": r["branch"],
            "bc": r["branch_code"],
            "closing": {k: v for k, v in r["cutoffs"].items()},
        }
    )

js = "const RECORDS=" + json.dumps(records, ensure_ascii=False, separators=(",", ":")) + ";"

template = TEMPLATE.read_text(encoding="utf-8")
html = template.replace("/* __DATA__ */", js)
OUT.write_text(html, encoding="utf-8")

print(f"Preview written: {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
