#!/usr/bin/env python3
"""NHIS 2024 Day 11-13 survey-aware predictive sensitivity analysis.

This script preserves every Day 8-10 model-development decision and adds:

* design-based population/outcome descriptions using WTFA_A, PSTRAT and PPSU;
* conventional versus WTFA_A-weighted training/evaluation sensitivity;
* stratified-PSU bootstrap intervals for weighted predictive performance;
* aggregate-only outputs suitable for review and reproducibility.

The analysis is deliberately not a new tuning cycle. Hyperparameters,
train/validation/test membership, probability version and operating thresholds
come from the locked Day 8-10 artifacts. PSTRAT/PPSU/WTFA_A are never predictors.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
    f1_score,
)

from day8_10_modeling import (
    MAIN,
    OUTCOMES,
    SEED,
    build_lr,
    build_rf,
    build_xgb,
    clean_features,
    day5_bucket,
    make_prep,
    validation_role,
)


METRICS = [
    "AUROC",
    "AUPRC",
    "Recall",
    "Precision",
    "F1",
    "Specificity",
    "Brier",
    "Observed_prevalence",
    "Mean_predicted_probability",
    "Predicted_positive_rate",
]

DESCRIPTIVE_DOMAINS = [
    "AGE_GROUP",
    "SEX_A",
    "HISPALLP_A",
    "RATCAT_A",
    "NOTCOV_A",
    "FDSCAT3_A",
    "DISAB3_A",
]


def normalize_training_weights(weights: np.ndarray) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    if not np.all(np.isfinite(weights)) or np.any(weights <= 0):
        raise ValueError("WTFA_A must be finite and strictly positive")
    return weights / np.mean(weights)


def weighted_specificity(y_true, y_pred, sample_weight) -> float:
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    w = np.asarray(sample_weight, dtype=float)
    negative = y_true == 0
    denom = float(np.sum(w[negative]))
    return float(np.sum(w[negative & (y_pred == 0)]) / denom) if denom else float("nan")


def evaluate(y_true, probs, threshold, sample_weight=None) -> dict:
    y_true = np.asarray(y_true, dtype=int)
    probs = np.asarray(probs, dtype=float)
    pred = (probs >= threshold).astype(int)
    w = np.ones(len(y_true), dtype=float) if sample_weight is None else np.asarray(sample_weight, dtype=float)
    return {
        "AUROC": float(roc_auc_score(y_true, probs, sample_weight=w)),
        "AUPRC": float(average_precision_score(y_true, probs, sample_weight=w)),
        "Recall": float(recall_score(y_true, pred, sample_weight=w, zero_division=0)),
        "Precision": float(precision_score(y_true, pred, sample_weight=w, zero_division=0)),
        "F1": float(f1_score(y_true, pred, sample_weight=w, zero_division=0)),
        "Specificity": weighted_specificity(y_true, pred, w),
        "Brier": float(brier_score_loss(y_true, probs, sample_weight=w)),
        "Observed_prevalence": float(np.average(y_true, weights=w)),
        "Mean_predicted_probability": float(np.average(probs, weights=w)),
        "Predicted_positive_rate": float(np.average(pred, weights=w)),
    }


class WeightedPlattScaler:
    """Platt scaling with optional validation sample weights."""

    def __init__(self):
        self.model = LogisticRegression(
            C=1e6, solver="lbfgs", max_iter=2000, random_state=SEED
        )

    @staticmethod
    def _logit(probs):
        probs = np.clip(np.asarray(probs, dtype=float), 1e-6, 1 - 1e-6)
        return np.log(probs / (1 - probs)).reshape(-1, 1)

    def fit(self, probs, y, sample_weight=None):
        self.model.fit(self._logit(probs), y, sample_weight=sample_weight)
        return self

    def transform(self, probs):
        return self.model.predict_proba(self._logit(probs))[:, 1]


def build_locked_model(model_name: str, params: dict, n_jobs: int):
    if model_name == "LR":
        return build_lr()
    if model_name == "RF":
        return build_rf(params, n_jobs)
    if model_name == "XGBoost":
        return build_xgb(params, n_jobs)
    raise ValueError(f"Unknown model {model_name}")


def validate_design(df: pd.DataFrame, outcome: str) -> dict:
    required = {"WTFA_A", "PSTRAT", "PPSU", "HHX"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError(f"{outcome}: missing survey fields {missing}")
    if df[list(required)].isna().any().any():
        raise RuntimeError(f"{outcome}: missing value in survey design fields")
    if not df["HHX"].is_unique:
        raise RuntimeError(f"{outcome}: HHX must be unique")

    psu_by_stratum = df.groupby("PSTRAT", observed=True)["PPSU"].nunique()
    w = df["WTFA_A"].to_numpy(dtype=float)
    return {
        "Outcome": outcome,
        "N": int(len(df)),
        "Strata_N": int(df["PSTRAT"].nunique()),
        "PSU_N": int(df[["PSTRAT", "PPSU"]].drop_duplicates().shape[0]),
        "Design_df": int(df[["PSTRAT", "PPSU"]].drop_duplicates().shape[0] - df["PSTRAT"].nunique()),
        "Min_PSU_per_stratum": int(psu_by_stratum.min()),
        "Max_PSU_per_stratum": int(psu_by_stratum.max()),
        "Lonely_strata_N": int((psu_by_stratum < 2).sum()),
        "Weight_sum": float(np.sum(w)),
        "Weight_mean": float(np.mean(w)),
        "Weight_min": float(np.min(w)),
        "Weight_max": float(np.max(w)),
        "Weight_CV": float(np.std(w, ddof=1) / np.mean(w)),
        "Kish_effective_N": float(np.sum(w) ** 2 / np.sum(w**2)),
    }


def taylor_ratio_mean(df: pd.DataFrame, outcome_col: str, domain=None) -> dict:
    """Taylor-linearized weighted binary mean with strata/PSU clustering.

    The domain form retains all PSUs and assigns zero linearized contribution to
    rows outside the domain, which is preferable to deleting non-domain rows.
    Finite-population corrections are not applied.
    """

    y = df[outcome_col].to_numpy(dtype=float)
    w = df["WTFA_A"].to_numpy(dtype=float)
    d = np.ones(len(df), dtype=float) if domain is None else np.asarray(domain, dtype=bool).astype(float)
    denom = float(np.sum(w * d))
    if denom <= 0:
        raise ValueError("Empty survey domain")
    estimate = float(np.sum(w * d * y) / denom)
    linearized = w * d * (y - estimate) / denom

    work = df[["PSTRAT", "PPSU"]].copy()
    work["linearized"] = linearized
    psu_totals = (
        work.groupby(["PSTRAT", "PPSU"], observed=True, as_index=False)["linearized"]
        .sum()
    )

    variance = 0.0
    strata_used = 0
    psu_count = 0
    for _, stratum in psu_totals.groupby("PSTRAT", observed=True):
        values = stratum["linearized"].to_numpy(dtype=float)
        m_h = len(values)
        if m_h < 2:
            continue
        strata_used += 1
        psu_count += m_h
        variance += float(m_h / (m_h - 1) * np.sum((values - np.mean(values)) ** 2))

    design_df = psu_count - strata_used
    se = math.sqrt(max(variance, 0.0))
    critical = float(student_t.ppf(0.975, design_df)) if design_df > 0 else 1.96
    lower = max(0.0, estimate - critical * se)
    upper = min(1.0, estimate + critical * se)
    unweighted = float(np.mean(y[d.astype(bool)]))
    n_domain = int(np.sum(d))
    srs_var = estimate * (1 - estimate) / n_domain if n_domain > 0 else float("nan")
    deff = variance / srs_var if srs_var > 0 else float("nan")
    domain_weights = w[d.astype(bool)]

    return {
        "Domain_N": n_domain,
        "Positive_N": int(np.sum(y[d.astype(bool)])),
        "Unweighted_prevalence": unweighted,
        "Weighted_prevalence": estimate,
        "Taylor_SE": se,
        "CI95_lower": lower,
        "CI95_upper": upper,
        "Design_df": int(design_df),
        "Approx_design_effect": float(deff),
        "Kish_effective_N": float(np.sum(domain_weights) ** 2 / np.sum(domain_weights**2)),
        "Weighted_population_total": float(denom),
    }


def add_age_group(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    age = pd.to_numeric(result["AGEP_A"], errors="coerce")
    result["AGE_GROUP"] = pd.cut(
        age,
        bins=[17, 34, 49, 64, 74, np.inf],
        labels=["18-34", "35-49", "50-64", "65-74", "75+"],
        right=True,
    ).astype("object")
    result["AGE_GROUP"] = result["AGE_GROUP"].where(result["AGE_GROUP"].notna(), "Missing")
    return result


def descriptive_rows(df: pd.DataFrame, outcome: str, target: str) -> tuple[list[dict], list[dict]]:
    overall = [{"Outcome": outcome, "Domain_variable": "Overall", "Domain_value": "All", **taylor_ratio_mean(df, target)}]
    subgroup = []
    work = add_age_group(df)
    for variable in DESCRIPTIVE_DOMAINS:
        series = work[variable].astype(str)
        for value in sorted(series.unique()):
            domain = series.eq(value).to_numpy()
            if int(domain.sum()) < 30:
                continue
            subgroup.append({
                "Outcome": outcome,
                "Domain_variable": variable,
                "Domain_value": value,
                **taylor_ratio_mean(work, target, domain=domain),
            })
    return overall, subgroup


def stratified_psu_bootstrap_multipliers(df_test: pd.DataFrame, reps: int, seed: int) -> np.ndarray:
    """Return replicate multipliers from PSU resampling within each stratum."""

    rng = np.random.default_rng(seed)
    n = len(df_test)
    multipliers = np.zeros((reps, n), dtype=np.int16)
    strata = df_test["PSTRAT"].to_numpy()
    psu = df_test["PPSU"].to_numpy()
    for stratum_value in np.unique(strata):
        stratum_mask = strata == stratum_value
        psus = np.unique(psu[stratum_mask])
        if len(psus) < 2:
            multipliers[:, stratum_mask] = 1
            continue
        sampled = rng.choice(psus, size=(reps, len(psus)), replace=True)
        for j, psu_value in enumerate(psus):
            counts = np.sum(sampled == psu_value, axis=1).astype(np.int16)
            multipliers[:, stratum_mask & (psu == psu_value)] = counts[:, None]
    return multipliers


def bootstrap_weighted_metrics(y, probs, base_weights, multipliers) -> dict[str, tuple[float, float, int]]:
    values = {metric: [] for metric in ("AUROC", "AUPRC", "Brier")}
    for multiplier in multipliers:
        replicate_weights = base_weights * multiplier
        if np.sum(replicate_weights[y == 1]) <= 0 or np.sum(replicate_weights[y == 0]) <= 0:
            continue
        values["AUROC"].append(roc_auc_score(y, probs, sample_weight=replicate_weights))
        values["AUPRC"].append(average_precision_score(y, probs, sample_weight=replicate_weights))
        values["Brier"].append(brier_score_loss(y, probs, sample_weight=replicate_weights))
    return {
        metric: (float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975)), len(v))
        for metric, v in values.items()
    }


def sensitivity_deltas(performance: pd.DataFrame) -> pd.DataFrame:
    rows = []
    index_cols = ["Outcome", "Model"]
    for keys, group in performance.groupby(index_cols, observed=True):
        keyed = group.set_index(["Training_weighting", "Evaluation_weighting"])
        comparisons = [
            ("Evaluation_weighting_effect", ("Unweighted", "WTFA_A"), ("Unweighted", "Unweighted")),
            ("Training_weighting_effect", ("WTFA_A", "WTFA_A"), ("Unweighted", "WTFA_A")),
            ("Combined_weighting_effect", ("WTFA_A", "WTFA_A"), ("Unweighted", "Unweighted")),
        ]
        for label, after_key, before_key in comparisons:
            after = keyed.loc[after_key]
            before = keyed.loc[before_key]
            for metric in METRICS:
                rows.append({
                    "Outcome": keys[0],
                    "Model": keys[1],
                    "Comparison": label,
                    "Metric": metric,
                    "Before": float(before[metric]),
                    "After": float(after[metric]),
                    "Absolute_delta": float(after[metric] - before[metric]),
                })
    return pd.DataFrame(rows)


def assert_locked_reproduction(performance: pd.DataFrame, locked_dir: Path) -> dict:
    """Verify that the conventional arm exactly reproduces Day 8-10."""

    locked_path = locked_dir / "day8_10_model_performance.csv"
    if not locked_path.exists():
        raise FileNotFoundError(locked_path)
    locked = pd.read_csv(locked_path).sort_values(["Outcome", "Model"]).reset_index(drop=True)
    reproduced = (
        performance[
            performance["Training_weighting"].eq("Unweighted")
            & performance["Evaluation_weighting"].eq("Unweighted")
        ]
        .sort_values(["Outcome", "Model"])
        .reset_index(drop=True)
    )
    if locked[["Outcome", "Model"]].to_dict("records") != reproduced[["Outcome", "Model"]].to_dict("records"):
        raise RuntimeError("Day 8-10 model/outcome rows do not align with the reproduced conventional arm")
    if not np.array_equal(
        locked["Selected_probability"].astype(str).to_numpy(),
        reproduced["Selected_probability"].astype(str).to_numpy(),
    ):
        raise RuntimeError("Locked probability-version drift detected")

    numeric_columns = ["Threshold", *METRICS]
    max_abs_diff = 0.0
    largest_differences = []
    for column in numeric_columns:
        reproduced_column = "Locked_threshold" if column == "Threshold" else column
        difference = np.abs(
            locked[column].to_numpy(dtype=float)
            - reproduced[reproduced_column].to_numpy(dtype=float)
        )
        max_abs_diff = max(max_abs_diff, float(np.max(difference)))
        for row_index, value in enumerate(difference):
            if value > 1e-12:
                largest_differences.append({
                    "Outcome": locked.loc[row_index, "Outcome"],
                    "Model": locked.loc[row_index, "Model"],
                    "Metric": column,
                    "Absolute_difference": float(value),
                })
    # XGBoost 3.0.4 can vary by a few 1e-9 across CPU builds while preserving
    # all decisions and displayed metrics.
    tolerance = 1e-8
    if max_abs_diff > tolerance:
        raise RuntimeError(
            f"Day 8-10 conventional-arm reproduction failed: max absolute difference "
            f"{max_abs_diff:.3g} exceeds {tolerance:.1g}; largest differences: "
            f"{sorted(largest_differences, key=lambda row: row['Absolute_difference'], reverse=True)[:8]}"
        )
    return {
        "status": "PASS",
        "rows_compared": int(len(locked)),
        "numeric_tolerance": tolerance,
        "max_absolute_difference": max_abs_diff,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--locked-dir", type=Path, default=Path("modeling/day8_10"))
    parser.add_argument("--out-dir", type=Path, default=Path("modeling/day11_13"))
    parser.add_argument("--bootstrap-reps", type=int, default=400)
    parser.add_argument("--n-jobs", type=int, default=-1)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    config_path = args.locked_dir / "day8_10_config_log.json"
    selection_path = args.locked_dir / "day8_10_validation_selection.csv"
    if not config_path.exists() or not selection_path.exists():
        raise FileNotFoundError("Locked Day 8-10 config/selection artifacts are required")
    locked_config = json.loads(config_path.read_text(encoding="utf-8"))
    locked_selection = pd.read_csv(selection_path).set_index(["Outcome", "Model"])

    design_rows = []
    overall_rows = []
    subgroup_rows = []
    performance_rows = []
    bootstrap_rows = []

    for outcome, spec in OUTCOMES.items():
        print(f"\n=== {outcome} ===")
        path = args.data_dir / spec["file"]
        if not path.exists():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        required = set(MAIN + ["HHX", "WTFA_A", "PSTRAT", "PPSU", spec["target"]])
        missing = sorted(required - set(df.columns))
        if missing:
            raise RuntimeError(f"{outcome}: missing columns {missing}")
        design_rows.append(validate_design(df, outcome))
        overall, subgroup = descriptive_rows(df, outcome, spec["target"])
        overall_rows.extend(overall)
        subgroup_rows.extend(subgroup)

        df["SPLIT"] = df["HHX"].map(day5_bucket)
        observed_split = {
            split: (int(mask.sum()), int(df.loc[mask, spec["target"]].sum()))
            for split in ("train", "validation", "test")
            for mask in [df["SPLIT"].eq(split)]
        }
        if observed_split != spec["expected"]:
            raise RuntimeError(f"{outcome}: split drift {observed_split} != {spec['expected']}")

        X = clean_features(df)
        y = df[spec["target"]].astype(int).to_numpy()
        weights = df["WTFA_A"].to_numpy(dtype=float)
        split = df["SPLIT"].to_numpy()
        tr, va, te = split == "train", split == "validation", split == "test"
        hhx = df["HHX"].to_numpy()
        val_roles = np.array([validation_role(value) for value in hhx[va]])
        calibration_mask = val_roles == "calibration"

        prep = make_prep()
        X_train = prep.fit_transform(X.loc[tr])
        X_validation = prep.transform(X.loc[va])
        X_test = prep.transform(X.loc[te])
        y_train, y_validation, y_test = y[tr], y[va], y[te]
        w_train, w_validation, w_test = weights[tr], weights[va], weights[te]

        test_design = df.loc[te, ["PSTRAT", "PPSU"]].reset_index(drop=True)
        bootstrap_multipliers = stratified_psu_bootstrap_multipliers(
            test_design, args.bootstrap_reps, seed=20261113 + (0 if outcome == "MEDNG" else 1)
        )

        best_params = locked_config["best_params"][outcome]
        for model_name in ("LR", "RF", "XGBoost"):
            selected = locked_selection.loc[(outcome, model_name)]
            selected_probability = str(selected["Selected_probability"])
            threshold = float(selected["Threshold"])

            params = best_params[model_name]
            if model_name == "LR":
                params = {"C": 1.0}

            for training_weighting in ("Unweighted", "WTFA_A"):
                model = build_locked_model(model_name, params, args.n_jobs)
                fit_kwargs = {}
                if training_weighting == "WTFA_A":
                    fit_kwargs["sample_weight"] = normalize_training_weights(w_train)
                model.fit(X_train, y_train, **fit_kwargs)

                p_validation_raw = model.predict_proba(X_validation[calibration_mask])[:, 1]
                p_test_raw = model.predict_proba(X_test)[:, 1]
                if selected_probability == "Platt":
                    calibration_weights = None
                    if training_weighting == "WTFA_A":
                        calibration_weights = normalize_training_weights(w_validation[calibration_mask])
                    platt = WeightedPlattScaler().fit(
                        p_validation_raw,
                        y_validation[calibration_mask],
                        sample_weight=calibration_weights,
                    )
                    p_test = platt.transform(p_test_raw)
                elif selected_probability == "Raw":
                    p_test = p_test_raw
                else:
                    raise RuntimeError(f"Unexpected probability version {selected_probability}")

                for evaluation_weighting, eval_weights in (
                    ("Unweighted", None),
                    ("WTFA_A", w_test),
                ):
                    performance_rows.append({
                        "Outcome": outcome,
                        "Model": model_name,
                        "Training_weighting": training_weighting,
                        "Evaluation_weighting": evaluation_weighting,
                        "Selected_probability": selected_probability,
                        "Locked_threshold": threshold,
                        **evaluate(y_test, p_test, threshold, sample_weight=eval_weights),
                    })

                ci = bootstrap_weighted_metrics(y_test, p_test, w_test, bootstrap_multipliers)
                weighted_point = evaluate(y_test, p_test, threshold, sample_weight=w_test)
                for metric in ("AUROC", "AUPRC", "Brier"):
                    lower, upper, valid_reps = ci[metric]
                    bootstrap_rows.append({
                        "Outcome": outcome,
                        "Model": model_name,
                        "Training_weighting": training_weighting,
                        "Evaluation_weighting": "WTFA_A",
                        "Metric": metric,
                        "Point_estimate": weighted_point[metric],
                        "CI95_lower": lower,
                        "CI95_upper": upper,
                        "Valid_replicates": valid_reps,
                        "Requested_replicates": args.bootstrap_reps,
                    })

    design_df = pd.DataFrame(design_rows)
    overall_df = pd.DataFrame(overall_rows)
    subgroup_df = pd.DataFrame(subgroup_rows)
    performance_df = pd.DataFrame(performance_rows)
    delta_df = sensitivity_deltas(performance_df)
    bootstrap_df = pd.DataFrame(bootstrap_rows)
    reproduction_audit = assert_locked_reproduction(performance_df, args.locked_dir)

    design_df.to_csv(args.out_dir / "day11_13_survey_design_audit.csv", index=False)
    overall_df.to_csv(args.out_dir / "day11_13_weighted_outcome_prevalence.csv", index=False)
    subgroup_df.to_csv(args.out_dir / "day11_13_weighted_subgroup_prevalence.csv", index=False)
    performance_df.to_csv(args.out_dir / "day11_13_weighted_model_sensitivity.csv", index=False)
    delta_df.to_csv(args.out_dir / "day11_13_weighted_model_sensitivity_deltas.csv", index=False)
    bootstrap_df.to_csv(args.out_dir / "day11_13_weighted_performance_cluster_bootstrap_ci.csv", index=False)

    output_config = {
        "status": "DAY11_13_SURVEY_AWARE_SENSITIVITY_COMPLETE",
        "seed": SEED,
        "runtime_versions": {
            package: importlib.metadata.version(package)
            for package in ("numpy", "pandas", "scipy", "scikit-learn", "xgboost")
        },
        "features": MAIN,
        "model_lock": "Day 8-10 hyperparameters, HHX split, probability version and operating threshold preserved; no search or reselection.",
        "training_weighting": "WTFA_A normalized to mean 1 within training data; unweighted and weighted fits use identical preprocessing and locked hyperparameters.",
        "evaluation_weighting": "Metrics reported both unweighted and with raw WTFA_A test weights.",
        "population_description": "WTFA_A point estimates with Taylor-linearized variance using PSTRAT and PPSU; no finite-population correction.",
        "performance_uncertainty": {
            "method": "stratified PSU resampling within PSTRAT on the locked test set, retaining WTFA_A",
            "reps": args.bootstrap_reps,
            "metrics": ["AUROC", "AUPRC", "Brier"],
            "status": "survey-aware sensitivity interval; not an official NCHS replicate-weight variance estimate",
        },
        "interpretation": "Contemporaneous predictive sensitivity for self-reported past-12-month outcomes; not causal inference, future forecasting, or deployment validation.",
        "test_policy": "Aggregate test sensitivity only. Results must not trigger new tuning, calibration, threshold selection, feature changes, or a winner claim.",
        "locked_reproduction_audit": reproduction_audit,
        "privacy": "No person-level predictions are written or committed.",
        "outputs": [
            "day11_13_survey_design_audit.csv",
            "day11_13_weighted_outcome_prevalence.csv",
            "day11_13_weighted_subgroup_prevalence.csv",
            "day11_13_weighted_model_sensitivity.csv",
            "day11_13_weighted_model_sensitivity_deltas.csv",
            "day11_13_weighted_performance_cluster_bootstrap_ci.csv",
            "day11_13_config_log.json",
        ],
    }
    (args.out_dir / "day11_13_config_log.json").write_text(
        json.dumps(output_config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n=== DESIGN-BASED OUTCOME PREVALENCE ===")
    print(overall_df[["Outcome", "Domain_N", "Unweighted_prevalence", "Weighted_prevalence", "CI95_lower", "CI95_upper"]].to_string(index=False))
    print("\n=== MATCHED WEIGHTED SENSITIVITY (weighted train + weighted evaluation) ===")
    matched = performance_df[
        performance_df["Training_weighting"].eq("WTFA_A")
        & performance_df["Evaluation_weighting"].eq("WTFA_A")
    ]
    print(matched[["Outcome", "Model", "AUROC", "AUPRC", "Recall", "Precision", "F1", "Specificity", "Brier"]].to_string(index=False))
    print(f"\nSaved aggregate outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
