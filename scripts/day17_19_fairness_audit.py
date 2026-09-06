#!/usr/bin/env python3
"""NHIS 2024 Day 17-19 locked-test subgroup fairness and error audit.

This script is deliberately evaluation-only. It reconstructs the unweighted
Day 8-10 LR/RF/XGBoost models, applies the locked probability version and
validation-selected operating threshold, and evaluates prespecified equity
subgroups on the unchanged test split. Survey-weighted estimates and
unweighted sensitivity estimates are reported in parallel.

Fairness boundaries
-------------------
* A performance gap is descriptive evidence for review, not proof of
  discrimination, causation, or deployability.
* Equal-opportunity information is reported as the unsigned between-group TPR
  span. FPR is reported separately; no single equalized-odds verdict is made.
* Threshold-dependent results use the locked validation operating point. It is
  not a clinical cutoff and is never re-optimized within a subgroup.
* Groups with N < 100, fewer than 20 positives, or fewer than 20 negatives are
  excluded from comparative performance summaries and recorded explicitly.
* Only aggregate tables and figures are written; no HHX or person-level
  prediction leaves memory.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from day8_10_modeling import (
    MAIN,
    OUTCOMES,
    SEED,
    PlattScaler,
    assert_day5_split,
    build_lr,
    build_rf,
    build_xgb,
    clean_features,
    day5_bucket,
    evaluate as locked_evaluate,
    make_prep,
    validation_role,
)
from day11_13_survey_sensitivity import stratified_psu_bootstrap_multipliers


MODELS = ("LR", "RF", "XGBoost")
EVALUATION_WEIGHTINGS = ("Unweighted", "WTFA_A")
MIN_GROUP_N = 100
MIN_POSITIVE_N = 20
MIN_NEGATIVE_N = 20
AUDIT_TOLERANCE = 1e-8
CI_METRICS = ("AUROC", "AUPRC", "Recall", "FNR", "FPR", "Brier", "Calibration_abs_error")
GAP_METRICS = ("AUPRC", "AUROC", "Recall", "FNR", "FPR", "Brier", "Calibration_abs_error")


AXES = {
    "Race_ethnicity": {
        "source": "HISPALLP_A",
        "domain": "Race/ethnicity",
        "primary": True,
        "order": [
            "Hispanic", "NH White", "NH Black", "NH Asian", "NH AIAN",
            "NH AIAN + other", "Other/multiple",
        ],
    },
    "Poverty": {
        "source": "RATCAT_A",
        "domain": "Income/poverty",
        "primary": True,
        "order": ["<100% FPL", "100-199% FPL", ">=200% FPL", "Missing/special"],
    },
    "Insurance": {
        "source": "NOTCOV_A",
        "domain": "Insurance",
        "primary": True,
        "order": ["Uninsured", "Insured", "Missing/special"],
    },
    "Sex": {
        "source": "SEX_A",
        "domain": "Demographic (sex/age)",
        "primary": True,
        "order": ["Male", "Female", "Missing/special"],
    },
    "Age": {
        "source": "AGEP_A",
        "domain": "Demographic (sex/age)",
        "primary": True,
        "order": ["18-34", "35-49", "50-64", "65-74", "75+", "Missing/special"],
    },
}


def build_locked_model(model_name: str, params: dict, n_jobs: int):
    if model_name == "LR":
        return build_lr()
    if model_name == "RF":
        return build_rf(params, n_jobs)
    if model_name == "XGBoost":
        return build_xgb(params, n_jobs)
    raise ValueError(f"Unknown model: {model_name}")


def subgroup_labels(frame: pd.DataFrame, axis: str) -> pd.Series:
    if axis == "Race_ethnicity":
        mapping = {
            1: "Hispanic", 2: "NH White", 3: "NH Black", 4: "NH Asian",
            5: "NH AIAN", 6: "NH AIAN + other", 7: "Other/multiple",
        }
        numeric = pd.to_numeric(frame["HISPALLP_A"], errors="coerce")
        return numeric.map(mapping).fillna("Missing/special")
    if axis == "Poverty":
        numeric = pd.to_numeric(frame["RATCAT_A"], errors="coerce")
        labels = pd.Series("Missing/special", index=frame.index, dtype=object)
        labels.loc[numeric.isin([1, 2, 3])] = "<100% FPL"
        labels.loc[numeric.isin([4, 5, 6, 7])] = "100-199% FPL"
        labels.loc[numeric.between(8, 14, inclusive="both")] = ">=200% FPL"
        return labels
    if axis == "Insurance":
        numeric = pd.to_numeric(frame["NOTCOV_A"], errors="coerce")
        return numeric.map({1: "Uninsured", 2: "Insured"}).fillna("Missing/special")
    if axis == "Sex":
        numeric = pd.to_numeric(frame["SEX_A"], errors="coerce")
        return numeric.map({1: "Male", 2: "Female"}).fillna("Missing/special")
    if axis == "Age":
        numeric = pd.to_numeric(frame["AGEP_A"], errors="coerce")
        numeric = numeric.mask(numeric.isin([97, 98, 99]))
        labels = pd.cut(
            numeric,
            bins=[17, 34, 49, 64, 74, math.inf],
            labels=["18-34", "35-49", "50-64", "65-74", "75+"],
            right=True,
        ).astype(object)
        return pd.Series(labels, index=frame.index).fillna("Missing/special")
    raise ValueError(f"Unknown axis: {axis}")


def eligibility(n: int, positive_n: int, negative_n: int) -> tuple[bool, str]:
    reasons = []
    if n < MIN_GROUP_N:
        reasons.append(f"N < {MIN_GROUP_N}")
    if positive_n < MIN_POSITIVE_N:
        reasons.append(f"positive N < {MIN_POSITIVE_N}")
    if negative_n < MIN_NEGATIVE_N:
        reasons.append(f"negative N < {MIN_NEGATIVE_N}")
    return not reasons, "; ".join(reasons)


def calibration_fit(y: np.ndarray, probs: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    clipped = np.clip(np.asarray(probs, dtype=float), 1e-6, 1 - 1e-6)
    logit = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    try:
        model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=2000, random_state=SEED)
        model.fit(logit, y, sample_weight=weights)
        return float(model.intercept_[0]), float(model.coef_[0, 0])
    except Exception:
        return float("nan"), float("nan")


def expected_calibration_error(
    y: np.ndarray, probs: np.ndarray, weights: np.ndarray, n_bins: int = 5
) -> float:
    edges = np.unique(np.quantile(probs, np.linspace(0, 1, n_bins + 1)))
    if len(edges) < 3:
        return float("nan")
    bins = np.digitize(probs, edges[1:-1], right=True)
    total = float(np.sum(weights))
    value = 0.0
    for b in range(len(edges) - 1):
        mask = bins == b
        if not np.any(mask):
            continue
        bin_weight = float(np.sum(weights[mask]))
        observed = float(np.average(y[mask], weights=weights[mask]))
        predicted = float(np.average(probs[mask], weights=weights[mask]))
        value += bin_weight / total * abs(observed - predicted)
    return float(value)


def subgroup_metrics(
    y: np.ndarray, probs: np.ndarray, threshold: float, weights: np.ndarray
) -> dict:
    y = np.asarray(y, dtype=int)
    probs = np.asarray(probs, dtype=float)
    weights = np.asarray(weights, dtype=float)
    pred = (probs >= threshold).astype(int)
    positive = y == 1
    negative = ~positive
    positive_weight = float(np.sum(weights[positive]))
    negative_weight = float(np.sum(weights[negative]))
    tp = float(np.sum(weights[positive & (pred == 1)]))
    fn = float(np.sum(weights[positive & (pred == 0)]))
    fp = float(np.sum(weights[negative & (pred == 1)]))
    tn = float(np.sum(weights[negative & (pred == 0)]))
    recall = tp / positive_weight if positive_weight else float("nan")
    fnr = fn / positive_weight if positive_weight else float("nan")
    fpr = fp / negative_weight if negative_weight else float("nan")
    specificity = tn / negative_weight if negative_weight else float("nan")
    precision = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    prevalence = float(np.average(y, weights=weights))
    mean_probability = float(np.average(probs, weights=weights))
    intercept, slope = calibration_fit(y, probs, weights)
    return {
        "Weighted_denominator": float(np.sum(weights)),
        "Observed_prevalence": prevalence,
        "Mean_predicted_probability": mean_probability,
        "Calibration_signed_error": mean_probability - prevalence,
        "Calibration_abs_error": abs(mean_probability - prevalence),
        "Calibration_intercept": intercept,
        "Calibration_slope": slope,
        "ECE_5bin": expected_calibration_error(y, probs, weights),
        "Predicted_positive_rate": float(np.average(pred, weights=weights)),
        "AUROC": float(roc_auc_score(y, probs, sample_weight=weights)),
        "AUPRC": float(average_precision_score(y, probs, sample_weight=weights)),
        "Recall": recall,
        "FNR": fnr,
        "FPR": fpr,
        "Specificity": specificity,
        "Precision": precision,
        "F1": f1,
        "Brier": float(brier_score_loss(y, probs, sample_weight=weights)),
    }


def fast_bootstrap_metrics(
    y: np.ndarray,
    probs: np.ndarray,
    threshold: float,
    base_weights: np.ndarray,
    multipliers: np.ndarray,
) -> dict[str, np.ndarray]:
    result = {metric: np.full(len(multipliers), np.nan, dtype=float) for metric in CI_METRICS}
    pred = probs >= threshold
    for index, multiplier in enumerate(multipliers):
        weights = base_weights * multiplier
        positive = y == 1
        negative = ~positive
        positive_weight = float(np.sum(weights[positive]))
        negative_weight = float(np.sum(weights[negative]))
        if positive_weight <= 0 or negative_weight <= 0:
            continue
        tp = float(np.sum(weights[positive & pred]))
        fn = float(np.sum(weights[positive & ~pred]))
        fp = float(np.sum(weights[negative & pred]))
        result["Recall"][index] = tp / positive_weight
        result["FNR"][index] = fn / positive_weight
        result["FPR"][index] = fp / negative_weight
        try:
            result["AUROC"][index] = roc_auc_score(y, probs, sample_weight=weights)
            result["AUPRC"][index] = average_precision_score(y, probs, sample_weight=weights)
            result["Brier"][index] = brier_score_loss(y, probs, sample_weight=weights)
            result["Calibration_abs_error"][index] = abs(
                float(np.average(probs, weights=weights)) - float(np.average(y, weights=weights))
            )
        except ValueError:
            continue
    return result


def ci_row(metadata: dict, metric: str, point: float, values: np.ndarray, reps: int) -> dict:
    valid = values[np.isfinite(values)]
    if len(valid) == 0:
        lower = upper = float("nan")
    else:
        lower, upper = np.quantile(valid, [0.025, 0.975])
    return {
        **metadata,
        "Metric": metric,
        "Point_estimate": point,
        "CI95_lower": float(lower),
        "CI95_upper": float(upper),
        "Valid_replicates": int(len(valid)),
        "Requested_replicates": int(reps),
    }


def append_disparity_rows(
    rows: list[dict],
    ci_rows: list[dict],
    base: dict,
    point_rows: list[dict],
    replicate_values: dict[str, dict[str, np.ndarray]],
    reps: int,
) -> None:
    if len(point_rows) < 2:
        rows.append({
            **base,
            "Metric": "Not_estimable",
            "Minimum_group": "",
            "Minimum": float("nan"),
            "Maximum_group": "",
            "Maximum": float("nan"),
            "Max_minus_min": float("nan"),
            "Eligible_groups_N": len(point_rows),
            "Interpretation": "Fewer than two eligible groups",
        })
        return
    points = pd.DataFrame(point_rows).set_index("Group")
    for metric in GAP_METRICS:
        minimum_group = str(points[metric].idxmin())
        maximum_group = str(points[metric].idxmax())
        minimum = float(points.loc[minimum_group, metric])
        maximum = float(points.loc[maximum_group, metric])
        gap = maximum - minimum
        label = (
            "Unsigned equal-opportunity TPR span at locked threshold"
            if metric == "Recall"
            else "Descriptive between-group max-minus-min span"
        )
        row = {
            **base,
            "Metric": metric,
            "Minimum_group": minimum_group,
            "Minimum": minimum,
            "Maximum_group": maximum_group,
            "Maximum": maximum,
            "Max_minus_min": gap,
            "Eligible_groups_N": len(point_rows),
            "Interpretation": label,
        }
        rows.append(row)
        matrix = np.vstack([replicate_values[group][metric] for group in points.index])
        valid_by_rep = np.sum(np.isfinite(matrix), axis=0) == len(points.index)
        spans = np.full(reps, np.nan, dtype=float)
        spans[valid_by_rep] = np.nanmax(matrix[:, valid_by_rep], axis=0) - np.nanmin(
            matrix[:, valid_by_rep], axis=0
        )
        ci_rows.append(ci_row(base, metric, gap, spans, reps))


def audit_reproduction(
    reproduced_rows: list[dict], locked_dir: Path, day11_dir: Path
) -> pd.DataFrame:
    reproduced = pd.DataFrame(reproduced_rows).set_index(["Outcome", "Model", "Evaluation_weighting"])
    locked_day8 = pd.read_csv(locked_dir / "day8_10_model_performance.csv").set_index(["Outcome", "Model"])
    day11 = pd.read_csv(day11_dir / "day11_13_weighted_model_sensitivity.csv")
    day11 = day11[
        day11["Training_weighting"].eq("Unweighted")
        & day11["Evaluation_weighting"].eq("WTFA_A")
    ].set_index(["Outcome", "Model"])
    rows = []
    metrics = ["AUROC", "AUPRC", "Recall", "Precision", "F1", "Specificity", "Brier"]
    for outcome in OUTCOMES:
        for model in MODELS:
            for weighting in EVALUATION_WEIGHTINGS:
                reference = locked_day8.loc[(outcome, model)] if weighting == "Unweighted" else day11.loc[(outcome, model)]
                observed = reproduced.loc[(outcome, model, weighting)]
                diffs = {metric: abs(float(reference[metric]) - float(observed[metric])) for metric in metrics}
                maximum = max(diffs.values())
                rows.append({
                    "Outcome": outcome,
                    "Model": model,
                    "Evaluation_weighting": weighting,
                    "Reference": "Day8_10" if weighting == "Unweighted" else "Day11_13_unweighted_training",
                    "Status": "PASS" if maximum <= AUDIT_TOLERANCE else "FAIL",
                    "Max_absolute_metric_difference": maximum,
                    "Tolerance": AUDIT_TOLERANCE,
                    **{f"Abs_diff_{metric}": value for metric, value in diffs.items()},
                })
    frame = pd.DataFrame(rows)
    if not frame["Status"].eq("PASS").all():
        failed = frame.loc[frame["Status"].ne("PASS"), ["Outcome", "Model", "Evaluation_weighting"]]
        raise RuntimeError(f"Locked reproduction failed:\n{failed.to_string(index=False)}")
    return frame


def plot_gap_heatmap(disparity: pd.DataFrame, outcome: str, output_path: Path) -> None:
    selected = disparity[
        disparity["Outcome"].eq(outcome)
        & disparity["Evaluation_weighting"].eq("WTFA_A")
        & disparity["Metric"].isin(["FNR", "FPR"])
    ].copy()
    axis_display = {"Race_ethnicity": "Race/ethnicity"}
    selected["Row"] = selected["Axis"].replace(axis_display) + " / " + selected["Metric"]
    table = selected.pivot(index="Row", columns="Model", values="Max_minus_min")
    wanted_rows = [
        f"{axis_display.get(axis, axis)} / {metric}"
        for axis in AXES
        for metric in ("FNR", "FPR")
    ]
    table = table.reindex(index=wanted_rows, columns=list(MODELS))
    values = table.to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(8.4, 6.7))
    image = ax.imshow(values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=max(0.35, np.nanmax(values)))
    ax.set_xticks(range(len(table.columns)), labels=table.columns)
    ax.set_yticks(range(len(table.index)), labels=table.index)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            label = "NA" if not np.isfinite(values[i, j]) else f"{values[i, j]:.3f}"
            ax.text(j, i, label, ha="center", va="center", fontsize=8)
    ax.set_title(f"{outcome}: WTFA_A-weighted subgroup error-rate spans\nlocked test / locked validation threshold")
    cbar = fig.colorbar(image, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("max − min across eligible groups")
    fig.tight_layout()
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def plot_calibration_error(subgroups: pd.DataFrame, outcome: str, output_path: Path) -> None:
    selected = subgroups[
        subgroups["Outcome"].eq(outcome)
        & subgroups["Evaluation_weighting"].eq("WTFA_A")
        & subgroups["Eligible_for_comparison"]
    ].copy()
    fig, axes = plt.subplots(1, len(MODELS), figsize=(13.5, 5.4), sharey=True)
    colors = dict(zip(AXES, plt.cm.tab10.colors[: len(AXES)]))
    for ax, model in zip(axes, MODELS):
        current = selected[selected["Model"].eq(model)]
        for axis in AXES:
            part = current[current["Axis"].eq(axis)]
            ax.scatter(
                part["Observed_prevalence"], part["Mean_predicted_probability"],
                s=35, alpha=0.8, label=axis, color=colors[axis],
            )
        upper = max(0.35, float(current[["Observed_prevalence", "Mean_predicted_probability"]].max().max()) * 1.05)
        ax.plot([0, upper], [0, upper], linestyle="--", color="black", linewidth=1)
        ax.set_xlim(0, upper)
        ax.set_ylim(0, upper)
        ax.set_title(model)
        ax.set_xlabel("Observed prevalence")
    axes[0].set_ylabel("Mean predicted probability")
    axes[-1].legend(title="Axis", fontsize=8, loc="lower right")
    fig.suptitle(f"{outcome}: subgroup calibration-in-the-large\nWTFA_A / locked test / locked probability version")
    fig.tight_layout()
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def runtime_versions() -> dict:
    return {
        package: importlib.metadata.version(package)
        for package in ("numpy", "pandas", "scipy", "scikit-learn", "xgboost", "matplotlib")
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--locked-dir", type=Path, default=Path("modeling/day8_10"))
    parser.add_argument("--day11-dir", type=Path, default=Path("modeling/day11_13"))
    parser.add_argument("--out-dir", type=Path, default=Path("modeling/day17_19"))
    parser.add_argument("--n-jobs", type=int, default=2)
    parser.add_argument("--bootstrap-reps", type=int, default=400)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = args.out_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    config_path = args.locked_dir / "day8_10_config_log.json"
    selection_path = args.locked_dir / "day8_10_validation_selection.csv"
    for path in (config_path, selection_path):
        if not path.exists():
            raise FileNotFoundError(path)
    locked_config = json.loads(config_path.read_text(encoding="utf-8"))
    locked_selection = pd.read_csv(selection_path).set_index(["Outcome", "Model"])

    subgroup_rows: list[dict] = []
    skipped_rows: list[dict] = []
    ci_rows: list[dict] = []
    disparity_rows: list[dict] = []
    disparity_ci_rows: list[dict] = []
    reproduced_rows: list[dict] = []
    split_rows: list[dict] = []

    for outcome_index, (outcome, spec) in enumerate(OUTCOMES.items()):
        print(f"\n=== {outcome}: locked-test fairness audit ===", flush=True)
        frame = pd.read_csv(args.data_dir / spec["file"])
        required = set(MAIN + ["HHX", "WTFA_A", "PSTRAT", "PPSU", spec["target"]])
        missing = sorted(required - set(frame.columns))
        if missing:
            raise RuntimeError(f"{outcome}: missing columns {missing}")
        if not frame["HHX"].is_unique:
            raise RuntimeError(f"{outcome}: HHX must be unique")
        if frame[["WTFA_A", "PSTRAT", "PPSU"]].isna().any().any():
            raise RuntimeError(f"{outcome}: missing survey design values")
        if (frame["WTFA_A"] <= 0).any():
            raise RuntimeError(f"{outcome}: non-positive WTFA_A")
        frame["SPLIT"] = frame["HHX"].map(day5_bucket)
        split_rows.extend(assert_day5_split(frame, outcome, spec["target"]))

        clean = clean_features(frame)
        target = frame[spec["target"]].astype(int).to_numpy()
        split = frame["SPLIT"].to_numpy()
        train_mask, validation_mask, test_mask = split == "train", split == "validation", split == "test"
        validation_roles = np.array([validation_role(value) for value in frame.loc[validation_mask, "HHX"]])
        calibration_mask = validation_roles == "calibration"

        prep = make_prep()
        x_train = prep.fit_transform(clean.loc[train_mask])
        x_validation = prep.transform(clean.loc[validation_mask])
        x_test = prep.transform(clean.loc[test_mask])
        y_train = target[train_mask]
        y_validation = target[validation_mask]
        y_test = target[test_mask]
        test_frame = frame.loc[test_mask].reset_index(drop=True)
        test_weights = test_frame["WTFA_A"].to_numpy(dtype=float)
        multipliers = stratified_psu_bootstrap_multipliers(
            test_frame, args.bootstrap_reps, SEED + 1000 * outcome_index + 917
        )

        for model_name in MODELS:
            print(f"  {model_name}: reconstruct, verify, stratify...", flush=True)
            selected = locked_selection.loc[(outcome, model_name)]
            params = locked_config["best_params"][outcome][model_name]
            if model_name == "LR":
                params = {"C": 1.0}
            model = build_locked_model(model_name, params, args.n_jobs)
            model.fit(x_train, y_train)
            raw_validation = model.predict_proba(x_validation[calibration_mask])[:, 1]
            raw_test = model.predict_proba(x_test)[:, 1]
            if str(selected["Selected_probability"]) == "Platt":
                platt = PlattScaler().fit(raw_validation, y_validation[calibration_mask])
                probs = platt.transform(raw_test)
            else:
                probs = raw_test
            threshold = float(selected["Threshold"])

            for weighting in EVALUATION_WEIGHTINGS:
                weights = np.ones(len(y_test), dtype=float) if weighting == "Unweighted" else test_weights
                overall_metrics = (
                    locked_evaluate(y_test, probs, threshold)
                    if weighting == "Unweighted"
                    else subgroup_metrics(y_test, probs, threshold, weights)
                )
                reproduced_rows.append({
                    "Outcome": outcome,
                    "Model": model_name,
                    "Evaluation_weighting": weighting,
                    **overall_metrics,
                })

            for axis, axis_spec in AXES.items():
                labels = subgroup_labels(test_frame, axis).to_numpy(dtype=object)
                group_order = [group for group in axis_spec["order"] if np.any(labels == group)]
                point_by_weighting = {weighting: [] for weighting in EVALUATION_WEIGHTINGS}
                replicates_by_weighting = {weighting: {} for weighting in EVALUATION_WEIGHTINGS}
                for order, group in enumerate(group_order, start=1):
                    mask = labels == group
                    n = int(np.sum(mask))
                    positive_n = int(np.sum(y_test[mask]))
                    negative_n = n - positive_n
                    eligible, reason = eligibility(n, positive_n, negative_n)
                    metadata = {
                        "Outcome": outcome,
                        "Model": model_name,
                        "Selected_probability": str(selected["Selected_probability"]),
                        "Locked_threshold": threshold,
                        "Split": "locked_test",
                        "Equity_domain": axis_spec["domain"],
                        "Axis": axis,
                        "Group": group,
                        "Group_order": order,
                        "N": n,
                        "Positive_N": positive_n,
                        "Negative_N": negative_n,
                        "Eligible_for_comparison": eligible,
                        "Exclusion_reason": reason,
                    }
                    if not eligible:
                        skipped_rows.append(metadata)
                        continue
                    for weighting in EVALUATION_WEIGHTINGS:
                        base_weights = np.ones(n, dtype=float) if weighting == "Unweighted" else test_weights[mask]
                        metrics = subgroup_metrics(y_test[mask], probs[mask], threshold, base_weights)
                        row = {**metadata, "Evaluation_weighting": weighting, **metrics}
                        subgroup_rows.append(row)
                        point_by_weighting[weighting].append(row)
                        replicate_values = fast_bootstrap_metrics(
                            y_test[mask], probs[mask], threshold, base_weights, multipliers[:, mask]
                        )
                        replicates_by_weighting[weighting][group] = replicate_values
                        ci_metadata = {
                            "Outcome": outcome,
                            "Model": model_name,
                            "Evaluation_weighting": weighting,
                            "Axis": axis,
                            "Group": group,
                        }
                        for metric in CI_METRICS:
                            ci_rows.append(ci_row(
                                ci_metadata, metric, float(metrics[metric]), replicate_values[metric], args.bootstrap_reps
                            ))
                for weighting in EVALUATION_WEIGHTINGS:
                    append_disparity_rows(
                        disparity_rows,
                        disparity_ci_rows,
                        {"Outcome": outcome, "Model": model_name, "Evaluation_weighting": weighting, "Axis": axis},
                        point_by_weighting[weighting],
                        replicates_by_weighting[weighting],
                        args.bootstrap_reps,
                    )

    subgroup_frame = pd.DataFrame(subgroup_rows)
    skipped_frame = pd.DataFrame(skipped_rows).drop_duplicates(
        subset=["Outcome", "Model", "Axis", "Group"]
    )
    ci_frame = pd.DataFrame(ci_rows)
    disparity_frame = pd.DataFrame(disparity_rows)
    disparity_ci_frame = pd.DataFrame(disparity_ci_rows)
    reproduction_frame = audit_reproduction(reproduced_rows, args.locked_dir, args.day11_dir)
    split_frame = pd.DataFrame(split_rows)

    subgroup_frame.to_csv(args.out_dir / "day17_19_subgroup_performance.csv", index=False)
    skipped_frame.to_csv(args.out_dir / "day17_19_subgroup_skipped.csv", index=False)
    ci_frame.to_csv(args.out_dir / "day17_19_subgroup_metric_cluster_bootstrap_ci.csv", index=False)
    disparity_frame.to_csv(args.out_dir / "day17_19_disparity_summary.csv", index=False)
    disparity_ci_frame.to_csv(args.out_dir / "day17_19_disparity_cluster_bootstrap_ci.csv", index=False)
    reproduction_frame.to_csv(args.out_dir / "day17_19_locked_reproduction_audit.csv", index=False)
    split_frame.to_csv(args.out_dir / "day17_19_split_audit.csv", index=False)

    for outcome in OUTCOMES:
        plot_gap_heatmap(
            disparity_frame, outcome, figure_dir / f"fairness_error_gap_{outcome}.svg"
        )
        plot_calibration_error(
            subgroup_frame, outcome, figure_dir / f"fairness_calibration_{outcome}.svg"
        )

    config = {
        "status": "DAY17_19_FAIRNESS_ERROR_AUDIT_COMPLETE",
        "seed": SEED,
        "runtime_versions": runtime_versions(),
        "outcomes": list(OUTCOMES),
        "models": list(MODELS),
        "features": MAIN,
        "model_lock": "Day 8-10 unweighted estimator, HHX split, probability version, calibration fit role, and validation-selected threshold preserved; no tuning or reselection.",
        "equity_domains": {
            "Race/ethnicity": ["Race_ethnicity"],
            "Income/poverty": ["Poverty"],
            "Insurance": ["Insurance"],
            "Demographic (sex/age)": ["Sex", "Age"],
        },
        "evaluation_weighting": ["Unweighted sensitivity", "WTFA_A-weighted primary population-relevant estimate"],
        "uncertainty": {
            "method": f"{args.bootstrap_reps}-replicate stratified PSU bootstrap within PSTRAT on locked test, retaining WTFA_A for weighted estimates",
            "requested_replicates": args.bootstrap_reps,
            "status": "survey-aware sensitivity interval; not an official NCHS replicate-weight variance estimate",
        },
        "eligibility": {
            "minimum_group_n": MIN_GROUP_N,
            "minimum_positive_n": MIN_POSITIVE_N,
            "minimum_negative_n": MIN_NEGATIVE_N,
            "policy": "Ineligible levels are recorded and omitted from comparative gap calculation; no pooling after outcome review.",
        },
        "metrics": {
            "discrimination": ["AUPRC (primary)", "AUROC (complementary)"],
            "errors_at_locked_threshold": ["Recall/TPR", "FNR", "FPR", "Specificity", "Precision", "F1"],
            "calibration": ["Brier", "calibration-in-the-large error", "calibration intercept/slope", "5-bin ECE"],
            "fairness_gap": "Unsigned max-minus-min spans across eligible groups. Recall span is the descriptive equal-opportunity TPR span; FPR is separate.",
        },
        "locked_reproduction": {
            "status": "PASS",
            "rows_compared": int(len(reproduction_frame)),
            "max_absolute_metric_difference": float(reproduction_frame["Max_absolute_metric_difference"].max()),
            "tolerance": AUDIT_TOLERANCE,
        },
        "interpretation_lock": "A subgroup metric gap is not by itself proof of discrimination, causation, or clinical harm. Different outcome prevalence, sampling variability, and measurement context must be considered with UHS.",
        "threshold_lock": "Threshold is the validation F1 operating point and not a clinical cutoff. It is not changed by subgroup.",
        "privacy": "Only aggregate tables and figures are saved; no HHX or person-level prediction is written.",
        "outputs": [
            "day17_19_subgroup_performance.csv",
            "day17_19_subgroup_skipped.csv",
            "day17_19_subgroup_metric_cluster_bootstrap_ci.csv",
            "day17_19_disparity_summary.csv",
            "day17_19_disparity_cluster_bootstrap_ci.csv",
            "day17_19_locked_reproduction_audit.csv",
            "day17_19_split_audit.csv",
            "figures/*.svg",
            "day17_19_config_log.json",
        ],
    }
    (args.out_dir / "day17_19_config_log.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    weighted_gaps = disparity_frame[
        disparity_frame["Evaluation_weighting"].eq("WTFA_A")
        & disparity_frame["Metric"].isin(["Recall", "FPR", "AUPRC", "Brier"])
    ]
    print("\n=== WTFA_A-WEIGHTED DESCRIPTIVE GAP SUMMARY ===")
    print(weighted_gaps[["Outcome", "Model", "Axis", "Metric", "Max_minus_min", "Eligible_groups_N"]].to_string(index=False))
    print(f"\nSaved aggregate-only outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
