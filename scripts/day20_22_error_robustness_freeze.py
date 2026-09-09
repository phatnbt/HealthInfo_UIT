#!/usr/bin/env python3
"""NHIS 2024 Day 20-22 aggregate error analysis, robustness, and code freeze.

The Day 8-10 estimators, feature set, HHX split, probability version, and
validation-selected threshold remain locked. Day 20-21 only audits errors and
prespecified sensitivity analyses. The composite outcome is a separate
sensitivity model built on the common analyzable cohort without test-driven
tuning. Day 22 writes manuscript-facing tables, figures, and a hash manifest.

Privacy boundary: no HHX, person-level probability, or person-level prediction
is written to disk. All outputs are aggregate tables, figures, or file hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, brier_score_loss
from xgboost import XGBClassifier

from day8_10_modeling import (
    MAIN,
    OUTCOMES,
    SEED,
    SPECIAL,
    PlattScaler,
    assert_day5_split,
    build_lr,
    clean_features,
    day5_bucket,
    make_prep,
    select_threshold,
    validation_role,
)
from day17_19_fairness_audit import AXES, eligibility, subgroup_labels, subgroup_metrics


MODELS = ("LR", "RF", "XGBoost")
WEIGHTINGS = ("Unweighted", "WTFA_A")
THRESHOLD_FACTORS = (0.8, 1.0, 1.2)
ROBUSTNESS_SEEDS = (2026, 2037, 2048)
PERFORMANCE_METRICS = (
    "AUROC", "AUPRC", "Recall", "Precision", "F1", "Specificity", "Brier",
    "Observed_prevalence", "Mean_predicted_probability", "Predicted_positive_rate",
)
FORBIDDEN_PREDICTORS = {
    "HHX", "WTFA_A", "PPSU", "PSTRAT", "MEDNG12M_A", "MEDDL12M_A",
    "TARGET_FORGONE_COST", "TARGET_DELAYED_COST", "TARGET_ANY_COST_BARRIER",
}
EXPECTED_COMMON_N = 32345
EXPECTED_COMMON_POSITIVE_N = 3014


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_model(model_name: str, params: dict, n_jobs: int, seed: int):
    if model_name == "LR":
        return build_lr()
    if model_name == "RF":
        return RandomForestClassifier(
            **params, random_state=seed, class_weight=None, n_jobs=n_jobs
        )
    if model_name == "XGBoost":
        return XGBClassifier(
            **params,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            reg_lambda=1.0,
            random_state=seed,
            n_jobs=n_jobs,
        )
    raise ValueError(model_name)


def selected_probabilities(
    model,
    x_validation,
    y_validation: np.ndarray,
    validation_roles: np.ndarray,
    x_test,
    selected_probability: str,
) -> np.ndarray:
    calibration_mask = validation_roles == "calibration"
    raw_calibration = model.predict_proba(x_validation[calibration_mask])[:, 1]
    raw_test = model.predict_proba(x_test)[:, 1]
    if selected_probability == "Raw":
        return raw_test
    if selected_probability != "Platt":
        raise RuntimeError(f"Unknown probability version: {selected_probability}")
    platt = PlattScaler().fit(raw_calibration, y_validation[calibration_mask])
    return platt.transform(raw_test)


def metrics(y: np.ndarray, probs: np.ndarray, threshold: float, weights: np.ndarray) -> dict:
    result = subgroup_metrics(y, probs, threshold, weights)
    return {name: float(result[name]) for name in PERFORMANCE_METRICS}


def confusion_values(
    y: np.ndarray, probs: np.ndarray, threshold: float, weights: np.ndarray
) -> dict:
    pred = probs >= threshold
    positive = y == 1
    negative = ~positive
    tp = float(np.sum(weights[positive & pred]))
    fn = float(np.sum(weights[positive & ~pred]))
    fp = float(np.sum(weights[negative & pred]))
    tn = float(np.sum(weights[negative & ~pred]))
    return {"TN": tn, "FP": fp, "FN": fn, "TP": tp}


def raw_missing_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    result = {}
    for feature in MAIN:
        if feature == "CHRONIC_BURDEN_CAT":
            text = frame[feature].astype("string").str.strip()
            result[feature] = frame[feature].isna() | text.isin(["", "Missing/indeterminate"])
        else:
            numeric = pd.to_numeric(frame[feature], errors="coerce")
            result[feature] = numeric.isna() | numeric.isin(SPECIAL.get(feature, set()))
    return pd.DataFrame(result, index=frame.index)


def append_error_outputs(
    outcome: str,
    model_name: str,
    selected_probability: str,
    threshold: float,
    test_frame: pd.DataFrame,
    y_test: np.ndarray,
    probs: np.ndarray,
    summary_rows: list[dict],
    profile_rows: list[dict],
) -> None:
    pred = probs >= threshold
    positive = y_test == 1
    negative = ~positive
    for weighting in WEIGHTINGS:
        weights = (
            np.ones(len(y_test), dtype=float)
            if weighting == "Unweighted"
            else test_frame["WTFA_A"].to_numpy(dtype=float)
        )
        perf = metrics(y_test, probs, threshold, weights)
        counts = confusion_values(y_test, probs, threshold, weights)
        summary_rows.append({
            "Outcome": outcome,
            "Model": model_name,
            "Evaluation_weighting": weighting,
            "Selected_probability": selected_probability,
            "Locked_threshold": threshold,
            "N": int(len(y_test)),
            "Positive_N": int(np.sum(positive)),
            "Negative_N": int(np.sum(negative)),
            "TN_weighted_count": counts["TN"],
            "FP_weighted_count": counts["FP"],
            "FN_weighted_count": counts["FN"],
            "TP_weighted_count": counts["TP"],
            "FNR": 1.0 - perf["Recall"],
            "FPR": 1.0 - perf["Specificity"],
            **perf,
            "Interpretation": "Aggregate operating-point audit; not a clinical or individual risk rule.",
        })

        total_fn = float(np.sum(weights[positive & ~pred]))
        total_fp = float(np.sum(weights[negative & pred]))
        for axis in AXES:
            labels = subgroup_labels(test_frame, axis).to_numpy(dtype=object)
            for group in AXES[axis]["order"]:
                mask = labels == group
                if not np.any(mask):
                    continue
                n = int(np.sum(mask))
                positive_n = int(np.sum(y_test[mask]))
                negative_n = n - positive_n
                eligible, reason = eligibility(n, positive_n, negative_n)
                if not eligible:
                    continue
                local_pred = pred[mask]
                local_y = y_test[mask]
                local_weights = weights[mask]
                local_positive = local_y == 1
                local_negative = ~local_positive
                fn = float(np.sum(local_weights[local_positive & ~local_pred]))
                fp = float(np.sum(local_weights[local_negative & local_pred]))
                profile_rows.append({
                    "Outcome": outcome,
                    "Model": model_name,
                    "Evaluation_weighting": weighting,
                    "Selected_probability": selected_probability,
                    "Locked_threshold": threshold,
                    "Axis": axis,
                    "Group": group,
                    "N": n,
                    "Positive_N": positive_n,
                    "Negative_N": negative_n,
                    "FN_weighted_count": fn,
                    "FP_weighted_count": fp,
                    "FNR": fn / float(np.sum(local_weights[local_positive])),
                    "FPR": fp / float(np.sum(local_weights[local_negative])),
                    "Share_of_all_FN": fn / total_fn if total_fn else np.nan,
                    "Share_of_all_FP": fp / total_fp if total_fp else np.nan,
                    "Eligibility_rule": reason or "PASS",
                    "Interpretation_boundary": "Group-level aggregate; do not use for individual micro-targeting.",
                })


def plot_error_rates(error_summary: pd.DataFrame, output_path: Path) -> None:
    selected = error_summary[error_summary["Evaluation_weighting"].eq("WTFA_A")].copy()
    selected["Label"] = selected["Outcome"] + " / " + selected["Model"]
    selected = selected.sort_values(["Outcome", "Model"])
    x = np.arange(len(selected))
    width = 0.36
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    ax.bar(x - width / 2, selected["FNR"], width, label="FNR", color="#2563EB")
    ax.bar(x + width / 2, selected["FPR"], width, label="FPR", color="#F97316")
    ax.set_xticks(x, selected["Label"], rotation=25, ha="right")
    ax.set_ylabel("Weighted error rate")
    ax.set_ylim(0, 1.05)
    ax.set_title("Locked-test error trade-off at validation-selected thresholds")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def plot_threshold_robustness(threshold: pd.DataFrame, output_path: Path) -> None:
    selected = threshold[threshold["Evaluation_weighting"].eq("WTFA_A")]
    colors = {"LR": "#2563EB", "RF": "#F97316", "XGBoost": "#059669"}
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for ax, outcome in zip(axes, ("MEDNG", "MEDDL")):
        for model in MODELS:
            current = selected[selected["Outcome"].eq(outcome) & selected["Model"].eq(model)]
            ax.plot(
                current["Threshold_factor"], current["F1"], marker="o",
                label=model, color=colors[model], linewidth=2,
            )
        ax.axvline(1.0, color="black", linestyle="--", linewidth=1)
        ax.set_title(outcome)
        ax.set_xlabel("Locked-threshold multiplier")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("WTFA_A-weighted F1")
    axes[-1].legend(title="Model")
    fig.suptitle("Prespecified threshold perturbation (no threshold reselection)")
    fig.tight_layout()
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def composite_sensitivity(
    data_dir: Path,
    locked_config: dict,
    n_jobs: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict]]:
    ng = pd.read_csv(data_dir / OUTCOMES["MEDNG"]["file"])
    dl = pd.read_csv(data_dir / OUTCOMES["MEDDL"]["file"])
    compare_columns = ["WTFA_A", "PPSU", "PSTRAT", *MAIN]
    joined = ng[["HHX", *compare_columns, "TARGET_FORGONE_COST"]].merge(
        dl[["HHX", *compare_columns, "TARGET_DELAYED_COST"]],
        on="HHX", how="inner", suffixes=("_NG", "_DL"), validate="one_to_one",
    )
    if len(joined) != EXPECTED_COMMON_N:
        raise RuntimeError(f"Common cohort N={len(joined)} != {EXPECTED_COMMON_N}")
    for column in compare_columns:
        left = joined[f"{column}_NG"].astype("string").fillna("<NA>")
        right = joined[f"{column}_DL"].astype("string").fillna("<NA>")
        if not left.equals(right):
            raise RuntimeError(f"Common-cohort source disagreement: {column}")

    frame = pd.DataFrame({"HHX": joined["HHX"]})
    for column in compare_columns:
        frame[column] = joined[f"{column}_NG"]
    frame["TARGET_ANY_COST_BARRIER"] = (
        joined["TARGET_FORGONE_COST"].astype(int)
        | joined["TARGET_DELAYED_COST"].astype(int)
    ).astype(int)
    if int(frame["TARGET_ANY_COST_BARRIER"].sum()) != EXPECTED_COMMON_POSITIVE_N:
        raise RuntimeError("Composite positive count drift")
    frame["SPLIT"] = frame["HHX"].map(day5_bucket)
    split_rows = []
    for split in ("train", "validation", "test"):
        mask = frame["SPLIT"].eq(split)
        split_rows.append({
            "Outcome": "ANY_COST",
            "Split": split,
            "N": int(mask.sum()),
            "Positive_N": int(frame.loc[mask, "TARGET_ANY_COST_BARRIER"].sum()),
        })

    clean = clean_features(frame)
    y = frame["TARGET_ANY_COST_BARRIER"].to_numpy(dtype=int)
    split = frame["SPLIT"].to_numpy()
    train, validation, test = split == "train", split == "validation", split == "test"
    roles = np.array([validation_role(h) for h in frame.loc[validation, "HHX"]])
    y_validation = y[validation]
    prep = make_prep()
    x_train = prep.fit_transform(clean.loc[train])
    x_validation = prep.transform(clean.loc[validation])
    x_test = prep.transform(clean.loc[test])
    selection_rows = []
    performance_rows = []
    validation_audit = []
    for role in ("model_selection", "calibration", "threshold"):
        mask = roles == role
        validation_audit.append({
            "Outcome": "ANY_COST", "Role": role, "N": int(mask.sum()),
            "Positive_N": int(y_validation[mask].sum()),
            "Positive_rate": float(np.mean(y_validation[mask])),
        })
        if int(y_validation[mask].sum()) < 40:
            raise RuntimeError(f"Composite validation role {role} has too few positives")

    for model_name in MODELS:
        params = locked_config["best_params"]["MEDNG"][model_name]
        if model_name == "LR":
            params = {"C": 1.0}
        model = build_model(model_name, params, n_jobs, SEED)
        model.fit(x_train, y[train])
        calibration_mask = roles == "calibration"
        threshold_mask = roles == "threshold"
        raw_calibration = model.predict_proba(x_validation[calibration_mask])[:, 1]
        raw_threshold = model.predict_proba(x_validation[threshold_mask])[:, 1]
        raw_test = model.predict_proba(x_test)[:, 1]
        platt = PlattScaler().fit(raw_calibration, y_validation[calibration_mask])
        platt_threshold = platt.transform(raw_threshold)
        platt_test = platt.transform(raw_test)
        raw_brier = float(brier_score_loss(y_validation[threshold_mask], raw_threshold))
        platt_brier = float(brier_score_loss(y_validation[threshold_mask], platt_threshold))
        use_platt = platt_brier < raw_brier
        probability_version = "Platt" if use_platt else "Raw"
        selected_threshold_probs = platt_threshold if use_platt else raw_threshold
        selected_test_probs = platt_test if use_platt else raw_test
        threshold, validation_f1 = select_threshold(
            selected_threshold_probs, y_validation[threshold_mask]
        )
        selection_rows.append({
            "Outcome": "ANY_COST",
            "Model": model_name,
            "Hyperparameter_source": "MEDNG locked Day 8-10; no composite tuning",
            "Selected_probability": probability_version,
            "Raw_validation_Brier": raw_brier,
            "Platt_validation_Brier": platt_brier,
            "Threshold": threshold,
            "Validation_F1": validation_f1,
            "Validation_AUPRC": float(average_precision_score(
                y_validation[threshold_mask], selected_threshold_probs
            )),
        })
        test_frame = frame.loc[test].reset_index(drop=True)
        y_test = y[test]
        for weighting in WEIGHTINGS:
            weights = (
                np.ones(len(y_test), dtype=float)
                if weighting == "Unweighted"
                else test_frame["WTFA_A"].to_numpy(dtype=float)
            )
            performance_rows.append({
                "Outcome": "ANY_COST",
                "Model": model_name,
                "Evaluation_weighting": weighting,
                "Hyperparameter_source": "MEDNG locked Day 8-10; no composite tuning",
                "Selected_probability": probability_version,
                "Validation_selected_threshold": threshold,
                **metrics(y_test, selected_test_probs, threshold, weights),
            })
    return (
        pd.DataFrame(selection_rows),
        pd.DataFrame(performance_rows),
        pd.DataFrame(split_rows),
        validation_audit,
    )


def runtime_versions() -> dict:
    return {
        name: importlib.metadata.version(name)
        for name in ("numpy", "pandas", "scikit-learn", "xgboost", "matplotlib")
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--locked-dir", type=Path, default=Path("modeling/day8_10"))
    parser.add_argument("--day11-dir", type=Path, default=Path("modeling/day11_13"))
    parser.add_argument("--day17-dir", type=Path, default=Path("modeling/day17_19"))
    parser.add_argument("--out-dir", type=Path, default=Path("modeling/day20_22"))
    parser.add_argument("--n-jobs", type=int, default=2)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = args.out_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    locked_config = json.loads(
        (args.locked_dir / "day8_10_config_log.json").read_text(encoding="utf-8")
    )
    locked_selection = pd.read_csv(
        args.locked_dir / "day8_10_validation_selection.csv"
    ).set_index(["Outcome", "Model"])
    if set(MAIN) & FORBIDDEN_PREDICTORS:
        raise RuntimeError("Forbidden target/identifier/survey field found in MAIN")

    error_summary_rows = []
    error_profile_rows = []
    threshold_rows = []
    seed_rows = []
    missingness_rows = []
    missingness_performance_rows = []
    lock_rows = []
    split_sets = {}

    for outcome, spec in OUTCOMES.items():
        print(f"\n=== {outcome}: Day 20-21 error and robustness audit ===", flush=True)
        frame = pd.read_csv(args.data_dir / spec["file"])
        required = set(MAIN + ["HHX", "WTFA_A", "PSTRAT", "PPSU", spec["target"]])
        missing_columns = sorted(required - set(frame.columns))
        if missing_columns:
            raise RuntimeError(f"{outcome}: missing columns {missing_columns}")
        if not frame["HHX"].is_unique:
            raise RuntimeError(f"{outcome}: HHX is not unique")
        if frame[["WTFA_A", "PSTRAT", "PPSU"]].isna().any().any():
            raise RuntimeError(f"{outcome}: missing survey design field")
        if (frame["WTFA_A"] <= 0).any():
            raise RuntimeError(f"{outcome}: non-positive weight")
        frame["SPLIT"] = frame["HHX"].map(day5_bucket)
        assert_day5_split(frame, outcome, spec["target"])
        split_sets[outcome] = {
            split: set(frame.loc[frame["SPLIT"].eq(split), "HHX"])
            for split in ("train", "validation", "test")
        }
        if any(
            split_sets[outcome][a] & split_sets[outcome][b]
            for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))
        ):
            raise RuntimeError(f"{outcome}: split overlap")

        missing_matrix = raw_missing_matrix(frame)
        for split in ("train", "validation", "test"):
            split_mask = frame["SPLIT"].eq(split)
            for feature in MAIN:
                count = int(missing_matrix.loc[split_mask, feature].sum())
                n = int(split_mask.sum())
                missingness_rows.append({
                    "Outcome": outcome, "Feature": feature, "Split": split,
                    "N": n, "Missing_N": count, "Missing_rate": count / n,
                    "Handling": "Train-fitted imputation" if feature != "CHRONIC_BURDEN_CAT" else "Explicit Missing/indeterminate category",
                })

        clean = clean_features(frame)
        y = frame[spec["target"]].to_numpy(dtype=int)
        split = frame["SPLIT"].to_numpy()
        train, validation, test = split == "train", split == "validation", split == "test"
        roles = np.array([validation_role(h) for h in frame.loc[validation, "HHX"]])
        y_validation = y[validation]
        prep = make_prep()
        x_train = prep.fit_transform(clean.loc[train])
        x_validation = prep.transform(clean.loc[validation])
        x_test = prep.transform(clean.loc[test])
        y_test = y[test]
        test_frame = frame.loc[test].reset_index(drop=True)
        test_missing_count = missing_matrix.loc[test].sum(axis=1).to_numpy(dtype=int)

        for model_name in MODELS:
            print(f"  {model_name}: locked errors, threshold and seed sensitivity", flush=True)
            selected = locked_selection.loc[(outcome, model_name)]
            selected_probability = str(selected["Selected_probability"])
            locked_threshold = float(selected["Threshold"])
            params = locked_config["best_params"][outcome][model_name]
            if model_name == "LR":
                params = {"C": 1.0}

            reference_model = build_model(model_name, params, args.n_jobs, SEED)
            reference_model.fit(x_train, y[train])
            reference_probs = selected_probabilities(
                reference_model, x_validation, y_validation, roles, x_test, selected_probability
            )
            append_error_outputs(
                outcome, model_name, selected_probability, locked_threshold,
                test_frame, y_test, reference_probs, error_summary_rows, error_profile_rows,
            )

            for factor in THRESHOLD_FACTORS:
                perturbed = float(np.clip(locked_threshold * factor, 0.01, 0.99))
                for weighting in WEIGHTINGS:
                    weights = (
                        np.ones(len(y_test), dtype=float)
                        if weighting == "Unweighted"
                        else test_frame["WTFA_A"].to_numpy(dtype=float)
                    )
                    threshold_rows.append({
                        "Outcome": outcome,
                        "Model": model_name,
                        "Evaluation_weighting": weighting,
                        "Selected_probability": selected_probability,
                        "Locked_threshold": locked_threshold,
                        "Threshold_factor": factor,
                        "Evaluated_threshold": perturbed,
                        **metrics(y_test, reference_probs, perturbed, weights),
                        "Decision_rule": "Prespecified perturbation only; never used to replace the locked threshold.",
                    })

            for seed in ROBUSTNESS_SEEDS:
                if seed == SEED:
                    seed_probs = reference_probs
                else:
                    seed_model = build_model(model_name, params, args.n_jobs, seed)
                    seed_model.fit(x_train, y[train])
                    seed_probs = selected_probabilities(
                        seed_model, x_validation, y_validation, roles, x_test, selected_probability
                    )
                for weighting in WEIGHTINGS:
                    weights = (
                        np.ones(len(y_test), dtype=float)
                        if weighting == "Unweighted"
                        else test_frame["WTFA_A"].to_numpy(dtype=float)
                    )
                    seed_rows.append({
                        "Outcome": outcome,
                        "Model": model_name,
                        "Evaluation_weighting": weighting,
                        "Seed": seed,
                        "Selected_probability": selected_probability,
                        "Locked_threshold": locked_threshold,
                        **metrics(y_test, seed_probs, locked_threshold, weights),
                        "Decision_rule": "Robustness range only; no seed chosen from test performance.",
                    })

            for label, stratum_mask in (
                ("No cleaned-feature missing", test_missing_count == 0),
                (">=1 cleaned-feature missing", test_missing_count >= 1),
            ):
                local_y = y_test[stratum_mask]
                positive_n = int(np.sum(local_y))
                negative_n = int(len(local_y) - positive_n)
                eligible, reason = eligibility(len(local_y), positive_n, negative_n)
                if not eligible:
                    raise RuntimeError(f"{outcome}/{model_name}/{label}: {reason}")
                for weighting in WEIGHTINGS:
                    base_weights = (
                        np.ones(len(y_test), dtype=float)
                        if weighting == "Unweighted"
                        else test_frame["WTFA_A"].to_numpy(dtype=float)
                    )
                    missingness_performance_rows.append({
                        "Outcome": outcome,
                        "Model": model_name,
                        "Evaluation_weighting": weighting,
                        "Missingness_stratum": label,
                        "N": int(np.sum(stratum_mask)),
                        "Positive_N": positive_n,
                        "Negative_N": negative_n,
                        **metrics(
                            local_y, reference_probs[stratum_mask], locked_threshold,
                            base_weights[stratum_mask],
                        ),
                        "Interpretation": "Evaluation stratum only; preprocessing and model were not refit.",
                    })

        lock_rows.extend([
            {
                "Outcome": outcome, "Check": "Predictor lock excludes identifiers, survey design and outcomes",
                "Status": "PASS", "Evidence": f"12 constructs exactly; forbidden intersection={sorted(set(MAIN) & FORBIDDEN_PREDICTORS)}",
                "Why_it_matters": "Prevents direct target leakage and use of survey fields as predictors.",
            },
            {
                "Outcome": outcome, "Check": "Deterministic split integrity",
                "Status": "PASS", "Evidence": "Day-5 HHX SHA-256 70/10/20 counts match and split intersections are empty.",
                "Why_it_matters": "Prevents train/validation/test overlap.",
            },
            {
                "Outcome": outcome, "Check": "Train-only preprocessing",
                "Status": "PASS", "Evidence": "make_prep().fit_transform called only on train; validation/test use transform.",
                "Why_it_matters": "Prevents preprocessing leakage.",
            },
            {
                "Outcome": outcome, "Check": "Probability and threshold lock",
                "Status": "PASS", "Evidence": "Raw/Platt and threshold read from Day 8-10 validation_selection; subgroup/test never reselect them.",
                "Why_it_matters": "Prevents test-driven optimization.",
            },
            {
                "Outcome": outcome, "Check": "Other outcome excluded from predictors",
                "Status": "PASS", "Evidence": "MEDNG and MEDDL modeled separately; neither raw/derived outcome appears in MAIN.",
                "Why_it_matters": "Prevents outcome-to-outcome leakage.",
            },
        ])

    error_summary = pd.DataFrame(error_summary_rows)
    error_profile = pd.DataFrame(error_profile_rows)
    threshold_frame = pd.DataFrame(threshold_rows)
    seed_frame = pd.DataFrame(seed_rows)
    missingness_frame = pd.DataFrame(missingness_rows)
    missingness_performance = pd.DataFrame(missingness_performance_rows)
    lock_frame = pd.DataFrame(lock_rows)

    composite_selection, composite_performance, composite_split, composite_roles = composite_sensitivity(
        args.data_dir, locked_config, args.n_jobs
    )

    error_summary.to_csv(args.out_dir / "day20_22_error_summary.csv", index=False)
    error_profile.to_csv(args.out_dir / "day20_22_error_profile_by_group.csv", index=False)
    threshold_frame.to_csv(args.out_dir / "day20_22_threshold_robustness.csv", index=False)
    seed_frame.to_csv(args.out_dir / "day20_22_seed_robustness.csv", index=False)
    missingness_frame.to_csv(args.out_dir / "day20_22_missingness_by_split.csv", index=False)
    missingness_performance.to_csv(
        args.out_dir / "day20_22_missingness_performance.csv", index=False
    )
    lock_frame.to_csv(args.out_dir / "day20_22_leakage_integrity_checklist.csv", index=False)
    composite_selection.to_csv(
        args.out_dir / "day20_22_composite_validation_selection.csv", index=False
    )
    composite_performance.to_csv(
        args.out_dir / "day20_22_composite_sensitivity_performance.csv", index=False
    )
    composite_split.to_csv(args.out_dir / "day20_22_composite_split_audit.csv", index=False)
    pd.DataFrame(composite_roles).to_csv(
        args.out_dir / "day20_22_composite_validation_role_audit.csv", index=False
    )

    # Manuscript-facing compact tables.
    day8 = pd.read_csv(args.locked_dir / "day8_10_model_performance.csv")
    day11 = pd.read_csv(args.day11_dir / "day11_13_weighted_model_sensitivity.csv")
    day11 = day11[
        day11["Training_weighting"].eq("Unweighted")
        & day11["Evaluation_weighting"].eq("WTFA_A")
    ]
    final_rows = []
    for _, base in day8.iterrows():
        weighted = day11[
            day11["Outcome"].eq(base["Outcome"]) & day11["Model"].eq(base["Model"])
        ].iloc[0]
        final_rows.append({
            "Outcome": base["Outcome"], "Model": base["Model"],
            "Selected_probability": base["Selected_probability"], "Locked_threshold": base["Threshold"],
            **{f"Unweighted_{m}": base[m] for m in ("AUROC", "AUPRC", "Recall", "Precision", "F1", "Specificity", "Brier")},
            **{f"WTFA_A_{m}": weighted[m] for m in ("AUROC", "AUPRC", "Recall", "Precision", "F1", "Specificity", "Brier")},
        })
    final_model_table = pd.DataFrame(final_rows).sort_values(["Outcome", "Model"])
    final_model_table.to_csv(args.out_dir / "day22_final_model_table.csv", index=False)
    error_summary[error_summary["Evaluation_weighting"].eq("WTFA_A")].to_csv(
        args.out_dir / "day22_final_error_table.csv", index=False
    )

    robustness_rows = []
    for (outcome, model), group in threshold_frame[
        threshold_frame["Evaluation_weighting"].eq("WTFA_A")
    ].groupby(["Outcome", "Model"], observed=True):
        seed_group = seed_frame[
            seed_frame["Outcome"].eq(outcome)
            & seed_frame["Model"].eq(model)
            & seed_frame["Evaluation_weighting"].eq("WTFA_A")
        ]
        missing_group = missingness_performance[
            missingness_performance["Outcome"].eq(outcome)
            & missingness_performance["Model"].eq(model)
            & missingness_performance["Evaluation_weighting"].eq("WTFA_A")
        ].set_index("Missingness_stratum")
        robustness_rows.append({
            "Outcome": outcome,
            "Model": model,
            "Threshold_F1_min": float(group["F1"].min()),
            "Threshold_F1_max": float(group["F1"].max()),
            "Threshold_Recall_min": float(group["Recall"].min()),
            "Threshold_Recall_max": float(group["Recall"].max()),
            "Seed_AUPRC_min": float(seed_group["AUPRC"].min()),
            "Seed_AUPRC_max": float(seed_group["AUPRC"].max()),
            "Seed_AUROC_min": float(seed_group["AUROC"].min()),
            "Seed_AUROC_max": float(seed_group["AUROC"].max()),
            "F1_no_missing": float(missing_group.loc["No cleaned-feature missing", "F1"]),
            "F1_with_missing": float(missing_group.loc[">=1 cleaned-feature missing", "F1"]),
            "Interpretation": "Sensitivity range only; no post-test model/seed/threshold selection.",
        })
    robustness_summary = pd.DataFrame(robustness_rows)
    robustness_summary.to_csv(args.out_dir / "day22_robustness_summary.csv", index=False)

    plot_error_rates(error_summary, figure_dir / "day20_22_weighted_error_tradeoff.svg")
    plot_threshold_robustness(
        threshold_frame, figure_dir / "day20_22_threshold_robustness.svg"
    )

    outputs = [
        "day20_22_error_summary.csv",
        "day20_22_error_profile_by_group.csv",
        "day20_22_threshold_robustness.csv",
        "day20_22_seed_robustness.csv",
        "day20_22_missingness_by_split.csv",
        "day20_22_missingness_performance.csv",
        "day20_22_leakage_integrity_checklist.csv",
        "day20_22_composite_validation_selection.csv",
        "day20_22_composite_sensitivity_performance.csv",
        "day20_22_composite_split_audit.csv",
        "day20_22_composite_validation_role_audit.csv",
        "day22_final_model_table.csv",
        "day22_final_error_table.csv",
        "day22_robustness_summary.csv",
        "figures/day20_22_weighted_error_tradeoff.svg",
        "figures/day20_22_threshold_robustness.svg",
        "day20_22_config_log.json",
        "day22_code_freeze_manifest.csv",
    ]
    config = {
        "status": "DAY20_22_ERROR_ROBUSTNESS_AND_INITIAL_CODE_FREEZE_COMPLETE",
        "seed": SEED,
        "runtime_versions": runtime_versions(),
        "model_lock": "Day 8-10 estimator hyperparameters, 12 constructs, HHX split, Raw/Platt choice, and validation-selected threshold preserved for MEDNG/MEDDL.",
        "error_analysis": "Aggregate false-negative/false-positive counts, rates, and eligible subgroup shares; no person-level output or micro-targeting.",
        "threshold_robustness": {
            "factors": list(THRESHOLD_FACTORS),
            "policy": "Prespecified perturbation around the locked threshold; no replacement threshold selected.",
        },
        "seed_robustness": {
            "seeds": list(ROBUSTNESS_SEEDS),
            "policy": "Ranges reported; no seed selected using test performance.",
        },
        "missingness_robustness": "Split-level feature missingness plus test evaluation strata; no complete-case refit.",
        "composite_sensitivity": {
            "definition": "TARGET_FORGONE_COST OR TARGET_DELAYED_COST on common valid-outcome cohort.",
            "n": EXPECTED_COMMON_N,
            "positive_n": EXPECTED_COMMON_POSITIVE_N,
            "hyperparameters": "Reuse MEDNG Day 8-10 hyperparameters; no composite tuning.",
            "calibration_threshold": "Day 8-10 validation-only protocol applied within composite sensitivity.",
            "status": "Separate sensitivity analysis; does not replace independent MEDNG/MEDDL primary reporting.",
        },
        "privacy": "Only aggregate tables, SVGs, and hashes are saved; no HHX/person-level prediction/probability is written.",
        "gate4": "PASS after validator confirms fairness plus Day 20-21 error/robustness outputs.",
        "day22_freeze": "Initial computational freeze through Day 22; later manuscript-only edits must not silently change locked analysis.",
        "outputs": outputs,
    }
    (args.out_dir / "day20_22_config_log.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    project_root = Path.cwd().resolve()
    freeze_paths = [
        Path("scripts/day8_10_modeling.py"),
        Path("scripts/day11_13_survey_sensitivity.py"),
        Path("scripts/day14_16_shap_explainability.py"),
        Path("scripts/validate_day14_16_outputs.py"),
        Path("scripts/day17_19_fairness_audit.py"),
        Path("scripts/day20_22_error_robustness_freeze.py"),
        Path("scripts/validate_day17_19_outputs.py"),
        Path("scripts/validate_day20_22_outputs.py"),
        Path("modeling/day8_10/day8_10_config_log.json"),
        Path("modeling/day8_10/day8_10_validation_selection.csv"),
        Path("modeling/day11_13/day11_13_config_log.json"),
        Path("modeling/day14_16/day14_16_config_log.json"),
        Path("modeling/day17_19/day17_19_config_log.json"),
        Path("modeling/day20_22/day20_22_config_log.json"),
    ]
    freeze_paths.extend(
        Path("modeling/day20_22") / relative
        for relative in outputs
        if relative not in {"day22_code_freeze_manifest.csv", "day20_22_config_log.json"}
    )
    freeze_rows = []
    for relative in freeze_paths:
        absolute = project_root / relative
        if not absolute.exists():
            raise FileNotFoundError(absolute)
        freeze_rows.append({
            "Relative_path": relative.as_posix(),
            "SHA256": sha256(absolute),
            "Size_bytes": absolute.stat().st_size,
            "Freeze_role": "Upstream lock" if "day20_22" not in relative.as_posix() else "Day20-22 code/output",
        })
    pd.DataFrame(freeze_rows).to_csv(
        args.out_dir / "day22_code_freeze_manifest.csv", index=False
    )

    print("\nSaved aggregate-only Day 20-22 outputs to", args.out_dir)
    print(f"Error summary rows: {len(error_summary)}; eligible group profiles: {len(error_profile)}")
    print(f"Threshold rows: {len(threshold_frame)}; seed rows: {len(seed_frame)}")
    print(f"Composite: N={EXPECTED_COMMON_N}, positive={EXPECTED_COMMON_POSITIVE_N}")
    print(f"Code freeze files: {len(freeze_rows)}")


if __name__ == "__main__":
    main()
