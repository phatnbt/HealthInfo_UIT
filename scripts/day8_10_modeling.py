import os
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold, RandomizedSearchCV
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    roc_auc_score, average_precision_score, recall_score, precision_score,
    f1_score, brier_score_loss, confusion_matrix
)
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
import warnings
warnings.filterwarnings('ignore')

RANDOM_SEED = 2026
DATA_PATH = r"E:\HealthInfo\NHIS2024_Day4_POST_UHS_FINAL_PACKAGE\analysis_ready_MEDNG_FINAL_FEATURELOCK_RAWCODES.csv"
TARGET = "TARGET_FORGONE_COST"
GROUP_COL = "HHX"
WEIGHT_COL = "WTFA_A"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"KHÔNG TÌM THẤY FILE GỐC TỪ DAY 4: {DATA_PATH}")

MAIN = ['AGEP_A', 'SEX_A', 'HISPALLP_A', 'EDUCP_A', 'RATCAT_A', 'EMPWRKLSW1_A', 
        'NOTCOV_A', 'FDSCAT3_A', 'PHSTAT_A', 'DISAB3_A', 'K6SPD_A', 'CHRONIC_BURDEN_CAT']
NUM = ['AGEP_A']
CAT = [c for c in MAIN if c not in NUM]

# Định nghĩa từ Day 5
SPECIAL = {
    'AGEP_A': {97,98,99},
    'SEX_A': {7,8,9},
    'HISPALLP_A': {97,98,99},
    'EDUCP_A': {97,98,99},
    'RATCAT_A': {98},
    'EMPWRKLSW1_A': {7,8,9},
    'NOTCOV_A': {7,8,9},
    'FDSCAT3_A': {8},
    'PHSTAT_A': {7,8,9},
    'DISAB3_A': {9},
    'K6SPD_A': {8}
}

def bucket(h):
    x = int(hashlib.sha256((f'NHIS2024_DAY5|{h}').encode()).hexdigest()[:12], 16) % 10
    return 'test' if x in (0,1) else ('validation' if x == 2 else 'train')

def clean(df):
    x = df[MAIN].copy()
    for c, vals in SPECIAL.items():
        x[c] = pd.to_numeric(x[c], errors='coerce')
        x.loc[x[c].isin(vals), c] = np.nan
    for c in CAT:
        if c == 'CHRONIC_BURDEN_CAT':
            x[c] = x[c].where(x[c].notna(), 'Missing/indeterminate').astype(str)
        else:
            x[c] = x[c].map(lambda v: np.nan if pd.isna(v) else str(int(v)) if float(v).is_integer() else str(v))
    return x

def make_prep():
    return ColumnTransformer([
        ('num', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scale', StandardScaler())
        ]), NUM),
        ('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
            ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ]), CAT)
    ])

print("1. Đang nạp dữ liệu và tiến hành chia Split...")
df = pd.read_csv(DATA_PATH)
df['SPLIT'] = df.HHX.map(bucket)

# Áp dụng clean trước khi nạp vào pipeline
X_cleaned = clean(df)
y = df[TARGET].astype(int).to_numpy()
w = df[WEIGHT_COL].astype(float).to_numpy()
sp = df['SPLIT'].to_numpy()
hhx = df[GROUP_COL].to_numpy()

X_train, y_train, w_train, hhx_train = X_cleaned[sp == 'train'], y[sp == 'train'], w[sp == 'train'], hhx[sp == 'train']
X_val, y_val, w_val, hhx_val = X_cleaned[sp == 'validation'], y[sp == 'validation'], w[sp == 'validation'], hhx[sp == 'validation']
X_test, y_test, w_test, hhx_test = X_cleaned[sp == 'test'], y[sp == 'test'], w[sp == 'test'], hhx[sp == 'test']

print(f"Train: {len(y_train)} | Val: {len(y_val)} | Test: {len(y_test)}")

print("2. Đang cấu hình Tuning Pipelines...")
group_kfold = GroupKFold(n_splits=5)

# Định nghĩa các Pipeline với prep__ được GIỮ NGUYÊN
rf_pipeline = Pipeline([
    ('prep', make_prep()),
    ('clf', RandomForestClassifier(random_state=RANDOM_SEED, class_weight=None, n_jobs=-1))
])
rf_param_grid = {
    "clf__n_estimators": [300, 500, 800],
    "clf__max_depth": [4, 6, 8, None],
    "clf__min_samples_leaf": [1, 5, 10, 20],
    "clf__max_features": ["sqrt", "log2"],
}

xgb_pipeline = Pipeline([
    ('prep', make_prep()),
    ('clf', xgb.XGBClassifier(random_state=RANDOM_SEED, eval_metric="aucpr", use_label_encoder=False, n_jobs=-1))
])
xgb_param_grid = {
    "clf__n_estimators": [200, 400, 600],
    "clf__max_depth": [3, 4, 5, 6],
    "clf__learning_rate": [0.01, 0.05, 0.1],
    "clf__subsample": [0.7, 0.85, 1.0],
    "clf__colsample_bytree": [0.7, 0.85, 1.0],
}

print("3. Đang tiến hành Tuning (RandomizedSearchCV) KHÔNG dùng Sample Weight...")
rf_search = RandomizedSearchCV(
    rf_pipeline, rf_param_grid, n_iter=20, scoring="average_precision",
    cv=group_kfold.split(X_train, y_train, hhx_train),
    random_state=RANDOM_SEED, n_jobs=-1
)
rf_search.fit(X_train, y_train)

