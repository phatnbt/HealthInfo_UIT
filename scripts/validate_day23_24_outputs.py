#!/usr/bin/env python3
"""Fail-fast checks for the Day 23-24 manuscript package.

This validator checks traceability and reporting boundaries only. It does not
recompute or modify any frozen model output.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "docs" / "Day23_24_Manuscript_V1.md"
TRACE = ROOT / "docs" / "Day23_24_Claim_Traceability.csv"
GUIDE = ROOT / "docs" / "Day23_24_UHS_Review_Guide.md"
INDEX = ROOT / "docs" / "Day23_24_Final_Figure_Table_Index.md"
LOG = ROOT / "research_log" / "Day23_24_Manuscript_Assembly.md"
FREEZE = ROOT / "modeling" / "day20_22" / "day22_code_freeze_manifest.csv"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    required = [MANUSCRIPT, TRACE, GUIDE, INDEX, LOG, FREEZE]
    for path in required:
        require(path.is_file() and path.stat().st_size > 0, f"missing or empty {path.relative_to(ROOT)}")

    text = MANUSCRIPT.read_text(encoding="utf-8")
    for heading in [
        "## Abstract",
        "## 1 Introduction",
        "## 2 Methods",
        "## 3 Results",
        "## 4 Discussion",
        "## 5 Limitations",
        "## 6 Conclusions",
    ]:
        require(heading in text, f"manuscript section absent: {heading}")

    lower = text.lower()
    for forbidden in [
        "xgboost was the universal winner",
        "random forest was the universal winner",
        "logistic regression was the universal winner",
        "shap proves",
        "shap caused",
        "clinically validated cutoff",
        "generalizable to vietnam",
    ]:
        require(forbidden not in lower, f"forbidden overclaim present: {forbidden}")

    with TRACE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 16, f"expected 16 traceability rows, found {len(rows)}")
    require(len({row['Claim_ID'] for row in rows}) == len(rows), "Claim_ID values are not unique")
    for row in rows:
        source = ROOT / row["Authoritative_source"]
        require(source.is_file(), f"trace source missing for {row['Claim_ID']}: {row['Authoritative_source']}")
        require(row["Interpretation_boundary"].strip(), f"missing boundary for {row['Claim_ID']}")

    with FREEZE.open(encoding="utf-8-sig", newline="") as handle:
        freeze_rows = list(csv.DictReader(handle))
    require(len(freeze_rows) == 30, f"current freeze manifest must contain 30 entries, found {len(freeze_rows)}")

    guide = GUIDE.read_text(encoding="utf-8")
    for phrase in ["false negative", "false positive", "không có universal winner", "Việt Nam"]:
        require(phrase in guide, f"UHS guide missing required concept: {phrase}")

    print("PASS Day23-24 manuscript sections")
    print("PASS 16 claim-traceability rows and source paths")
    print("PASS reporting-boundary language")
    print("PASS current 30-entry freeze manifest")


if __name__ == "__main__":
    main()
