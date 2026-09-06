#!/usr/bin/env python3
"""Fail-fast integrity checks for Day 20-22 aggregate-only outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd


FORBIDDEN_PERSON_LEVEL_COLUMNS = {
    "HHX", "PPSU", "PSTRAT", "WTFA_A", "Prediction", "Probability",
}
EXPECTED_OUTCOMES = {"MEDNG", "MEDDL"}
EXPECTED_MODELS = {"LR", "RF", "XGBoost"}
EXPECTED_WEIGHTINGS = {"Unweighted", "WTFA_A"}
EXPECTED_SEEDS = {2026, 2037, 2048}
EXPECTED_FACTORS = {0.8, 1.0, 1.2}
TOLERANCE = 1e-10


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("modeling/day20_22"))
    args = parser.parse_args()
    out = args.out_dir
    config = json.loads((out / "day20_22_config_log.json").read_text(encoding="utf-8"))
    for relative in config["outputs"]:
        require((out / relative).exists(), f"Missing output: {relative}")

    frames = {
        "error": pd.read_csv(out / "day20_22_error_summary.csv"),
        "profile": pd.read_csv(out / "day20_22_error_profile_by_group.csv"),
        "threshold": pd.read_csv(out / "day20_22_threshold_robustness.csv"),
        "seed": pd.read_csv(out / "day20_22_seed_robustness.csv"),
        "missing_split": pd.read_csv(out / "day20_22_missingness_by_split.csv"),
        "missing_perf": pd.read_csv(out / "day20_22_missingness_performance.csv"),
        "leakage": pd.read_csv(out / "day20_22_leakage_integrity_checklist.csv"),
        "composite_selection": pd.read_csv(out / "day20_22_composite_validation_selection.csv"),
        "composite_perf": pd.read_csv(out / "day20_22_composite_sensitivity_performance.csv"),
        "composite_split": pd.read_csv(out / "day20_22_composite_split_audit.csv"),
        "composite_roles": pd.read_csv(out / "day20_22_composite_validation_role_audit.csv"),
        "final_model": pd.read_csv(out / "day22_final_model_table.csv"),
        "final_error": pd.read_csv(out / "day22_final_error_table.csv"),
        "robustness": pd.read_csv(out / "day22_robustness_summary.csv"),
    }
    for name, frame in frames.items():
        leaked = FORBIDDEN_PERSON_LEVEL_COLUMNS & set(frame.columns)
        require(not leaked, f"{name}: forbidden person-level columns: {sorted(leaked)}")

    error = frames["error"]
    require(len(error) == 12, "Expected 2 outcomes x 3 models x 2 weightings")
    require(set(error["Outcome"]) == EXPECTED_OUTCOMES, "Error outcome coverage drift")
    require(set(error["Model"]) == EXPECTED_MODELS, "Error model coverage drift")
    require(set(error["Evaluation_weighting"]) == EXPECTED_WEIGHTINGS, "Error weighting drift")
    require(not error.duplicated(["Outcome", "Model", "Evaluation_weighting"]).any(), "Duplicate error key")
    require(np.allclose(error["Recall"] + error["FNR"], 1.0, atol=1e-12), "Recall/FNR invariant failed")
    require(np.allclose(error["Specificity"] + error["FPR"], 1.0, atol=1e-12), "Specificity/FPR invariant failed")
    confusion_total = error[[
        "TN_weighted_count", "FP_weighted_count", "FN_weighted_count", "TP_weighted_count"
    ]].sum(axis=1)
    unweighted = error["Evaluation_weighting"].eq("Unweighted")
    require(np.allclose(confusion_total[unweighted], error.loc[unweighted, "N"]),
            "Unweighted confusion counts do not sum to N")
    require((confusion_total[~unweighted] > 0).all(), "Weighted confusion total is non-positive")

    profile = frames["profile"]
    require(len(profile) == 168, "Expected 168 eligible group error-profile rows")
    require(profile["Eligibility_rule"].eq("PASS").all(), "Ineligible group entered error profile")
    require(((profile[["FNR", "FPR", "Share_of_all_FN", "Share_of_all_FP"]] >= 0) &
             (profile[["FNR", "FPR", "Share_of_all_FN", "Share_of_all_FP"]] <= 1)).all().all(),
            "Group error metric outside [0,1]")

    threshold = frames["threshold"]
    require(len(threshold) == 36, "Expected 36 threshold-robustness rows")
    require(set(threshold["Threshold_factor"].round(8)) == EXPECTED_FACTORS, "Threshold factors drift")
    locked_threshold = threshold[np.isclose(threshold["Threshold_factor"], 1.0)].set_index(
        ["Outcome", "Model", "Evaluation_weighting"]
    )
    error_indexed = error.set_index(["Outcome", "Model", "Evaluation_weighting"])
    for metric in ("AUROC", "AUPRC", "Recall", "Precision", "F1", "Specificity", "Brier"):
        require(np.allclose(locked_threshold[metric], error_indexed[metric], atol=TOLERANCE),
                f"Threshold factor 1 does not reproduce error summary: {metric}")

    seed = frames["seed"]
    require(len(seed) == 36, "Expected 36 seed-robustness rows")
    require(set(seed["Seed"]) == EXPECTED_SEEDS, "Seed set drift")
    reference_seed = seed[seed["Seed"].eq(2026)].set_index(
        ["Outcome", "Model", "Evaluation_weighting"]
    )
    for metric in ("AUROC", "AUPRC", "Recall", "Precision", "F1", "Specificity", "Brier"):
        require(np.allclose(reference_seed[metric], error_indexed[metric], atol=TOLERANCE),
                f"Seed 2026 does not reproduce locked model: {metric}")

    missing_split = frames["missing_split"]
    require(len(missing_split) == 72, "Expected 2 outcomes x 12 features x 3 splits")
    require(((missing_split["Missing_rate"] >= 0) & (missing_split["Missing_rate"] <= 1)).all(),
            "Missingness rate outside [0,1]")
    require(len(frames["missing_perf"]) == 24, "Expected 24 missingness-stratum rows")

    leakage = frames["leakage"]
    require(len(leakage) == 10, "Expected five lock checks per outcome")
    require(leakage["Status"].eq("PASS").all(), "Leakage/integrity checklist failed")

    composite_selection = frames["composite_selection"]
    composite_perf = frames["composite_perf"]
    composite_split = frames["composite_split"]
    composite_roles = frames["composite_roles"]
    require(len(composite_selection) == 3, "Expected three composite selections")
    require(len(composite_perf) == 6, "Expected three composite models x two weightings")
    require(set(composite_perf["Model"]) == EXPECTED_MODELS, "Composite model coverage drift")
    require(set(composite_perf["Evaluation_weighting"]) == EXPECTED_WEIGHTINGS, "Composite weighting drift")
    require(composite_split["N"].sum() == 32345, "Composite N drift")
    require(composite_split["Positive_N"].sum() == 3014, "Composite positive N drift")
    require(set(composite_split["Split"]) == {"train", "validation", "test"}, "Composite split drift")
    require(set(composite_roles["Role"]) == {"model_selection", "calibration", "threshold"}, "Composite validation role drift")
    require(composite_roles["Positive_N"].ge(40).all(), "Composite validation role unstable")

    require(len(frames["final_model"]) == 6, "Expected six rows in Day 22 final model table")
    require(len(frames["final_error"]) == 6, "Expected six rows in Day 22 final error table")
    require(len(frames["robustness"]) == 6, "Expected six rows in robustness summary")

    svg_files = sorted((out / "figures").glob("*.svg"))
    require(len(svg_files) == 2, "Expected two Day 20-22 SVG figures")
    for svg in svg_files:
        require(svg.stat().st_size > 10_000, f"Suspiciously small SVG: {svg.name}")
        ET.parse(svg)

    project_root = Path.cwd().resolve()
    freeze = pd.read_csv(out / "day22_code_freeze_manifest.csv")
    require(not freeze["Relative_path"].duplicated().any(), "Duplicate freeze path")
    for _, row in freeze.iterrows():
        target = project_root / row["Relative_path"]
        require(target.exists(), f"Freeze target missing: {row['Relative_path']}")
        require(int(target.stat().st_size) == int(row["Size_bytes"]), f"Freeze size drift: {row['Relative_path']}")
        require(sha256(target) == row["SHA256"], f"Freeze hash drift: {row['Relative_path']}")

    require(config["gate4"].startswith("PASS"), "Gate 4 not marked PASS")
    print("PASS: Day 20-22 output integrity verified.")
    print("PASS: locked threshold and seed-2026 reproduction match for all 12 reference arms.")
    print("PASS: 168 eligible aggregate error profiles; no person-level schema exported.")
    print("PASS: threshold, seed, missingness, composite, figures, and code-freeze hashes verified.")


if __name__ == "__main__":
    main()
