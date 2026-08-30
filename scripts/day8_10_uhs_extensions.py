#!/usr/bin/env python3
"""UHS-requested evaluation extension for the locked NHIS 2024 Day 8–10 models.

Adds, without re-opening model selection:
- nonparametric paired-bootstrap 95% CIs for AUROC/AUPRC;
- locked-probability calibration plots/data;
- exploratory Decision Curve Analysis (DCA);
- a combined model-selection evidence table.

This script imports the locked Day 8–10 implementation from `day8_10_modeling.py`
and reads the committed config/selection/performance artifacts. It does not tune
new hyperparameters or choose new probability versions/thresholds.

Caveats:
- Bootstrap CIs are held-out predictive-performance CIs, not complex-survey
  design-based CIs; WTFA_A/PPSU/PSTRAT are not used here.
- DCA is exploratory and framed as hypothetical risk-based outreach/prioritization,
  not demonstrated clinical/policy utility.
- The same test split was already reported at Day 5; outputs here are evaluation
  only and must not drive further tuning.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
import day8_10_modeling as base  # noqa: E402

BOOTSTRAP_SEED = 20260830


def load_locked_metadata(repo_root: Path):
    model_dir = repo_root / "modeling" / "day8_10"
    config = json.loads((model_dir / "day8_10_config_log.json").read_text(encoding="utf-8"))
    selection = pd.read_csv(model_dir / "day8_10_validation_selection.csv")
    performance = pd.read_csv(model_dir / "day8_10_model_performance.csv")
    return config, selection, performance


def build_locked_model(name: str, params: dict, n_jobs: int):
    if name == "LR":
        return base.build_lr()
    if name == "RF":
        return base.build_rf(params, n_jobs)
    if name == "XGBoost":
        return base.build_xgb(params, n_jobs)
    raise ValueError(name)


def paired_bootstrap(y, probs_by_model, reps: int, seed: int):
    rng = np.random.default_rng(seed)
    n = len(y)
    models = list(probs_by_model)
    auc = {m: np.empty(reps) for m in models}
    ap = {m: np.empty(reps) for m in models}
    i = 0
    while i < reps:
        idx = rng.integers(0, n, size=n)
        yb = y[idx]
        if np.unique(yb).size < 2:
            continue
        for m in models:
            pb = probs_by_model[m][idx]
            auc[m][i] = roc_auc_score(yb, pb)
            ap[m][i] = average_precision_score(yb, pb)
        i += 1
    return auc, ap


def calibration_bins(y, p, n_bins=10):
    edges = np.unique(np.quantile(p, np.linspace(0, 1, n_bins + 1)))
    bins = np.digitize(p, edges[1:-1], right=True)
    rows = []
    for b in range(len(edges) - 1):
        m = bins == b
        if m.any():
            rows.append({
                "Bin": b + 1,
                "N": int(m.sum()),
                "Mean_predicted": float(p[m].mean()),
                "Observed_fraction": float(y[m].mean()),
                "Min_predicted": float(p[m].min()),
                "Max_predicted": float(p[m].max()),
            })
    return rows


def decision_curve(y, p, thresholds):
    n = len(y)
    prev = float(y.mean())
    rows = []
    for pt in thresholds:
        pred = p >= pt
        tp = int(np.sum(pred & (y == 1)))
        fp = int(np.sum(pred & (y == 0)))
        odds = pt / (1 - pt)
        rows.append({
            "Threshold_probability": float(pt),
            "Net_benefit_model": float(tp / n - fp / n * odds),
            "Net_benefit_treat_all": float(prev - (1 - prev) * odds),
            "Net_benefit_treat_none": 0.0,
            "TP": tp,
            "FP": fp,
        })
    return rows


def save_calibration(outcome, df, out_dir):
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    for model in ("LR", "RF", "XGBoost"):
        s = df[df.Model == model]
        ax.plot(s.Mean_predicted, s.Observed_fraction, marker="o", label=model)
    lim = max(0.25, 1.05 * max(df.Mean_predicted.max(), df.Observed_fraction.max()))
    ax.plot([0, lim], [0, lim], linestyle="--", label="Perfect calibration")
    ax.set(xlim=(0, lim), ylim=(0, lim), xlabel="Mean predicted probability",
           ylabel="Observed event proportion",
           title=f"NHIS 2024 {outcome} — Calibration (locked test)")
    ax.grid(True, alpha=.25); ax.legend(); fig.tight_layout()
    fig.savefig(out_dir / f"calibration_{outcome}.png", dpi=180)
    fig.savefig(out_dir / f"calibration_{outcome}.svg")
    plt.close(fig)


def save_dca(outcome, df, out_dir):
    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    for model in ("LR", "RF", "XGBoost"):
        s = df[df.Model == model]
        ax.plot(s.Threshold_probability, s.Net_benefit_model, label=model)
    ref = df[df.Model == "LR"]
    ax.plot(ref.Threshold_probability, ref.Net_benefit_treat_all, linestyle="--", label="Treat all")
    ax.plot(ref.Threshold_probability, ref.Net_benefit_treat_none, linestyle=":", label="Treat none")
    ax.set(xlabel="Threshold probability", ylabel="Net benefit",
           title=f"NHIS 2024 {outcome} — Exploratory Decision Curve Analysis")
    ax.grid(True, alpha=.25); ax.legend(); fig.tight_layout()
    fig.savefig(out_dir / f"decision_curve_{outcome}.png", dpi=180)
    fig.savefig(out_dir / f"decision_curve_{outcome}.svg")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT / "modeling" / "day8_10" / "uhs_extensions")
    ap.add_argument("--bootstrap-reps", type=int, default=1000)
    ap.add_argument("--n-jobs", type=int, default=2)
    ap.add_argument("--dca-min", type=float, default=.01)
    ap.add_argument("--dca-max", type=float, default=.30)
    ap.add_argument("--dca-step", type=float, default=.005)
    args = ap.parse_args(); args.out_dir.mkdir(parents=True, exist_ok=True)

    config, selection, locked_perf = load_locked_metadata(REPO_ROOT)
    all_ci, all_cal, all_dca, recomputed = [], [], [], []

    for oi, (outcome, spec) in enumerate(base.OUTCOMES.items()):
        df = pd.read_csv(args.data_dir / spec["file"])
        df["SPLIT"] = df.HHX.map(base.day5_bucket)
        for split, expected in spec["expected"].items():
            m = df.SPLIT.eq(split)
            observed = (int(m.sum()), int(df.loc[m, spec["target"]].sum()))
            if observed != tuple(expected):
                raise RuntimeError(f"{outcome}/{split}: {observed} != {tuple(expected)}")

        X = base.clean_features(df)
        y = df[spec["target"]].astype(int).to_numpy()
        sp = df.SPLIT.to_numpy(); hhx = df.HHX.to_numpy()
        tr, va, te = sp == "train", sp == "validation", sp == "test"
        roles = np.array([base.validation_role(h) for h in hhx[va]])
        cal = roles == "calibration"
        prep = base.make_prep()
        Xtr = prep.fit_transform(X.loc[tr]); Xva = prep.transform(X.loc[va]); Xte = prep.transform(X.loc[te])
        ytr, yva, yte = y[tr], y[va], y[te]

        probs = {}
        for model in ("LR", "RF", "XGBoost"):
            params = config["best_params"][outcome][model]
            if model == "LR": params = {"C": 1.0}
            est = build_locked_model(model, params, args.n_jobs); est.fit(Xtr, ytr)
            pcal = est.predict_proba(Xva[cal])[:, 1]
            ptest = est.predict_proba(Xte)[:, 1]
            sel = selection[(selection.Outcome == outcome) & (selection.Model == model)].iloc[0]
            if sel.Selected_probability == "Platt":
                ptest = base.PlattScaler().fit(pcal, yva[cal]).transform(ptest)
            probs[model] = ptest

            threshold = float(sel.Threshold)
            perf = base.evaluate(yte, ptest, threshold)
            ref = locked_perf[(locked_perf.Outcome == outcome) & (locked_perf.Model == model)].iloc[0]
            for metric in ("AUROC", "AUPRC", "Brier"):
                if abs(perf[metric] - float(ref[metric])) > 5e-10:
                    raise RuntimeError(f"Locked metric mismatch: {outcome}/{model}/{metric}")
            recomputed.append({"Outcome": outcome, "Model": model,
                               "Selected_probability": sel.Selected_probability,
                               "Threshold": threshold, **perf})
            for r in calibration_bins(yte, ptest):
                all_cal.append({"Outcome": outcome, "Model": model,
                                "Selected_probability": sel.Selected_probability, **r})

        auc_bs, ap_bs = paired_bootstrap(yte, probs, args.bootstrap_reps, BOOTSTRAP_SEED + oi)
        for model in probs:
            a = roc_auc_score(yte, probs[model]); p = average_precision_score(yte, probs[model])
            alo, ahi = np.quantile(auc_bs[model], [.025, .975]); plo, phi = np.quantile(ap_bs[model], [.025, .975])
            all_ci.append({"Outcome": outcome, "Model": model, "AUROC": a,
                           "AUROC_CI95_Lower": alo, "AUROC_CI95_Upper": ahi,
                           "AUPRC": p, "AUPRC_CI95_Lower": plo, "AUPRC_CI95_Upper": phi,
                           "Bootstrap_reps": args.bootstrap_reps,
                           "Bootstrap_seed": BOOTSTRAP_SEED + oi,
                           "Survey_design_CI": False})

        grid = np.arange(args.dca_min, args.dca_max + args.dca_step/2, args.dca_step)
        for model, p in probs.items():
            selp = selection[(selection.Outcome == outcome) & (selection.Model == model)].iloc[0].Selected_probability
            for r in decision_curve(yte, p, grid):
                all_dca.append({"Outcome": outcome, "Model": model, "Selected_probability": selp, **r})

    ci = pd.DataFrame(all_ci); cal = pd.DataFrame(all_cal); dca = pd.DataFrame(all_dca); perf = pd.DataFrame(recomputed)
    evidence = perf.merge(ci[["Outcome","Model","AUROC_CI95_Lower","AUROC_CI95_Upper","AUPRC_CI95_Lower","AUPRC_CI95_Upper"]], on=["Outcome","Model"])
    evidence = evidence.sort_values(["Outcome","AUPRC"], ascending=[True,False])
    common = dca[dca.Threshold_probability.round(3).isin([.05,.10,.15,.20,.25,.30])]

    ci.to_csv(args.out_dir / "day8_10_auroc_auprc_bootstrap_ci.csv", index=False)
    cal.to_csv(args.out_dir / "day8_10_calibration_selected.csv", index=False)
    dca.to_csv(args.out_dir / "day8_10_dca_values.csv", index=False)
    common.to_csv(args.out_dir / "day8_10_dca_common_threshold_summary.csv", index=False)
    evidence.to_csv(args.out_dir / "day8_10_model_selection_evidence_table.csv", index=False)
    for outcome in base.OUTCOMES:
        save_calibration(outcome, cal[cal.Outcome == outcome], args.out_dir)
        save_dca(outcome, dca[dca.Outcome == outcome], args.out_dir)

    ext_config = {
        "status": "DAY8_10_UHS_METRIC_EXTENSION_COMPLETE",
        "bootstrap": {"method": "nonparametric paired bootstrap of locked-test rows",
                      "reps": args.bootstrap_reps, "seed_base": BOOTSTRAP_SEED,
                      "ci": "percentile 2.5th/97.5th", "survey_design_based": False},
        "calibration": "locked selected probability; 10 equal-frequency test bins; evaluation only",
        "dca": {"threshold_min": args.dca_min, "threshold_max": args.dca_max,
                "threshold_step": args.dca_step, "status": "exploratory",
                "action_frame": "hypothetical risk-based outreach/prioritization"},
        "test_policy": "evaluation extension only; no further tuning on same test split",
    }
    (args.out_dir / "day8_10_uhs_extension_config.json").write_text(json.dumps(ext_config, indent=2), encoding="utf-8")
    print(evidence.to_string(index=False))


if __name__ == "__main__":
    main()
