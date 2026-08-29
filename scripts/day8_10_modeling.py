#!/usr/bin/env python3
"""NHIS 2024 — Day 8-10 conventional model tuning and preliminary calibration.

This script implements the Day 8-10 gate from the 4-week plan:
- Logistic Regression comparator + moderate Random Forest / XGBoost tuning
- fixed seed/config logging
- AUROC, AUPRC, Recall, Precision, F1, Specificity, Brier
- validation-only model selection, preliminary Platt calibration, and threshold selection
- one locked test re-evaluation after all validation decisions

Scope note: WTFA_A/PPSU/PSTRAT survey-aware sensitivity is Day 11-13. Day 5 already
reported an initial WTFA_A-weighted baseline comparison, but Day 8-10 does not expand that
analysis in order to keep the original workstream boundaries clear.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

SEED = 2026
MAIN = [
    "AGEP_A", "SEX_A", "HISPALLP_A", "EDUCP_A", "RATCAT_A",
    "EMPWRKLSW1_A", "NOTCOV_A", "FDSCAT3_A", "PHSTAT_A",
    "DISAB3_A", "K6SPD_A", "CHRONIC_BURDEN_CAT",
]
NUM = ["AGEP_A"]
CAT = [c for c in MAIN if c not in NUM]
SPECIAL = {
    "AGEP_A": {97, 98, 99},
    "SEX_A": {7, 8, 9},
    "HISPALLP_A": {97, 98, 99},
    "EDUCP_A": {97, 98, 99},
    "RATCAT_A": {98},
    "EMPWRKLSW1_A": {7, 8, 9},
    "NOTCOV_A": {7, 8, 9},
    "FDSCAT3_A": {8},
    "PHSTAT_A": {7, 8, 9},
    "DISAB3_A": {9},
    "K6SPD_A": {8},
}
OUTCOMES = {
    "MEDNG": {
        "file": "analysis_ready_MEDNG_FINAL_FEATURELOCK_RAWCODES.csv",
        "target": "TARGET_FORGONE_COST",
        "expected": {
            "train": (22711, 1524),
            "validation": (3226, 233),
            "test": (6417, 438),
        },
    },
    "MEDDL": {
        "file": "analysis_ready_MEDDL_FINAL_FEATURELOCK_RAWCODES.csv",
        "target": "TARGET_DELAYED_COST",
        "expected": {
            "train": (22711, 1761),
            "validation": (3225, 280),
            "test": (6419, 523),
        },
    },
}

# Moderate, prespecified search candidates. We intentionally do not run an exhaustive grid.
RF_CANDIDATES = [
    {"n_estimators": 200, "max_depth": 6, "min_samples_leaf": 5, "max_features": "sqrt"},
    {"n_estimators": 250, "max_depth": 8, "min_samples_leaf": 5, "max_features": "sqrt"},
    {"n_estimators": 300, "max_depth": 10, "min_samples_leaf": 5, "max_features": "sqrt"},
    {"n_estimators": 300, "max_depth": 8, "min_samples_leaf": 10, "max_features": "log2"},
]
XGB_CANDIDATES = [
    {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 2},
    {"n_estimators": 300, "max_depth": 3, "learning_rate": 0.05, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 2},
    {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.03, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 2},
    {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 2},
    {"n_estimators": 400, "max_depth": 4, "learning_rate": 0.03, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 2},
    {"n_estimators": 400, "max_depth": 5, "learning_rate": 0.03, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 2},
    {"n_estimators": 250, "max_depth": 5, "learning_rate": 0.05, "subsample": 0.75, "colsample_bytree": 0.85, "min_child_weight": 5},
    {"n_estimators": 450, "max_depth": 3, "learning_rate": 0.03, "subsample": 1.0, "colsample_bytree": 0.85, "min_child_weight": 2},
]


def day5_bucket(hhx: object) -> str:
    x = int(hashlib.sha256(f"NHIS2024_DAY5|{hhx}".encode()).hexdigest()[:12], 16) % 10
    return "test" if x in (0, 1) else ("validation" if x == 2 else "train")


def validation_role(hhx: object) -> str:
    """Three deterministic roles inside Day-5 validation: tuning, calibration, threshold."""
    x = int(hashlib.sha256(f"NHIS2024_DAY8_10_VAL|{hhx}".encode()).hexdigest()[:12], 16) % 3
    return ("model_selection", "calibration", "threshold")[x]


def clean_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df[MAIN].copy()
    for col, codes in SPECIAL.items():
        x[col] = pd.to_numeric(x[col], errors="coerce")
        x.loc[x[col].isin(codes), col] = np.nan
    for col in CAT:
        if col == "CHRONIC_BURDEN_CAT":
            x[col] = x[col].where(x[col].notna(), "Missing/indeterminate").astype(str)
        else:
            x[col] = x[col].map(
                lambda v: np.nan if pd.isna(v) else str(int(v)) if float(v).is_integer() else str(v)
            )
    return x


def make_prep() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), NUM),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]), CAT),
    ])


def specificity(y_true, y_pred) -> float:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return float(tn / (tn + fp)) if (tn + fp) else float("nan")


def evaluate(y_true, probs, threshold) -> dict:
    pred = (probs >= threshold).astype(int)
    return {
        "AUROC": float(roc_auc_score(y_true, probs)),
        "AUPRC": float(average_precision_score(y_true, probs)),
        "Recall": float(recall_score(y_true, pred, zero_division=0)),
        "Precision": float(precision_score(y_true, pred, zero_division=0)),
        "F1": float(f1_score(y_true, pred, zero_division=0)),
        "Specificity": specificity(y_true, pred),
        "Brier": float(brier_score_loss(y_true, probs)),
        "Observed_prevalence": float(np.mean(y_true)),
        "Mean_predicted_probability": float(np.mean(probs)),
        "Predicted_positive_rate": float(np.mean(pred)),
    }


class PlattScaler:
    def __init__(self):
        self.model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=2000, random_state=SEED)

    @staticmethod
    def _logit(p):
        p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
        return np.log(p / (1 - p)).reshape(-1, 1)

    def fit(self, probs, y):
        self.model.fit(self._logit(probs), y)
        return self

    def transform(self, probs):
        return self.model.predict_proba(self._logit(probs))[:, 1]

    def coefficients(self):
        return {
            "intercept": float(self.model.intercept_[0]),
            "slope": float(self.model.coef_[0, 0]),
        }


def select_threshold(probs, y) -> tuple[float, float]:
    thresholds = np.linspace(0.02, 0.60, 117)
    f1s = [f1_score(y, probs >= t, zero_division=0) for t in thresholds]
    idx = int(np.argmax(f1s))
    return float(thresholds[idx]), float(f1s[idx])


def calibration_bins(y, probs, n_bins=10):
    qs = np.unique(np.quantile(probs, np.linspace(0, 1, n_bins + 1)))
    if len(qs) < 3:
        return []
    bins = np.digitize(probs, qs[1:-1], right=True)
    rows = []
    for b in range(len(qs) - 1):
        m = bins == b
        if m.any():
            rows.append({
                "bin": b + 1,
                "N": int(m.sum()),
                "mean_predicted": float(np.mean(probs[m])),
                "fraction_positive": float(np.mean(y[m])),
            })
    return rows


def build_rf(params, n_jobs):
    return RandomForestClassifier(
        **params, random_state=SEED, class_weight=None, n_jobs=n_jobs
    )


def build_xgb(params, n_jobs):
    return XGBClassifier(
        **params,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        reg_lambda=1.0,
        random_state=SEED,
        n_jobs=n_jobs,
    )


def build_lr():
    return LogisticRegression(C=1.0, solver="lbfgs", max_iter=2000, random_state=SEED)


def tune_candidates(kind, candidates, X_train, y_train, X_select, y_select, n_jobs):
    rows = []
    best = None
    for idx, params in enumerate(candidates, start=1):
        model = build_rf(params, n_jobs) if kind == "RF" else build_xgb(params, n_jobs)
        model.fit(X_train, y_train)
        probs = model.predict_proba(X_select)[:, 1]
        row = {
            "Candidate": idx,
            "Params": json.dumps(params, sort_keys=True),
            "Validation_AUPRC": float(average_precision_score(y_select, probs)),
            "Validation_AUROC": float(roc_auc_score(y_select, probs)),
            "Validation_Brier": float(brier_score_loss(y_select, probs)),
        }
        rows.append(row)
        if best is None or row["Validation_AUPRC"] > best[0]:
            best = (row["Validation_AUPRC"], params, model)
    return best[1], best[2], rows


def assert_day5_split(df, outcome, target):
    rows = []
    for split in ("train", "validation", "test"):
        m = df["SPLIT"].eq(split)
        n, pos = int(m.sum()), int(df.loc[m, target].sum())
        expected = OUTCOMES[outcome]["expected"][split]
        if (n, pos) != expected:
            raise RuntimeError(f"{outcome}/{split}: observed {(n, pos)} != Day5 {expected}")
        rows.append({"Outcome": outcome, "Split": split, "N": n, "Positive_N": pos})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("modeling/day8_10"))
    parser.add_argument("--n-jobs", type=int, default=-1)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    split_rows, val_role_rows, tuning_rows, selection_rows = [], [], [], []
    performance_rows, calibration_rows = [], []
    best_params = {}

    for outcome, spec in OUTCOMES.items():
        print(f"\n=== {outcome} ===")
        path = args.data_dir / spec["file"]
        if not path.exists():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        required = set(MAIN + ["HHX", "WTFA_A", spec["target"]])
        missing = sorted(required - set(df.columns))
        if missing:
            raise RuntimeError(f"{outcome}: missing columns {missing}")
        if not df["HHX"].is_unique:
            raise RuntimeError(f"{outcome}: HHX is not unique in the verified Sample Adult cohort")

        df["SPLIT"] = df["HHX"].map(day5_bucket)
        split_rows.extend(assert_day5_split(df, outcome, spec["target"]))

        X = clean_features(df)
        y = df[spec["target"]].astype(int).to_numpy()
        sp = df["SPLIT"].to_numpy()
        hhx = df["HHX"].to_numpy()
        tr, va, te = sp == "train", sp == "validation", sp == "test"

        val_roles = np.array([validation_role(h) for h in hhx[va]])
        y_val = y[va]
        for role in ("model_selection", "calibration", "threshold"):
            m = val_roles == role
            val_role_rows.append({
                "Outcome": outcome,
                "Role": role,
                "N": int(m.sum()),
                "Positive_N": int(y_val[m].sum()),
                "Positive_rate": float(y_val[m].mean()),
            })
            if y_val[m].sum() < 40:
                raise RuntimeError(f"{outcome}: too few positives in validation role {role}")

        # Fit preprocessing on TRAIN only, then freeze it for all Day 8-10 candidates.
        prep = make_prep()
        X_train = prep.fit_transform(X.loc[tr])
        X_val_all = prep.transform(X.loc[va])
        X_test = prep.transform(X.loc[te])
        y_train, y_test = y[tr], y[te]

        sel = val_roles == "model_selection"
        cal = val_roles == "calibration"
        thr = val_roles == "threshold"

        print("Moderate RF tuning on validation model-selection subset...")
        rf_params, rf_model, rf_rows = tune_candidates(
            "RF", RF_CANDIDATES, X_train, y_train, X_val_all[sel], y_val[sel], args.n_jobs
        )
        print("Moderate XGBoost tuning on validation model-selection subset...")
        xgb_params, xgb_model, xgb_rows = tune_candidates(
            "XGBoost", XGB_CANDIDATES, X_train, y_train, X_val_all[sel], y_val[sel], args.n_jobs
        )
        for r in rf_rows:
            tuning_rows.append({"Outcome": outcome, "Model": "RF", **r})
        for r in xgb_rows:
            tuning_rows.append({"Outcome": outcome, "Model": "XGBoost", **r})

        lr_model = build_lr()
        lr_model.fit(X_train, y_train)

        best_params[outcome] = {
            "LR": {"C": 1.0, "note": "Day-5 baseline comparator; not tuned"},
            "RF": rf_params,
            "XGBoost": xgb_params,
        }

        models = {"LR": lr_model, "RF": rf_model, "XGBoost": xgb_model}

        for model_name, model in models.items():
            p_cal_raw = model.predict_proba(X_val_all[cal])[:, 1]
            p_thr_raw = model.predict_proba(X_val_all[thr])[:, 1]
            p_test_raw = model.predict_proba(X_test)[:, 1]

            platt = PlattScaler().fit(p_cal_raw, y_val[cal])
            p_thr_platt = platt.transform(p_thr_raw)
            p_test_platt = platt.transform(p_test_raw)

            raw_brier = float(brier_score_loss(y_val[thr], p_thr_raw))
            platt_brier = float(brier_score_loss(y_val[thr], p_thr_platt))
            use_platt = platt_brier < raw_brier
            probability_version = "Platt" if use_platt else "Raw"
            p_thr_selected = p_thr_platt if use_platt else p_thr_raw
            p_test_selected = p_test_platt if use_platt else p_test_raw

            threshold, val_f1 = select_threshold(p_thr_selected, y_val[thr])
            selection_rows.append({
                "Outcome": outcome,
                "Model": model_name,
                "Selected_probability": probability_version,
                "Raw_validation_Brier": raw_brier,
                "Platt_validation_Brier": platt_brier,
                "Threshold": threshold,
                "Validation_F1": val_f1,
                "Validation_AUPRC": float(average_precision_score(y_val[thr], p_thr_selected)),
                "Validation_AUROC": float(roc_auc_score(y_val[thr], p_thr_selected)),
                "Platt_intercept": platt.coefficients()["intercept"],
                "Platt_slope": platt.coefficients()["slope"],
            })

            perf = {
                "Outcome": outcome,
                "Model": model_name,
                "Selected_probability": probability_version,
                "Threshold": threshold,
                **evaluate(y_test, p_test_selected, threshold),
            }
            performance_rows.append(perf)

            # Save both raw and Platt test calibration curves as preliminary calibration evidence.
            for version, probs in [("Raw", p_test_raw), ("Platt", p_test_platt)]:
                for row in calibration_bins(y_test, probs, n_bins=10):
                    calibration_rows.append({
                        "Outcome": outcome,
                        "Model": model_name,
                        "Probability_version": version,
                        **row,
                    })

    split_df = pd.DataFrame(split_rows)
    val_role_df = pd.DataFrame(val_role_rows)
    tuning_df = pd.DataFrame(tuning_rows)
    selection_df = pd.DataFrame(selection_rows)
    performance_df = pd.DataFrame(performance_rows).sort_values(["Outcome", "AUPRC"], ascending=[True, False])
    calibration_df = pd.DataFrame(calibration_rows)

    split_df.to_csv(args.out_dir / "day8_10_split_audit.csv", index=False)
    val_role_df.to_csv(args.out_dir / "day8_10_validation_role_audit.csv", index=False)
    tuning_df.to_csv(args.out_dir / "day8_10_tuning_candidates.csv", index=False)
    selection_df.to_csv(args.out_dir / "day8_10_validation_selection.csv", index=False)
    performance_df.to_csv(args.out_dir / "day8_10_model_performance.csv", index=False)
    calibration_df.to_csv(args.out_dir / "day8_10_calibration_points.csv", index=False)

    config = {
        "status": "DAY8_10_COMPLETE_LOCKED_TEST_REEVALUATION",
        "seed": SEED,
        "outcomes": list(OUTCOMES.keys()),
        "features": MAIN,
        "split": "Day-5 deterministic HHX SHA-256 70/10/20 split preserved exactly.",
        "validation_subdivision": "Deterministic 3-way HHX hash: model_selection / calibration / threshold.",
        "preprocessing": "Fit on TRAIN only, then frozen. Same Day-5 variable-specific special-code handling and 12-construct main feature set.",
        "tuning": "Moderate prespecified candidate search for RF/XGBoost; candidate selected by AUPRC on validation model-selection subset. LR remains fixed Day-5 baseline comparator.",
        "calibration": "Platt scaling fit on validation calibration subset; Raw vs Platt chosen by Brier on threshold subset.",
        "threshold": "F1-maximizing operating point on validation threshold subset; not a clinical cutoff.",
        "test_policy": "Test touched only after tuning/calibration/threshold decisions. Test had already been reported once at Day 5 baseline, so no further choices should be driven by Day 8-10 test results.",
        "day11_13_boundary": "WTFA_A/PPSU/PSTRAT survey-aware sensitivity and weighted-vs-unweighted interpretation remain Day 11-13. Day 5 preliminary weighting results are not expanded here.",
        "best_params": best_params,
        "outputs": [
            "day8_10_split_audit.csv",
            "day8_10_validation_role_audit.csv",
            "day8_10_tuning_candidates.csv",
            "day8_10_validation_selection.csv",
            "day8_10_model_performance.csv",
            "day8_10_calibration_points.csv",
            "day8_10_config_log.json",
        ],
    }
    (args.out_dir / "day8_10_config_log.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n=== LOCKED TEST PERFORMANCE ===")
    cols = ["Outcome", "Model", "Selected_probability", "Threshold", "AUROC", "AUPRC", "Recall", "Precision", "F1", "Specificity", "Brier"]
    print(performance_df[cols].to_string(index=False))
    print(f"\nSaved outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
