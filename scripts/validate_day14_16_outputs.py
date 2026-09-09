#!/usr/bin/env python3
"""Fail-fast integrity checks for committed Day 14-16 aggregate SHAP outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from day8_10_modeling import MAIN, OUTCOMES, day5_bucket


FORBIDDEN_PERSON_LEVEL_COLUMNS = {"HHX", "PPSU", "PSTRAT", "WTFA_A"}
MODELS = ("LR", "RF", "XGBoost")
EXPECTED_AGGREGATIONS = {"Unweighted", "WTFA_A"}
EXPECTED_CHRONIC_LEVELS = {
    "code_0",
    "code_1",
    "code_2",
    "code_3+",
    "Missing/special",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def expected_chronic_counts(data_dir: Path, outcome: str) -> dict[str, int]:
    spec = OUTCOMES[outcome]
    frame = pd.read_csv(
        data_dir / spec["file"],
        dtype={"HHX": "string", "CHRONIC_BURDEN_CAT": "string"},
    )
    test = frame.loc[frame["HHX"].map(day5_bucket).eq("test"), "CHRONIC_BURDEN_CAT"]
    raw = test.astype("string").str.strip()
    labels = raw.map(
        {
            "0": "code_0",
            "1": "code_1",
            "2": "code_2",
            "3+": "code_3+",
        }
    ).fillna("Missing/special")
    return {str(level): int(count) for level, count in labels.value_counts().items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--out-dir", type=Path, default=Path("modeling/day14_16"))
    args = parser.parse_args()
    out = args.out_dir

    config = json.loads((out / "day14_16_config_log.json").read_text(encoding="utf-8"))
    require("code_3+" in config.get("category_label_policy", ""), "Missing category-label policy")
    require(
        "exclude" in config.get("direction_endpoint_policy", "").lower(),
        "Missing direction-endpoint policy",
    )
    for relative in config["outputs"]:
        if "*" in relative:
            require(any(out.glob(relative)), f"Missing output pattern: {relative}")
        else:
            require((out / relative).exists(), f"Missing output: {relative}")

    frames = {
        "global": pd.read_csv(out / "day14_16_shap_global_importance.csv"),
        "encoded": pd.read_csv(out / "day14_16_shap_encoded_importance.csv"),
        "direction": pd.read_csv(out / "day14_16_shap_direction_summary.csv"),
        "category": pd.read_csv(out / "day14_16_shap_category_patterns.csv"),
        "subgroup": pd.read_csv(out / "day14_16_shap_subgroup_patterns.csv"),
        "skipped": pd.read_csv(out / "day14_16_shap_subgroup_skipped.csv"),
        "interaction": pd.read_csv(out / "day14_16_shap_interaction_screen.csv"),
        "reproduction": pd.read_csv(out / "day14_16_locked_reproduction_audit.csv"),
    }

    for name, frame in frames.items():
        leaked = FORBIDDEN_PERSON_LEVEL_COLUMNS & set(frame.columns)
        require(not leaked, f"{name}: forbidden person-level columns: {sorted(leaked)}")

    global_frame = frames["global"]
    direction = frames["direction"]
    category = frames["category"]
    reproduction = frames["reproduction"]

    require(set(global_frame["Outcome"]) == set(OUTCOMES), "Outcome coverage drift")
    require(set(global_frame["Model"]) == set(MODELS), "Model coverage drift")
    require(set(global_frame["Aggregation"]) == EXPECTED_AGGREGATIONS, "Aggregation coverage drift")
    require(set(global_frame["Feature_construct"]) == set(MAIN), "Feature coverage drift")
    require(len(reproduction) == len(OUTCOMES) * len(MODELS), "Reproduction row-count drift")
    require(reproduction["Status"].eq("PASS").all(), "Locked reproduction did not pass")
    require(
        reproduction["Max_absolute_metric_difference"].max()
        <= reproduction["Tolerance"].min(),
        "Locked reproduction tolerance exceeded",
    )

    categorical_direction = direction[direction["Feature_construct"].ne("AGEP_A")]
    require(
        categorical_direction["Direction_method"].str.contains(
            "missing/special retained in category table but excluded from endpoints",
            regex=False,
        ).all(),
        "Categorical direction method does not document missing-value exclusion",
    )
    require(
        ~categorical_direction["Direction_summary"].str.contains(
            "Missing/special", regex=False
        ).any(),
        "Missing/special was used as a categorical direction endpoint",
    )

    for row in categorical_direction.itertuples(index=False):
        levels = category[
            category["Outcome"].eq(row.Outcome)
            & category["Model"].eq(row.Model)
            & category["Feature_construct"].eq(row.Feature_construct)
            & category["Level"].ne("Missing/special")
        ]
        require(not levels.empty, f"{row.Outcome}/{row.Model}/{row.Feature_construct}: no substantive levels")
        lowest = levels.loc[levels["Weighted_mean_SHAP"].idxmin(), "Level"]
        highest = levels.loc[levels["Weighted_mean_SHAP"].idxmax(), "Level"]
        expected_summary = f"category-specific: lowest {lowest}; highest {highest}"
        require(
            row.Direction_summary == expected_summary,
            f"{row.Outcome}/{row.Model}/{row.Feature_construct}: direction summary mismatch",
        )

    for outcome in OUTCOMES:
        expected = expected_chronic_counts(args.data_dir, outcome)
        require(set(expected) == EXPECTED_CHRONIC_LEVELS, f"{outcome}: source chronic levels drift")
        for model in MODELS:
            observed_frame = category[
                category["Outcome"].eq(outcome)
                & category["Model"].eq(model)
                & category["Feature_construct"].eq("CHRONIC_BURDEN_CAT")
            ]
            observed = {
                str(row.Level): int(row.N)
                for row in observed_frame[["Level", "N"]].itertuples(index=False)
            }
            require(
                observed == expected,
                f"{outcome}/{model}: chronic category partition mismatch; "
                f"expected={expected}, observed={observed}",
            )

    print("PASS: Day 14-16 aggregate SHAP output integrity verified.")
    print("PASS: CHRONIC_BURDEN_CAT preserves code_3+ separately from true missing values.")
    print("PASS: six locked-model reproduction rows remain within tolerance.")


if __name__ == "__main__":
    main()
