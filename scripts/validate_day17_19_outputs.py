#!/usr/bin/env python3
"""Fail-fast integrity checks for committed Day 17-19 aggregate outputs."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd


FORBIDDEN_PERSON_LEVEL_COLUMNS = {"HHX", "PPSU", "PSTRAT", "WTFA_A", "Prediction", "Probability"}
EXPECTED_MODELS = {"LR", "RF", "XGBoost"}
EXPECTED_OUTCOMES = {"MEDNG", "MEDDL"}
EXPECTED_WEIGHTINGS = {"Unweighted", "WTFA_A"}
EXPECTED_AXES = {"Race_ethnicity", "Poverty", "Insurance", "Sex", "Age"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("modeling/day17_19"))
    args = parser.parse_args()
    out = args.out_dir

    config = json.loads((out / "day17_19_config_log.json").read_text(encoding="utf-8"))
    for relative in config["outputs"]:
        if "*" in relative:
            require(any(out.glob(relative)), f"Missing output pattern: {relative}")
        else:
            require((out / relative).exists(), f"Missing output: {relative}")

    performance = pd.read_csv(out / "day17_19_subgroup_performance.csv")
    skipped = pd.read_csv(out / "day17_19_subgroup_skipped.csv")
    ci = pd.read_csv(out / "day17_19_subgroup_metric_cluster_bootstrap_ci.csv")
    disparity = pd.read_csv(out / "day17_19_disparity_summary.csv")
    disparity_ci = pd.read_csv(out / "day17_19_disparity_cluster_bootstrap_ci.csv")
    reproduction = pd.read_csv(out / "day17_19_locked_reproduction_audit.csv")
    split = pd.read_csv(out / "day17_19_split_audit.csv")

    for name, frame in {
        "performance": performance,
        "skipped": skipped,
        "ci": ci,
        "disparity": disparity,
        "disparity_ci": disparity_ci,
        "reproduction": reproduction,
        "split": split,
    }.items():
        leaked = FORBIDDEN_PERSON_LEVEL_COLUMNS & set(frame.columns)
        require(not leaked, f"{name}: forbidden person-level columns: {sorted(leaked)}")

    require(set(performance["Outcome"]) == EXPECTED_OUTCOMES, "Outcome coverage drift")
    require(set(performance["Model"]) == EXPECTED_MODELS, "Model coverage drift")
    require(set(performance["Evaluation_weighting"]) == EXPECTED_WEIGHTINGS, "Weighting coverage drift")
    require(set(performance["Axis"]) == EXPECTED_AXES, "Axis coverage drift")
    require(performance["Eligible_for_comparison"].all(), "Ineligible row leaked into performance table")
    require(not performance.duplicated(["Outcome", "Model", "Evaluation_weighting", "Axis", "Group"]).any(), "Duplicate performance key")
    require(not skipped.duplicated(["Outcome", "Model", "Axis", "Group"]).any(), "Duplicate skipped key")

    require(np.allclose(performance["Recall"] + performance["FNR"], 1.0, atol=1e-12), "Recall + FNR invariant failed")
    require(np.allclose(performance["Specificity"] + performance["FPR"], 1.0, atol=1e-12), "Specificity + FPR invariant failed")
    probabilities = [
        "Observed_prevalence", "Mean_predicted_probability", "Predicted_positive_rate",
        "AUROC", "AUPRC", "Recall", "FNR", "FPR", "Specificity", "Precision",
        "F1", "Brier", "Calibration_abs_error", "ECE_5bin",
    ]
    require(((performance[probabilities] >= 0) & (performance[probabilities] <= 1)).all().all(), "Probability metric outside [0,1]")

    require(len(reproduction) == 12, "Expected 12 reproduction rows")
    require(reproduction["Status"].eq("PASS").all(), "Locked reproduction did not pass")
    require(reproduction["Max_absolute_metric_difference"].max() <= reproduction["Tolerance"].min(), "Reproduction tolerance exceeded")
    require(set(split["Split"]) == {"train", "validation", "test"}, "Split coverage drift")
    require(len(split) == 6, "Expected two outcomes x three split rows")

    requested = int(config["uncertainty"]["requested_replicates"])
    require(ci["Requested_replicates"].eq(requested).all(), "Subgroup CI requested-replicate drift")
    require(disparity_ci["Requested_replicates"].eq(requested).all(), "Gap CI requested-replicate drift")
    require(ci["Valid_replicates"].ge(max(1, int(0.95 * requested))).all(), "Too few valid subgroup bootstrap replicates")
    require(disparity_ci["Valid_replicates"].ge(max(1, int(0.95 * requested))).all(), "Too few valid gap bootstrap replicates")
    require((ci["CI95_lower"] <= ci["CI95_upper"]).all(), "Subgroup CI bounds reversed")
    require((disparity_ci["CI95_lower"] <= disparity_ci["CI95_upper"]).all(), "Gap CI bounds reversed")

    for key, group in disparity[disparity["Metric"].ne("Not_estimable")].groupby(
        ["Outcome", "Model", "Evaluation_weighting", "Axis", "Metric"], observed=True
    ):
        outcome, model, weighting, axis, metric = key
        values = performance[
            performance["Outcome"].eq(outcome)
            & performance["Model"].eq(model)
            & performance["Evaluation_weighting"].eq(weighting)
            & performance["Axis"].eq(axis)
        ][metric]
        require(len(values) >= 2, f"{key}: disparity has fewer than two groups")
        expected = float(values.max() - values.min())
        require(np.isclose(float(group.iloc[0]["Max_minus_min"]), expected, atol=1e-12), f"{key}: disparity recomputation failed")

    svg_files = sorted((out / "figures").glob("*.svg"))
    require(len(svg_files) == 4, "Expected four SVG figures")
    for svg in svg_files:
        require(svg.stat().st_size > 10_000, f"Suspiciously small figure: {svg.name}")
        ET.parse(svg)

    print("PASS: Day 17-19 output integrity verified.")
    print(f"PASS: 12/12 locked reproduction rows; max drift={reproduction['Max_absolute_metric_difference'].max():.3e}.")
    print(f"PASS: {len(performance)} eligible subgroup rows, {len(skipped)} skipped rows, {requested} bootstrap replicates.")
    print("PASS: metric invariants, disparity recomputation, privacy schema, manifest, and four SVGs.")


if __name__ == "__main__":
    main()
