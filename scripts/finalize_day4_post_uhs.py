#!/usr/bin/env python3
"""Finalize NHIS 2024 Day 4 after UHS predictor review.

Usage:
    python scripts/finalize_day4_post_uhs.py adult24csv.zip adultinc24csv.zip

The script verifies the official raw files, audits the post-UHS variables,
builds the selected chronic-condition burden, verifies POVRATTC_A's 10
imputations, and writes local MEDNG/MEDDL final feature-lock cohort files.
Person-level outputs are intentionally not committed to the public repo.
"""
import csv, hashlib, shutil, sys, zipfile
from collections import Counter, defaultdict
from pathlib import Path

ADULT_MD5 = "6b0d5e572841ffef7b0f7df4ddfed556"
INC_MD5 = "14a1d5780100c1b0a13acce433e00360"

CORE = [
    "AGEP_A","SEX_A","HISPALLP_A","EDUCP_A","RATCAT_A",
    "EMPWRKLSW1_A","NOTCOV_A","FDSCAT3_A","PHSTAT_A","DISAB3_A","K6SPD_A"
]
SUPPORTING = ["MARSTAT_A","URBRRL23","REGION"]
EXPLORATORY = ["BMICAT_A","ANXFREQ_A","DEPFREQ_A","LONELY_A","SOCSCLPAR_A","SMKCIGST_A"]
DISEASE_SENS = ["DIBEV_A","HYPEV_A"]

# Eight selected chronic-condition domains. The CVD domain is counted once even
# if several of CHD/angina/MI/stroke are positive. This is a selected-condition
# count, not a validated clinical severity index.
DOMAINS = {
    "hypertension": ["HYPEV_A"],
    "cardiovascular": ["CHDEV_A","ANGEV_A","MIEV_A","STREV_A"],
    "asthma": ["ASEV_A"],
    "copd": ["COPDEV_A"],
    "cancer": ["CANEV_A"],
    "diabetes": ["DIBEV_A"],
    "arthritis": ["ARTHEV_A"],
    "kidney": ["KIDWEAKEV_A"],
}
CHRONIC_VARS = sorted({v for xs in DOMAINS.values() for v in xs})
EXPECTED = {v:{"1","2","7","8","9"} for v in CHRONIC_VARS}
EXPECTED["SMKCIGST_A"] = {"1","2","3","4","5","9"}


def md5(p):
    h = hashlib.md5()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()


def extract(zp, member, out):
    with zipfile.ZipFile(zp) as z:
        if member not in z.namelist():
            raise RuntimeError(f"{member} not found")
        with z.open(member) as src, open(out,"wb") as dst:
            shutil.copyfileobj(src,dst)


def binary(r,v):
    if r[v] == "1": return 1
    if r[v] == "2": return 0
    return None


def cvd(r):
    vals = [r[v] for v in DOMAINS["cardiovascular"]]
    if any(x == "1" for x in vals): return 1
    if all(x == "2" for x in vals): return 0
    return None


def burden(r):
    vals = []
    for d, vs in DOMAINS.items():
        vals.append(cvd(r) if d == "cardiovascular" else binary(r,vs[0]))
    if any(x is None for x in vals): return ""
    n = sum(vals)
    return "0" if n == 0 else "1" if n == 1 else "2" if n == 2 else "3+"


def write_model(path, rows, target_name, source_target):
    fields = ["HHX","WTFA_A","PPSU","PSTRAT","MEDNG12M_A","MEDDL12M_A"] + CORE + SUPPORTING + EXPLORATORY + DISEASE_SENS + ["CHRONIC_BURDEN_CAT",target_name]
    with open(path,"w",encoding="utf-8-sig",newline="") as f:
        w = csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows:
            o = {k:r[k] for k in fields if k not in ("CHRONIC_BURDEN_CAT",target_name)}
            o["CHRONIC_BURDEN_CAT"] = burden(r)
            o[target_name] = int(r[source_target] == "1")
            w.writerow(o)


if len(sys.argv) != 3:
    raise SystemExit("Usage: python scripts/finalize_day4_post_uhs.py adult24csv.zip adultinc24csv.zip")

out = Path("nhis_day4_post_uhs_final"); out.mkdir(exist_ok=True)
adult = out/"adult24.csv"; inc = out/"adultinc24.csv"
extract(Path(sys.argv[1]),"adult24.csv",adult)
extract(Path(sys.argv[2]),"adultinc24.csv",inc)
assert md5(adult) == ADULT_MD5
assert md5(inc) == INC_MD5

with adult.open(encoding="utf-8-sig",newline="") as f: A = list(csv.DictReader(f))
with inc.open(encoding="utf-8-sig",newline="") as f: I = list(csv.DictReader(f))
assert len(A) == 32629 and len(I) == 326290
assert Counter(r["MEDNG12M_A"] for r in A) == Counter({"2":30159,"1":2195,"8":259,"7":10,"9":6})
assert Counter(r["MEDDL12M_A"] for r in A) == Counter({"2":29791,"1":2564,"8":255,"7":10,"9":9})

# Variable-specific code audit. No global 7/8/9 missing rule is used.
for v in CHRONIC_VARS + ["SMKCIGST_A"]:
    observed = {r[v] for r in A}
    assert observed <= EXPECTED[v], (v, observed - EXPECTED[v])

# MARSTAT_A is a recode whose 7/8/9 are valid categories (never married,
# living with a partner, unknown marital status), so they are preserved.
assert {r["MARSTAT_A"] for r in A} <= {str(i) for i in range(1,10)}

NG = [r for r in A if r["MEDNG12M_A"] in ("1","2")]
DL = [r for r in A if r["MEDDL12M_A"] in ("1","2")]
assert len(NG) == 32354 and len(DL) == 32355

# Chronic burden audit: unresolved domain values stay missing rather than being
# treated as disease absence.
ng_missing = sum(burden(r) == "" for r in NG)
dl_missing = sum(burden(r) == "" for r in DL)
assert ng_missing == 222 and dl_missing == 222

# Verify income multiple-imputation structure and continuous poverty range.
by_hhx = defaultdict(list)
for r in I:
    by_hhx[r["HHX"]].append(int(r["IMPNUM_A"]))
    x = float(r["POVRATTC_A"])
    assert 0.0 <= x <= 11.0
assert len(by_hhx) == 32629
assert all(sorted(v) == list(range(1,11)) for v in by_hhx.values())

write_model(out/"analysis_ready_MEDNG_FINAL_FEATURELOCK_RAWCODES.csv", NG, "TARGET_FORGONE_COST", "MEDNG12M_A")
write_model(out/"analysis_ready_MEDDL_FINAL_FEATURELOCK_RAWCODES.csv", DL, "TARGET_DELAYED_COST", "MEDDL12M_A")

print("PASS: Day 4 post-UHS final feature lock verified.")
print("Main model: 11 existing core predictors + CHRONIC_BURDEN_CAT.")
print("SMKCIGST_A is exploratory; SMKEV_A is replaced for smoking-status analyses.")
print("POVRATTC_A is sensitivity-only and must be run across all 10 imputations.")