xgb_search = RandomizedSearchCV(
    xgb_pipeline, xgb_param_grid, n_iter=25, scoring="average_precision",
    cv=group_kfold.split(X_train, y_train, hhx_train),
    random_state=RANDOM_SEED, n_jobs=-1
)
xgb_search.fit(X_train, y_train)

lr_unweighted = Pipeline([
    ('prep', make_prep()),
    ('clf', LogisticRegression(max_iter=2000, solver='lbfgs', C=1.0, random_state=RANDOM_SEED))
])
lr_unweighted.fit(X_train, y_train)

print("4. Đang tiến hành Fit lại các best parameters VỚI Sample Weight (WTFA_A)...")
# Normalize train weights to mean 1 as in Day 5
w_train_norm = w_train / w_train.mean()

rf_weighted = Pipeline([
    ('prep', make_prep()),
    ('clf', RandomForestClassifier(**rf_search.best_estimator_.named_steps['clf'].get_params()))
])
rf_weighted.fit(X_train, y_train, clf__sample_weight=w_train_norm)

xgb_weighted = Pipeline([
    ('prep', make_prep()),
    ('clf', xgb.XGBClassifier(**xgb_search.best_estimator_.named_steps['clf'].get_params()))
])
xgb_weighted.fit(X_train, y_train, clf__sample_weight=w_train_norm)

lr_weighted = Pipeline([
    ('prep', make_prep()),
    ('clf', LogisticRegression(max_iter=2000, solver='lbfgs', C=1.0, random_state=RANDOM_SEED))
])
lr_weighted.fit(X_train, y_train, clf__sample_weight=w_train_norm)

models = {
    "LogisticRegression_unweighted": lr_unweighted,
    "RandomForest_unweighted": rf_search.best_estimator_,
    "XGBoost_unweighted": xgb_search.best_estimator_,
    "LogisticRegression_weighted": lr_weighted,
    "RandomForest_weighted": rf_weighted,
    "XGBoost_weighted": xgb_weighted,
}

print("5. Đang chọn Threshold trên tập Validation bằng F1-score...")
def best_threshold_by_f1(model, X_v, y_v):
    probs = model.predict_proba(X_v)[:, 1]
    thresholds = np.linspace(0.05, 0.95, 91)
    f1s = [f1_score(y_v, probs >= t, zero_division=0) for t in thresholds]
    return thresholds[int(np.argmax(f1s))]

thresholds = {name: best_threshold_by_f1(m, X_val, y_val) for name, m in models.items()}

print("6. Đang đánh giá đầy đủ trên tập Test...")
def specificity_score(y_true, y_pred, sample_weight=None):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0,1], sample_weight=sample_weight).ravel()
    return tn / (tn + fp) if (tn + fp) else np.nan

results = []
calibration_records = []
w_test_norm = w_test # Không normalize trên tập đánh giá theo nguyên tắc population, hoặc cứ dùng w_test gốc.
# Day 5 eval code: ew = w[te]. metrics calculation passes it as sample_weight=w[te]

for name, m in models.items():
    is_weighted = "weighted" in name and "unweighted" not in name
    eval_w = w_test if is_weighted else None
    
    probs = m.predict_proba(X_test)[:, 1]
    thr = thresholds[name]
    preds = (probs >= thr).astype(int)

    results.append({
        "Model": name,
        "Threshold": round(thr, 3),
        "AUROC": round(roc_auc_score(y_test, probs, sample_weight=eval_w), 4),
        "AUPRC": round(average_precision_score(y_test, probs, sample_weight=eval_w), 4),
        "Recall": round(recall_score(y_test, preds, sample_weight=eval_w, zero_division=0), 4),
        "Precision": round(precision_score(y_test, preds, sample_weight=eval_w, zero_division=0), 4),
        "F1": round(f1_score(y_test, preds, sample_weight=eval_w, zero_division=0), 4),
        "Specificity": round(specificity_score(y_test, preds, sample_weight=eval_w), 4),
        "Brier": round(brier_score_loss(y_test, probs, sample_weight=eval_w), 4),
    })

    # Calibration sơ bộ (unweighted)
    frac_pos, mean_pred = calibration_curve(y_test, probs, n_bins=10, strategy="quantile")
    for fp, mp in zip(frac_pos, mean_pred):
        calibration_records.append({"model": name, "mean_predicted": mp, "fraction_positive": fp})

# Lấy thư mục của script hiện tại làm nơi lưu output (E:\HealthInfo_UIT\scripts) hoặc để ở root
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(OUT_DIR, '..', 'NHIS2024_Day8_10_OUTPUT')
os.makedirs(OUT_DIR, exist_ok=True)

results_df = pd.DataFrame(results).sort_values("AUPRC", ascending=False)
results_df.to_csv(os.path.join(OUT_DIR, "day8_10_model_performance.csv"), index=False)
pd.DataFrame(calibration_records).to_csv(os.path.join(OUT_DIR, "day8_10_calibration_points.csv"), index=False)

print("\n--- PERFORMANCE SUMMARY ---")
print(results_df.to_string(index=False))

config_log = {
    "random_seed": RANDOM_SEED,
    "target": TARGET,
    "features": MAIN,
    "best_params": {
        "RandomForest": rf_search.best_params_,
        "XGBoost": xgb_search.best_params_,
    },
    "thresholds": thresholds,
    "cv_strategy": "GroupKFold(5) theo HHX",
}
with open(os.path.join(OUT_DIR, "day8_10_config_log.json"), "w") as f:
    json.dump(config_log, f, indent=2, default=str)

print(f"\nĐã lưu thành công các file output Day 8-10 tại: {OUT_DIR}")
