#!/usr/bin/env python3
"""
Minimal reproducibility script for NHIS 2024 UIT Day 1-4.

Usage:
    python reproduce_day1_4.py adult24csv.zip adultinc24csv.zip

It verifies official CSV checksums and independently creates:
- MEDNG-valid cohort
- MEDDL-valid cohort
- common-valid cohort
"""
import csv, hashlib, shutil, sys, zipfile
from pathlib import Path
from collections import Counter, defaultdict

ADULT_MD5="6b0d5e572841ffef7b0f7df4ddfed556"
INC_MD5="14a1d5780100c1b0a13acce433e00360"
ADULT_N=32629
INC_N=326290

PRED=["AGEP_A","SEX_A","HISPALLP_A","EDUCP_A","MARSTAT_A","RATCAT_A",
"EMPWRKLSW1_A","NOTCOV_A","FDSCAT3_A","REGION","URBRRL23","PHSTAT_A",
"DISAB3_A","DIBEV_A","HYPEV_A","BMICAT_A","K6SPD_A","ANXFREQ_A",
"DEPFREQ_A","LONELY_A","SOCSCLPAR_A","SMKEV_A"]
KEEP=["HHX","WTFA_A","PPSU","PSTRAT","MEDNG12M_A","MEDDL12M_A","IMPNUM_A"]+PRED

def md5(p):
    h=hashlib.md5()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def extract(zpath, member, out):
    with zipfile.ZipFile(zpath) as z:
        if member not in z.namelist():
            raise RuntimeError(f"{member} not found in {zpath}")
        with z.open(member) as src, open(out,"wb") as dst:
            shutil.copyfileobj(src,dst)

def write(path, rows, targets):
    with open(path,"w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=KEEP+targets); w.writeheader()
        for r in rows:
            o={c:r[c] for c in KEEP}
            if "TARGET_FORGONE_COST" in targets:o["TARGET_FORGONE_COST"]=int(r["MEDNG12M_A"]=="1")
            if "TARGET_DELAYED_COST" in targets:o["TARGET_DELAYED_COST"]=int(r["MEDDL12M_A"]=="1")
            if "TARGET_ANY_COST_BARRIER" in targets:o["TARGET_ANY_COST_BARRIER"]=int(r["MEDNG12M_A"]=="1" or r["MEDDL12M_A"]=="1")
            w.writerow(o)

if len(sys.argv) != 3:
    raise SystemExit("Usage: python reproduce_day1_4.py adult24csv.zip adultinc24csv.zip")

adult_zip=Path(sys.argv[1])
inc_zip=Path(sys.argv[2])
out=Path("nhis_day1_4_exact"); out.mkdir(exist_ok=True)
adult=out/"adult24.csv"; inc=out/"adultinc24.csv"
extract(adult_zip,"adult24.csv",adult)
extract(inc_zip,"adultinc24.csv",inc)
assert md5(adult)==ADULT_MD5, f"adult24 MD5 fail: {md5(adult)}"
assert md5(inc)==INC_MD5, f"adultinc24 MD5 fail: {md5(inc)}"

with adult.open(encoding="utf-8-sig",newline="") as f: A=list(csv.DictReader(f))
with inc.open(encoding="utf-8-sig",newline="") as f: I=list(csv.DictReader(f))
assert len(A)==ADULT_N
assert len(I)==INC_N

cng=Counter(r["MEDNG12M_A"] for r in A)
cdl=Counter(r["MEDDL12M_A"] for r in A)
assert cng==Counter({"2":30159,"1":2195,"8":259,"7":10,"9":6})
assert cdl==Counter({"2":29791,"1":2564,"8":255,"7":10,"9":9})

ng=[r for r in A if r["MEDNG12M_A"] in ("1","2")]
dl=[r for r in A if r["MEDDL12M_A"] in ("1","2")]
co=[r for r in A if r["MEDNG12M_A"] in ("1","2") and r["MEDDL12M_A"] in ("1","2")]
assert len(ng)==32354
assert len(dl)==32355
assert len(co)==32345

# Verify 10 income imputations and first-imputation equivalence
d=defaultdict(list)
imp1={}
for r in I:
    d[r["HHX"]].append(int(r["IMPNUM_A"]))
    if r["IMPNUM_A"]=="1": imp1[r["HHX"]]=r["RATCAT_A"]
assert len(d)==32629
assert all(sorted(v)==list(range(1,11)) for v in d.values())
assert all(r["RATCAT_A"]==imp1[r["HHX"]] for r in A)

write(out/"analysis_ready_MEDNG_EXACT_RAWCODES.csv",ng,["TARGET_FORGONE_COST"])
write(out/"analysis_ready_MEDDL_EXACT_RAWCODES.csv",dl,["TARGET_DELAYED_COST"])
write(out/"analysis_ready_COMMON_EXACT_RAWCODES.csv",co,["TARGET_FORGONE_COST","TARGET_DELAYED_COST","TARGET_ANY_COST_BARRIER"])
print("PASS: raw checksums, target counts, independent cohorts, and 10 income imputations verified.")
