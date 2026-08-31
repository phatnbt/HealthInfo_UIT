"""NHIS 2024 Day 14-16 locked-model SHAP explainability.

This analysis is evaluation-only. It reconstructs the locked Day 8-10
unweighted LR/RF/XGBoost estimators, verifies their locked-test performance,
and explains their base-estimator outputs on the unchanged test split.

Important boundaries:
* SHAP is predictive attribution, not a causal or etiologic effect.
* No SHAP result is used to change predictors, hyperparameters, calibration,
  thresholds, or model retention.
* MEDDL's locked Platt layer is audited but SHAP explains the underlying base
  estimator. The calibration layer is monotonic and is not decomposed here.
* Person-level predictions and SHAP values are never written to disk. Only
  aggregate tables and figures are exported.
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
import shap
from day8_10_modeling import (
    MAIN,
    OUTCOMES,
    SEED,
    SPECIAL,
    PlattScaler,
    assert_day5_split,
    build_lr,
    build_rf,
    build_xgb,
    clean_features,
    day5_bucket,
    evaluate,
    make_prep,
    validation_role,
)
from scipy.stats import spearmanr

MODELS = ("LR", "RF", "XGBoost")
TREE_MODELS = ("RF", "XGBoost")
SUBGROUPS = ("HISPALLP_A", "RATCAT_A", "NOTCOV_A", "SEX_A", "AGE_GROUP")
PRIMARY_EQUITY_SUBGROUP = "HISPALLP_A"
AUDIT_METRICS = ("AUROC", "AUPRC", "Recall", "Precision", "F1", "Specificity", "Brier")
AUDIT_TOLERANCE = 1e-8
MIN_SUBGROUP_N = 100


def build_locked_model(model_name: str, params: dict, n_jobs: int):
    if model_name == "LR":
        return build_lr()
    if model_name == "RF":
        return build_rf(params, n_jobs)
    if model_name == "XGBoost":
        return build_xgb(params, n_jobs)
    raise ValueError(f"Unknown model: {model_name}")


def deterministic_indices(n: int, requested: int, seed: int) -> np.ndarray:
    if requested <= 0 or requested >= n:
        return np.arange(n, dtype=int)
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n, size=requested, replace=False))


def encoded_to_construct(encoded_name: str) -> str:
    name = encoded_name.split("__", 1)[-1]
    for construct in sorted(MAIN, key=len, reverse=True):
        if name == construct or name.startswith(f"{construct}_"):
            return construct
    raise RuntimeError(f"Cannot map encoded feature to locked construct: {encoded_name}")


def display_feature_name(encoded_name: str, construct: str) -> str:
    name = encoded_name.split("__", 1)[-1]
    if name == construct:
        return construct
    suffix = name[len(construct) + 1 :]
    return f"{construct}={suffix}"


def normalize_shap_output(values, model_name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if model_name == "RF":
        if array.ndim != 3 or array.shape[-1] != 2:
            raise RuntimeError(f"Unexpected RF SHAP shape: {array.shape}")
        return array[:, :, 1]
    if array.ndim != 2:
        raise RuntimeError(f"Unexpected {model_name} SHAP shape: {array.shape}")
    return array


def normalize_interaction_output(values, model_name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if model_name == "RF":
        if array.ndim != 4 or array.shape[-1] != 2:
            raise RuntimeError(f"Unexpected RF interaction shape: {array.shape}")
        return array[:, :, :, 1]
    if array.ndim != 3:
        raise RuntimeError(f"Unexpected {model_name} interaction shape: {array.shape}")
    return array


def aggregate_construct_values(shap_values: np.ndarray, construct_for_column: list[str]) -> np.ndarray:
    result = np.zeros((shap_values.shape[0], len(MAIN)), dtype=float)
    for construct_index, construct in enumerate(MAIN):
        columns = [i for i, value in enumerate(construct_for_column) if value == construct]
        if not columns:
            raise RuntimeError(f"No encoded columns found for {construct}")
        result[:, construct_index] = np.sum(shap_values[:, columns], axis=1)
    return result


def weighted_mean(values: np.ndarray, weights: np.ndarray | None) -> float:
    return float(np.mean(values)) if weights is None else float(np.average(values, weights=weights))


def global_importance_rows(
    outcome: str,
    model_name: str,
    construct_values: np.ndarray,
    test_weights: np.ndarray,
    explained_output: str,
) -> list[dict]:
    rows = []
    for aggregation, weights in (("Unweighted", None), ("WTFA_A", test_weights)):
        importances = np.array(
            [weighted_mean(np.abs(construct_values[:, j]), weights) for j in range(len(MAIN))]
        )
        signed = np.array(
            [weighted_mean(construct_values[:, j], weights) for j in range(len(MAIN))]
        )
        denominator = float(np.sum(importances))
        order = np.argsort(-importances)
        for rank, index in enumerate(order, start=1):
            rows.append({
                "Outcome": outcome,
                "Model": model_name,
                "Split": "locked_test",
                "Explained_output": explained_output,
                "Aggregation": aggregation,
                "Rank": rank,
                "Feature_construct": MAIN[index],
                "Mean_abs_SHAP": float(importances[index]),
                "Importance_share_pct": float(100 * importances[index] / denominator) if denominator else 0.0,
                "Mean_signed_SHAP": float(signed[index]),
                "N_explained": int(construct_values.shape[0]),
            })
    return rows


def encoded_importance_rows(
    outcome: str,
    model_name: str,
    shap_values: np.ndarray,
    encoded_names: list[str],
    constructs: list[str],
    test_weights: np.ndarray,
    explained_output: str,
) -> list[dict]:
    importance = np.average(np.abs(shap_values), axis=0, weights=test_weights)
    signed = np.average(shap_values, axis=0, weights=test_weights)
    order = np.argsort(-importance)
    denominator = float(np.sum(importance))
    rows = []
    for rank, index in enumerate(order, start=1):
        rows.append({
            "Outcome": outcome,
            "Model": model_name,
            "Split": "locked_test",
            "Explained_output": explained_output,
            "Aggregation": "WTFA_A",
            "Rank": rank,
            "Encoded_feature": display_feature_name(encoded_names[index], constructs[index]),
            "Feature_construct": constructs[index],
            "Mean_abs_SHAP": float(importance[index]),
            "Importance_share_pct": float(100 * importance[index] / denominator) if denominator else 0.0,
            "Mean_signed_SHAP": float(signed[index]),
            "N_explained": int(shap_values.shape[0]),
        })
    return rows


def cleaned_category(series: pd.Series, feature: str) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if feature in SPECIAL:
        numeric = numeric.mask(numeric.isin(SPECIAL[feature]))
    return numeric.map(lambda value: "Missing/special" if pd.isna(value) else f"code_{int(value)}")


def subgroup_series(test_frame: pd.DataFrame, subgroup: str) -> pd.Series:
    if subgroup == "AGE_GROUP":
        age = pd.to_numeric(test_frame["AGEP_A"], errors="coerce")
        age = age.mask(age.isin(SPECIAL["AGEP_A"]))
        values = pd.cut(
            age,
            bins=[17, 34, 49, 64, math.inf],
            labels=["18-34", "35-49", "50-64", "65+"],
        ).astype(object)
        return pd.Series(values, index=test_frame.index).fillna("Missing/special").astype(str)
    return cleaned_category(test_frame[subgroup], subgroup)


def subgroup_importance_rows(
    outcome: str,
    model_name: str,
    construct_values: np.ndarray,
    test_frame: pd.DataFrame,
    test_weights: np.ndarray,
    explained_output: str,
) -> tuple[list[dict], list[dict]]:
    rows, skipped = [], []
    for subgroup in SUBGROUPS:
        labels = subgroup_series(test_frame, subgroup).to_numpy()
        for level in sorted(np.unique(labels)):
            mask = labels == level
            n = int(np.sum(mask))
            if n < MIN_SUBGROUP_N:
                skipped.append({
                    "Outcome": outcome,
                    "Model": model_name,
                    "Subgroup": subgroup,
                    "Level": level,
                    "N": n,
                    "Reason": f"N < {MIN_SUBGROUP_N}",
                })
                continue
            for aggregation, weights in (
                ("Unweighted", None),
                ("WTFA_A", test_weights[mask]),
            ):
                importance = np.array([
                    weighted_mean(np.abs(construct_values[mask, j]), weights)
                    for j in range(len(MAIN))
                ])
                denominator = float(np.sum(importance))
                order = np.argsort(-importance)
                for rank, index in enumerate(order, start=1):
                    rows.append({
                        "Outcome": outcome,
                        "Model": model_name,
                        "Split": "locked_test",
                        "Explained_output": explained_output,
                        "Subgroup": subgroup,
                        "Level": level,
                        "Aggregation": aggregation,
                        "Rank": rank,
                        "Feature_construct": MAIN[index],
                        "Mean_abs_SHAP": float(importance[index]),
                        "Importance_share_pct": float(100 * importance[index] / denominator) if denominator else 0.0,
                        "N": n,
                        "Weight_sum": float(np.sum(test_weights[mask])),
                    })
    return rows, skipped


def direction_rows(
    outcome: str,
    model_name: str,
    construct_values: np.ndarray,
    test_frame: pd.DataFrame,
    test_weights: np.ndarray,
    explained_output: str,
) -> tuple[list[dict], list[dict]]:
    summary, categories = [], []
    for j, feature in enumerate(MAIN):
        values = construct_values[:, j]
        if feature == "AGEP_A":
            raw = pd.to_numeric(test_frame[feature], errors="coerce").to_numpy(dtype=float)
            valid = np.isfinite(raw) & ~np.isin(raw, list(SPECIAL[feature]))
            rho = float(spearmanr(raw[valid], values[valid]).statistic)
            if rho >= 0.10:
                direction = "higher value -> higher model output"
            elif rho <= -0.10:
                direction = "higher value -> lower model output"
            else:
                direction = "weak/non-monotonic pattern"
            summary.append({
                "Outcome": outcome,
                "Model": model_name,
                "Feature_construct": feature,
                "Explained_output": explained_output,
                "Direction_method": "Spearman(raw value, construct SHAP)",
                "Direction_summary": direction,
                "Spearman_rho": rho,
                "N": int(np.sum(valid)),
            })
            continue

        levels = cleaned_category(test_frame[feature], feature).to_numpy()
        level_rows = []
        for level in sorted(np.unique(levels)):
            mask = levels == level
            n = int(np.sum(mask))
            if n == 0:
                continue
            level_row = {
                "Outcome": outcome,
                "Model": model_name,
                "Feature_construct": feature,
                "Explained_output": explained_output,
                "Level": level,
                "N": n,
                "Weighted_mean_SHAP": float(np.average(values[mask], weights=test_weights[mask])),
                "Weighted_mean_abs_SHAP": float(np.average(np.abs(values[mask]), weights=test_weights[mask])),
                "Weight_sum": float(np.sum(test_weights[mask])),
            }
            categories.append(level_row)
            level_rows.append(level_row)
        if level_rows:
            lowest = min(level_rows, key=lambda row: row["Weighted_mean_SHAP"])
            highest = max(level_rows, key=lambda row: row["Weighted_mean_SHAP"])
            direction = f"category-specific: lowest {lowest['Level']}; highest {highest['Level']}"
        else:
            direction = "category-specific"
        summary.append({
            "Outcome": outcome,
            "Model": model_name,
            "Feature_construct": feature,
            "Explained_output": explained_output,
            "Direction_method": "WTFA_A-weighted mean construct SHAP by raw category code",
            "Direction_summary": direction,
            "Spearman_rho": np.nan,
            "N": len(values),
        })
    return summary, categories


def aggregate_interactions(
    interaction_values: np.ndarray,
    construct_for_column: list[str],
    outcome: str,
    model_name: str,
    explained_output: str,
) -> list[dict]:
    pair_rows = []
    indices = {
        construct: [i for i, value in enumerate(construct_for_column) if value == construct]
        for construct in MAIN
    }
    for left in range(len(MAIN)):
        for right in range(left + 1, len(MAIN)):
            block = interaction_values[:, indices[MAIN[left]], :][:, :, indices[MAIN[right]]]
            per_row = np.sum(block, axis=(1, 2))
            pair_rows.append({
                "Outcome": outcome,
                "Model": model_name,
                "Split": "locked_test",
                "Explained_output": explained_output,
                "Feature_1": MAIN[left],
                "Feature_2": MAIN[right],
                "Mean_abs_interaction_SHAP": float(np.mean(np.abs(per_row))),
                "Mean_signed_interaction_SHAP": float(np.mean(per_row)),
                "N_interaction_screen": int(interaction_values.shape[0]),
            })
    pair_rows.sort(key=lambda row: row["Mean_abs_interaction_SHAP"], reverse=True)
    for rank, row in enumerate(pair_rows, start=1):
        row["Rank"] = rank
    return pair_rows


def save_summary_plot(
    shap_values: np.ndarray,
    encoded_matrix: np.ndarray,
    display_names: list[str],
    display_indices: np.ndarray,
    outcome: str,
    model_name: str,
    explained_output: str,
    output_path: Path,
):
    shap.summary_plot(
        shap_values[display_indices],
        encoded_matrix[display_indices],
        feature_names=display_names,
        max_display=15,
        show=False,
        plot_size=(10, 7),
    )
    figure = plt.gcf()
    figure.suptitle(
        f"{outcome} - {model_name} - SHAP summary\nlocked test; {explained_output}; unweighted display sample",
        fontsize=12,
        y=1.01,
    )
    figure.tight_layout()
    figure.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(figure)


def save_dependence_plot(
    feature: str,
    construct_values: np.ndarray,
    test_frame: pd.DataFrame,
    display_indices: np.ndarray,
    outcome: str,
    model_name: str,
    explained_output: str,
    output_path: Path,
):
    values = construct_values[:, MAIN.index(feature)]
    fig, ax = plt.subplots(figsize=(9, 6))
    if feature == "AGEP_A":
        raw = pd.to_numeric(test_frame[feature], errors="coerce").to_numpy(dtype=float)
        valid = np.isfinite(raw) & ~np.isin(raw, list(SPECIAL[feature]))
        indices = np.intersect1d(display_indices, np.flatnonzero(valid))
        ax.scatter(raw[indices], values[indices], s=12, alpha=0.35, color="#2563eb", edgecolors="none")
        ax.set_xlabel("AGEP_A (years)")
    else:
        categories = cleaned_category(test_frame[feature], feature).to_numpy()
        counts = pd.Series(categories).value_counts()
        kept = counts.head(10).index.tolist()
        data = [values[(categories == level) & np.isin(np.arange(len(values)), display_indices)] for level in kept]
        ax.boxplot(data, tick_labels=kept, showfliers=False)
        ax.tick_params(axis="x", rotation=35)
        ax.set_xlabel(f"{feature} raw public-use category")
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_ylabel("Construct-level SHAP value")
    ax.set_title(
        f"{outcome} - {model_name} - dependence pattern for {feature}\n"
        f"locked test; {explained_output}; descriptive, not causal"
    )
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def save_interaction_plot(rows: list[dict], output_path: Path):
    top = rows[:10][::-1]
    labels = [f"{row['Feature_1']} x {row['Feature_2']}" for row in top]
    values = [row["Mean_abs_interaction_SHAP"] for row in top]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(labels, values, color="#7c3aed")
    ax.set_xlabel("Mean absolute interaction SHAP (screening sample)")
    ax.set_title(
        f"{rows[0]['Outcome']} - {rows[0]['Model']} - exploratory interaction screen\n"
        f"locked test; {rows[0]['Explained_output']}; not causal"
    )
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def save_global_plot(global_frame: pd.DataFrame, outcome: str, output_path: Path):
    fig, axes = plt.subplots(1, 3, figsize=(17, 7), sharex=False)
    for ax, model_name in zip(axes, MODELS):
        subset = global_frame[
            global_frame["Outcome"].eq(outcome)
            & global_frame["Model"].eq(model_name)
            & global_frame["Aggregation"].eq("WTFA_A")
        ].sort_values("Mean_abs_SHAP", ascending=True)
        ax.barh(subset["Feature_construct"], subset["Importance_share_pct"], color="#0f766e")
        ax.set_title(model_name)
        ax.set_xlabel("WTFA_A-weighted importance share (%)")
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle(
        f"{outcome} - locked-test construct-level SHAP importance\n"
        "Base estimators; population-weighted aggregation; predictive, not causal",
        fontsize=13,
    )
    fig.tight_layout()
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def save_primary_subgroup_heatmap(subgroup_frame: pd.DataFrame, outcome: str, output_path: Path):
    if subgroup_frame.empty or "Outcome" not in subgroup_frame.columns:
        return
    subset = subgroup_frame[
        subgroup_frame["Outcome"].eq(outcome)
        & subgroup_frame["Subgroup"].eq(PRIMARY_EQUITY_SUBGROUP)
        & subgroup_frame["Aggregation"].eq("WTFA_A")
    ].copy()
    if subset.empty:
        return
    subset["Row"] = subset["Model"] + " | " + subset["Level"]
    pivot = subset.pivot(index="Row", columns="Feature_construct", values="Importance_share_pct")
    pivot = pivot.reindex(columns=MAIN)
    row_order = []
    for model_name in MODELS:
        row_order.extend(sorted(row for row in pivot.index if row.startswith(f"{model_name} |")))
    pivot = pivot.reindex(row_order)
    fig_height = max(6, 0.34 * len(pivot) + 2)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    image = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="viridis")
    ax.set_xticks(np.arange(len(pivot.columns)), labels=pivot.columns, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)), labels=pivot.index)
    ax.set_title(
        f"{outcome} - SHAP pattern by {PRIMARY_EQUITY_SUBGROUP}\n"
        "raw public-use codes; WTFA_A-weighted; explanation pattern, not a fairness metric"
    )
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("Within-group importance share (%)")
    fig.tight_layout()
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def runtime_versions() -> dict:
    packages = ("numpy", "pandas", "scipy", "scikit-learn", "matplotlib", "xgboost", "shap")
    return {package: importlib.metadata.version(package) for package in packages}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--locked-dir", type=Path, default=Path("modeling/day8_10"))
    parser.add_argument("--out-dir", type=Path, default=Path("modeling/day14_16"))
    parser.add_argument("--n-jobs", type=int, default=2)
    parser.add_argument("--max-explain-n", type=int, default=0, help="0 uses the full locked test split")
    parser.add_argument("--display-n", type=int, default=1500)
    parser.add_argument("--interaction-n", type=int, default=100)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = args.out_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    config_path = args.locked_dir / "day8_10_config_log.json"
    selection_path = args.locked_dir / "day8_10_validation_selection.csv"
    performance_path = args.locked_dir / "day8_10_model_performance.csv"
    for path in (config_path, selection_path, performance_path):
        if not path.exists():
            raise FileNotFoundError(path)
    locked_config = json.loads(config_path.read_text(encoding="utf-8"))
    locked_selection = pd.read_csv(selection_path).set_index(["Outcome", "Model"])
    locked_performance = pd.read_csv(performance_path).set_index(["Outcome", "Model"])

    global_rows, encoded_rows = [], []
    direction_summary_rows, category_direction_rows = [], []
    subgroup_rows, skipped_subgroup_rows = [], []
    interaction_rows, audit_rows = [], []

    for outcome_index, (outcome, spec) in enumerate(OUTCOMES.items()):
        print(f"\n=== {outcome}: locked-model SHAP ===", flush=True)
        source_path = args.data_dir / spec["file"]
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        frame = pd.read_csv(source_path)
        required = set(MAIN + ["HHX", "WTFA_A", spec["target"]])
        missing = sorted(required - set(frame.columns))
        if missing:
            raise RuntimeError(f"{outcome}: missing columns {missing}")
        if not frame["HHX"].is_unique:
            raise RuntimeError(f"{outcome}: HHX must be unique")
        frame["SPLIT"] = frame["HHX"].map(day5_bucket)
        assert_day5_split(frame, outcome, spec["target"])

        clean = clean_features(frame)
        target = frame[spec["target"]].astype(int).to_numpy()
        split = frame["SPLIT"].to_numpy()
        train_mask, validation_mask, test_mask = split == "train", split == "validation", split == "test"
        validation_roles = np.array([validation_role(value) for value in frame.loc[validation_mask, "HHX"]])
        calibration_mask = validation_roles == "calibration"

        prep = make_prep()
        x_train = prep.fit_transform(clean.loc[train_mask])
        x_validation = prep.transform(clean.loc[validation_mask])
        x_test_sparse = prep.transform(clean.loc[test_mask])
        encoded_names = list(prep.get_feature_names_out())
        constructs = [encoded_to_construct(name) for name in encoded_names]
        display_names = [display_feature_name(name, construct) for name, construct in zip(encoded_names, constructs)]

        y_train = target[train_mask]
        y_validation = target[validation_mask]
        y_test_full = target[test_mask]
        test_frame_full = frame.loc[test_mask].reset_index(drop=True)
        test_weights_full = test_frame_full["WTFA_A"].to_numpy(dtype=float)

        explain_indices = deterministic_indices(
            len(test_frame_full), args.max_explain_n, SEED + 1000 * outcome_index
        )
        x_test = x_test_sparse[explain_indices].toarray().astype(np.float32)
        test_frame = test_frame_full.iloc[explain_indices].reset_index(drop=True)
        test_weights = test_weights_full[explain_indices]
        display_indices = deterministic_indices(
            len(explain_indices), args.display_n, SEED + 1000 * outcome_index + 101
        )
        background_indices = deterministic_indices(
            x_train.shape[0], 500, SEED + 1000 * outcome_index + 202
        )
        x_background = x_train[background_indices].toarray().astype(np.float32)

        for model_index, model_name in enumerate(MODELS):
            print(f"  {model_name}: fit locked estimator and verify performance...", flush=True)
            selected = locked_selection.loc[(outcome, model_name)]
            params = locked_config["best_params"][outcome][model_name]
            if model_name == "LR":
                params = {"C": 1.0}
            model = build_locked_model(model_name, params, args.n_jobs)
            model.fit(x_train, y_train)

            raw_validation = model.predict_proba(x_validation[calibration_mask])[:, 1]
            raw_test_full = model.predict_proba(x_test_sparse)[:, 1]
            if str(selected["Selected_probability"]) == "Platt":
                platt = PlattScaler().fit(raw_validation, y_validation[calibration_mask])
                selected_test = platt.transform(raw_test_full)
            else:
                selected_test = raw_test_full
            reproduced = evaluate(y_test_full, selected_test, float(selected["Threshold"]))
            locked = locked_performance.loc[(outcome, model_name)]
            differences = {
                metric: abs(float(reproduced[metric]) - float(locked[metric]))
                for metric in AUDIT_METRICS
            }
            max_difference = max(differences.values())
            status = "PASS" if max_difference <= AUDIT_TOLERANCE else "FAIL"
            audit_rows.append({
                "Outcome": outcome,
                "Model": model_name,
                "Status": status,
                "Rows_in_locked_test": len(y_test_full),
                "Selected_probability": str(selected["Selected_probability"]),
                "Locked_threshold": float(selected["Threshold"]),
                "Max_absolute_metric_difference": float(max_difference),
                "Tolerance": AUDIT_TOLERANCE,
                **{f"Abs_diff_{metric}": value for metric, value in differences.items()},
            })
            if status != "PASS":
                raise RuntimeError(f"{outcome}/{model_name}: locked performance drift {max_difference}")

            print(f"  {model_name}: compute SHAP on N={len(x_test):,} locked-test rows...", flush=True)
            if model_name == "LR":
                masker = shap.maskers.Independent(x_background, max_samples=len(x_background))
                explainer = shap.LinearExplainer(model, masker)
                explanation = explainer(x_test)
                explained_output = "base_estimator_log_odds"
            else:
                explainer = shap.TreeExplainer(model)
                explanation = explainer(x_test, check_additivity=False)
                explained_output = (
                    "base_estimator_positive_class_probability"
                    if model_name == "RF"
                    else "base_estimator_raw_margin_log_odds"
                )
            shap_values = normalize_shap_output(explanation.values, model_name)
            construct_values = aggregate_construct_values(shap_values, constructs)

            global_rows.extend(global_importance_rows(
                outcome, model_name, construct_values, test_weights, explained_output
            ))
            encoded_rows.extend(encoded_importance_rows(
                outcome, model_name, shap_values, encoded_names, constructs, test_weights, explained_output
            ))
            summary, categories = direction_rows(
                outcome, model_name, construct_values, test_frame, test_weights, explained_output
            )
            direction_summary_rows.extend(summary)
            category_direction_rows.extend(categories)
            model_subgroups, model_skipped = subgroup_importance_rows(
                outcome, model_name, construct_values, test_frame, test_weights, explained_output
            )
            subgroup_rows.extend(model_subgroups)
            skipped_subgroup_rows.extend(model_skipped)

            save_summary_plot(
                shap_values,
                x_test,
                display_names,
                display_indices,
                outcome,
                model_name,
                explained_output,
                figure_dir / f"shap_summary_{outcome}_{model_name}.svg",
            )

            current_global = pd.DataFrame(global_importance_rows(
                outcome, model_name, construct_values, test_weights, explained_output
            ))
            top_feature = str(
                current_global[current_global["Aggregation"].eq("WTFA_A")]
                .sort_values("Rank")
                .iloc[0]["Feature_construct"]
            )
            save_dependence_plot(
                top_feature,
                construct_values,
                test_frame,
                display_indices,
                outcome,
                model_name,
                explained_output,
                figure_dir / f"shap_dependence_{outcome}_{model_name}_{top_feature}.svg",
            )

            if model_name in TREE_MODELS and args.interaction_n > 0:
                interaction_indices = deterministic_indices(
                    len(x_test),
                    args.interaction_n,
                    SEED + 1000 * outcome_index + 10 * model_index + 303,
                )
                print(
                    f"  {model_name}: exploratory interaction screen N={len(interaction_indices)}...",
                    flush=True,
                )
                interactions = normalize_interaction_output(
                    explainer.shap_interaction_values(x_test[interaction_indices]), model_name
                )
                rows = aggregate_interactions(
                    interactions, constructs, outcome, model_name, explained_output
                )
                interaction_rows.extend(rows)
                save_interaction_plot(
                    rows, figure_dir / f"shap_interaction_{outcome}_{model_name}.svg"
                )

    global_frame = pd.DataFrame(global_rows)
    encoded_frame = pd.DataFrame(encoded_rows)
    direction_frame = pd.DataFrame(direction_summary_rows)
    category_frame = pd.DataFrame(category_direction_rows)
    subgroup_frame = pd.DataFrame(subgroup_rows)
    skipped_frame = pd.DataFrame(skipped_subgroup_rows)
    interaction_frame = pd.DataFrame(interaction_rows)
    audit_frame = pd.DataFrame(audit_rows)

    global_frame.to_csv(args.out_dir / "day14_16_shap_global_importance.csv", index=False)
    encoded_frame.to_csv(args.out_dir / "day14_16_shap_encoded_importance.csv", index=False)
    direction_frame.to_csv(args.out_dir / "day14_16_shap_direction_summary.csv", index=False)
    category_frame.to_csv(args.out_dir / "day14_16_shap_category_patterns.csv", index=False)
    subgroup_frame.to_csv(args.out_dir / "day14_16_shap_subgroup_patterns.csv", index=False)
    skipped_frame.to_csv(args.out_dir / "day14_16_shap_subgroup_skipped.csv", index=False)
    interaction_frame.to_csv(args.out_dir / "day14_16_shap_interaction_screen.csv", index=False)
    audit_frame.to_csv(args.out_dir / "day14_16_locked_reproduction_audit.csv", index=False)

    for outcome in OUTCOMES:
        save_global_plot(
            global_frame, outcome, figure_dir / f"shap_global_constructs_{outcome}.svg"
        )
        save_primary_subgroup_heatmap(
            subgroup_frame,
            outcome,
            figure_dir / f"shap_subgroup_{PRIMARY_EQUITY_SUBGROUP}_{outcome}.svg",
        )

    config = {
        "status": "DAY14_16_SHAP_EXPLAINABILITY_COMPLETE",
        "seed": SEED,
        "runtime_versions": runtime_versions(),
        "outcomes": list(OUTCOMES),
        "models": list(MODELS),
        "features": MAIN,
        "model_lock": "Reconstruct Day 8-10 unweighted estimators with locked hyperparameters and train-only preprocessing; no tuning or reselection.",
        "locked_reproduction": {
            "status": "PASS" if audit_frame["Status"].eq("PASS").all() else "FAIL",
            "rows_compared": len(audit_frame),
            "tolerance": AUDIT_TOLERANCE,
            "max_absolute_metric_difference": float(audit_frame["Max_absolute_metric_difference"].max()),
        },
        "explanation_split": "Locked Day-5/Day-8-10 test split. Full test used unless --max-explain-n is explicitly set for a smoke run.",
        "n_explained": {
            outcome: int(global_frame[global_frame["Outcome"].eq(outcome)]["N_explained"].max())
            for outcome in OUTCOMES
        },
        "explainers": {
            "LR": "SHAP LinearExplainer with deterministic 500-row training background; log-odds output.",
            "RF": "SHAP TreeExplainer; positive-class probability output.",
            "XGBoost": "SHAP TreeExplainer; raw-margin/log-odds output.",
        },
        "calibration_boundary": "MEDDL Platt performance is reproduced, but SHAP explains the base estimator before the locked monotonic Platt layer.",
        "importance_aggregation": ["Unweighted", "WTFA_A-weighted on locked test"],
        "subgroup_pattern_axes": list(SUBGROUPS),
        "primary_equity_subgroup": PRIMARY_EQUITY_SUBGROUP,
        "minimum_subgroup_n": MIN_SUBGROUP_N,
        "interaction_screen": {
            "models": list(TREE_MODELS),
            "sample_n_requested": args.interaction_n,
            "scope": "Exploratory construct-pair screen; not a confirmatory interaction test.",
        },
        "interpretation_lock": "SHAP values are predictive attributions, not causes, independent etiologic effects, or evidence that a subgroup difference is unfair.",
        "test_policy": "Explanation-only use. SHAP outputs must not change model, predictors, calibration, threshold, or model-retention decisions.",
        "privacy": "Only aggregate SHAP tables and figures are saved; no HHX, person-level prediction, or person-level SHAP matrix is written.",
        "outputs": [
            "day14_16_shap_global_importance.csv",
            "day14_16_shap_encoded_importance.csv",
            "day14_16_shap_direction_summary.csv",
            "day14_16_shap_category_patterns.csv",
            "day14_16_shap_subgroup_patterns.csv",
            "day14_16_shap_subgroup_skipped.csv",
            "day14_16_shap_interaction_screen.csv",
            "day14_16_locked_reproduction_audit.csv",
            "figures/*.svg",
            "day14_16_config_log.json",
        ],
    }
    (args.out_dir / "day14_16_config_log.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    top = (
        global_frame[global_frame["Aggregation"].eq("WTFA_A")]
        .sort_values(["Outcome", "Model", "Rank"])
        .groupby(["Outcome", "Model"], as_index=False)
        .head(5)
    )
    print("\n=== WTFA_A-WEIGHTED TOP-5 CONSTRUCTS ===")
    print(top[["Outcome", "Model", "Rank", "Feature_construct", "Importance_share_pct"]].to_string(index=False))
    print(f"\nSaved aggregate-only outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
