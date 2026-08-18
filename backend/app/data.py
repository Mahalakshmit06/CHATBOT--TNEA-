"""Dataset loader and recommendation engine for Campus AI.

All recommendations are generated exclusively from the supplied TNEA dataset.
No fabricated facts are ever returned.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "data"
PROCESSED = BASE / "tnea_2025_processed.json"

COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]


class Dataset:
    """In-memory index over the preprocessed TNEA dataset."""

    def __init__(self, path: Path = PROCESSED):
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        self.meta: dict = payload["meta"]
        self.colleges: list[dict] = payload["colleges"]
        self.records: list[dict] = payload["records"]

        self.district_set: list[str] = sorted(
            {c["district"] for c in self.colleges if c["district"] != "UNKNOWN"}
        )
        self.branch_set: list[str] = sorted({r["branch"] for r in self.records})
        self.college_names: list[str] = [c["college_name"] for c in self.colleges]

        # Fast lookup indexes.
        self.by_college: dict[str, list[dict]] = {}
        self.branch_code_map: dict[str, str] = {}
        for r in self.records:
            self.by_college.setdefault(r["college_name"], []).append(r)
            code = str(r.get("branch_code") or "").upper().strip()
            if code and code not in self.branch_code_map:
                self.branch_code_map[code] = r["branch"]

    def cutoff(self, record: dict, community: str) -> float | None:
        return record.get("cutoffs", {}).get(community)

    def eligible(self, record: dict, community: str, user_cutoff: float) -> bool:
        val = self.cutoff(record, community)
        return val is not None and user_cutoff >= val

    def recommend(
        self,
        cutoff: float,
        community: str = "OC",
        district: str = "ALL",
        branch: str = "ALL",
        search: str = "",
        include_na: bool = True,
        limit: int = 500,
    ) -> dict:
        """Return all eligible college-branch records plus optional NA records.

        Never hides eligible colleges: every record whose closing cutoff is
        below or equal to the user's cutoff is included (up to `limit`).
        """
        community = community.upper() if community in COMMUNITIES else "OC"
        district = district.upper().strip() if district else "ALL"
        branch = branch.upper().strip() if branch else "ALL"

        eligible, na = [], []
        for r in self.records:
            if district != "ALL" and r["district"] != district:
                continue
            if branch != "ALL" and not self.branch_matches(branch, r["branch"]):
                continue
            if search:
                q = search.lower()
                hay = f"{r['college_name']} {r['district']} {r['branch']}".lower()
                if not all(tok in hay for tok in q.split()):
                    continue
            val = self.cutoff(r, community)
            if val is None:
                na.append(r)
            elif cutoff >= val:
                r2 = dict(r)
                r2["_margin"] = round(cutoff - val, 2)
                r2["_status"] = "Strong match" if r2["_margin"] >= 10 else ("Good match" if r2["_margin"] >= 3 else "Edge")
                eligible.append(r2)

        # Best matches first (smallest margin = just made it in).
        eligible.sort(key=lambda r: (r["_margin"], r["college_code"], r["branch"]))
        if include_na:
            na.sort(key=lambda r: (r["college_code"], r["branch"]))

        # The application asks for every eligible record. `limit` is retained only
        # as a safety valve for external API callers; normal chatbot calls use 10000.
        eligible_view = eligible[:limit]
        na_view = na[: max(0, limit - len(eligible_view))]

        return {
            "community": community,
            "eligible_count": len(eligible),
            "na_count": len(na),
            "total_matching": len(eligible) + len(na),
            "records": [self._serialize(r, community) for r in eligible_view],
            "na_records": [self._serialize(r, community, na=True) for r in na_view],
        }

    def college_detail(self, college_name: str) -> dict | None:
        """Return all branches for a specific college."""
        records = self.by_college.get(college_name)
        if not records:
            return None
        return {
            "college_name": college_name,
            "college_code": records[0]["college_code"],
            "district": records[0]["district"],
            "college_type": self.college_type(college_name),
            "branches": [
                self._serialize(r, None) for r in sorted(records, key=lambda x: x["branch"])
            ],
        }

    def branches_in_district(self, district: str) -> list[str]:
        return sorted({r["branch"] for r in self.records if r["district"] == district})

    @staticmethod
    def college_type(name: str) -> str:
        n=(name or "").upper(); auto="AUTONOMOUS" in n
        if "UNIVERSITY DEPARTMENTS OF ANNA UNIVERSITY" in n or "SCHOOL OF ARCHITECTURE AND PLANNING" in n:
            return "University Department + Autonomous" if auto else "University Department"
        if "UNIVERSITY COLLEGE OF ENGINEERING" in n:
            return "Government / University College + Autonomous" if auto else "Government / University College"
        if "GOVERNMENT-AIDED" in n or "GOVERNMENT AIDED" in n or "AIDED" in n:
            return "Government-aided + Autonomous" if auto else "Government-aided"
        if "GOVERNMENT" in n or n.startswith("GOVT ") or " GOVT " in n:
            return "Government + Autonomous" if auto else "Government"
        if auto:return "Private / Self-financing + Autonomous"
        return "Private / Self-financing"

    def _serialize(self, r: dict, community: str | None, na: bool = False) -> dict:
        return {
            "record_id": r["record_id"],
            "college_code": r["college_code"],
            "college_name": r["college_name"],
            "district": r["district"],
            "branch": r["branch"],
            "branch_code": r["branch_code"],
            "college_type": self.college_type(r["college_name"]),
            "cutoffs": dict(r.get("cutoffs", {})),
            "closing_cutoff": None if na else (r["cutoffs"].get(community) if community else None),
            "margin": None if na else r.get("_margin"),
            "status": "Cutoff not published" if na else r.get("_status", "Dataset record"),
            "eligible": not na,
        }

    COLLEGE_ALIASES = {
        "psg": "2006", "psg tech": "2006", "psg college": "2006",
        "kct": "2712", "kumaraguru": "2712",
        "cit": "2007", "cit coimbatore": "2007",
        "thiagarajar": "5008", "tce": "5008",
        "ceg": "1", "ceg campus": "1", "anna university ceg": "1",
        "anna university mit": "4", "mit anna university": "4",
        "anna university act": "2", "act anna university": "2",
        "gct": "2005", "gct coimbatore": "2005",
    }

    def search_colleges(self, query: str, limit: int = 8) -> list[dict]:
        """Token-aware college search with strong preference for exact distinctive phrases."""
        import re
        from difflib import SequenceMatcher
        q = re.sub(r"[^a-z0-9]+", " ", (query or "").lower()).strip()
        if not q:
            return []
        for alias, code in sorted(self.COLLEGE_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
            if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", q):
                exact=[c for c in self.colleges if str(c.get("college_code"))==code]
                if exact:return exact[:limit]
        if re.fullmatch(r"\d{1,5}", q):
            exact=[c for c in self.colleges if str(c.get("college_code"))==q]
            return exact[:limit]
        stop = {
            "what", "which", "show", "find", "tell", "me", "about", "college", "colleges",
            "details", "detail", "info", "information", "branch", "branches", "course", "courses",
            "cutoff", "cutoffs", "available", "offer", "offers", "list", "give", "please",
            "the", "a", "an", "and", "or", "of", "in", "for", "to", "with", "is", "are",
            "can", "you", "my", "i", "want", "need", "know", "tell", "about",
        }
        # Keep technology only when it is part of a distinctive phrase; otherwise it is too generic.
        qt = [t for t in q.split() if t not in stop and len(t) >= 3]
        if not qt:
            qt = [t for t in q.split() if len(t) >= 3]
        qphrase = " ".join(qt)
        scored = []
        for c in self.colleges:
            name = c["college_name"]
            n = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
            nt = set(n.split())
            overlap = len(set(qt) & nt) / max(1, len(set(qt)))
            ratio = SequenceMatcher(None, qphrase, n).ratio() if qphrase else 0
            contains_phrase = 1.0 if qphrase and qphrase in n else 0.0
            score = max(contains_phrase, overlap * 0.95, ratio * 0.55)
            if score >= 0.42:
                scored.append((score, name, c))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [c for _, _, c in scored[:limit]]

    def college_detail_by_query(self, query: str) -> dict | None:
        hits = self.search_colleges(query, limit=3)
        if not hits:
            return None
        # Prefer exact code or exact/contained name.
        q = str(query).strip().lower()
        for c in hits:
            if q == str(c["college_code"]).lower() or q == c["college_name"].lower():
                return self.college_detail(c["college_name"])
        return self.college_detail(hits[0]["college_name"])

    def branch_matches(self, branch_query: str, branch_name: str) -> bool:
        """Match a canonical branch, alias/family canonical, or plain text query."""
        from .aliases import BRANCH_FAMILIES
        q = (branch_query or "").upper().strip()
        b = (branch_name or "").upper().strip()
        if not q or q == "ALL":
            return True
        if q in BRANCH_FAMILIES:
            return any(x.upper() in b for x in BRANCH_FAMILIES[q])
        return q in b

    def branch_records(self, branch_query: str, district: str = "ALL") -> list[dict]:
        out = []
        for r in self.records:
            if district != "ALL" and r["district"] != district:
                continue
            if self.branch_matches(branch_query, r["branch"]):
                out.append(r)
        return out

    def compare_colleges(self, names: list[str], community: str | None = None) -> list[dict]:
        result = []
        for q in names[:5]:
            d = self.college_detail_by_query(q)
            if d:
                branches = d["branches"]
                if community:
                    for br in branches:
                        br["community_cutoff"] = br.get("cutoffs", {}).get(community)
                result.append(d)
        return result

    def stats(self) -> dict:
        return {
            "records": self.meta["record_count"],
            "colleges": self.meta["college_count"],
            "districts": len(self.district_set),
            "branches": len(self.branch_set),
            "communities": COMMUNITIES,
            "formula": self.meta["formula"],
        }


DATASET = Dataset()


def calculate_cutoff(mathematics: float, physics: float, chemistry: float) -> float:
    return round(mathematics + physics / 2 + chemistry / 2, 2)
