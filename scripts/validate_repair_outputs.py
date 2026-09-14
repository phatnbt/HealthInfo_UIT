"""Validate new repair evidence independently of historical integrity gates."""
from pathlib import Path
import argparse,hashlib,json,platform,sys,zipfile
from datetime import datetime,timezone
import numpy as np
import pandas as pd


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--require-historical-match',action='store_true')
    args=parser.parse_args();repo=Path(__file__).resolve().parents[1]
    freeze=pd.read_csv(repo/'modeling/day20_22/day22_code_freeze_manifest.csv')
    for row in freeze.to_dict('records'):
        b=(repo/row['Relative_path']).read_bytes()
        assert len(b)==row['Size_bytes'] and hashlib.sha256(b).hexdigest()==row['SHA256']
    with zipfile.ZipFile(repo/'literature/NHIS2024_Day6_Literature_Matrix_18.xlsx') as z:assert z.testzip() is None
    mi=args.results/'poverty_mi';performance=pd.read_csv(mi/'poverty_mi_per_imputation_performance.csv')
    keys=['Outcome','Model','Training_weighting','Evaluation_weighting','IMPNUM_A']
    assert len(performance)==240 and not performance.duplicated(keys).any()
    assert performance.groupby(keys[:-1]).IMPNUM_A.apply(lambda s:set(s)==set(range(1,11))).all()
    for column in ['AUROC','AUPRC','Brier','Recall','Precision','F1','Specificity']:assert performance[column].between(0,1).all()
    sf=pd.read_csv(mi/'poverty_mi_shap_per_imputation.csv');quality=pd.read_csv(mi/'poverty_mi_shap_quality_audit.csv')
    assert len(sf)==2880 and len(quality)==120
    assert sf.groupby(['Outcome','Model','Training_weighting','Aggregation','Construct']).IMPNUM_A.nunique().eq(10).all()
    assert quality.groupby('Outcome').Sample_SHA256.nunique().eq(1).all()
    assert quality.Additivity_passed.all() and quality.Additivity_max_absolute_residual.le(3e-5).all()
    assert sf.Mean_absolute_SHAP.ge(0).all() and sf.Explained_N.eq(128).all()
    assert np.allclose(sf.groupby(['Outcome','Model','Training_weighting','Aggregation','IMPNUM_A']).Importance_share.sum(),1,atol=1e-6)
    survey=pd.read_csv(args.results/'survey_prevalence/Korn_Graubard_companion.csv')
    assert len(survey)==76 and survey.Domain_variable.eq('Overall').sum()==2
    assert (survey.KG_CI95_lower<=survey.Weighted_prevalence).all() and (survey.Weighted_prevalence<=survey.KG_CI95_upper).all()
    assert survey.KG_CI95_lower.between(0,1).all() and survey.KG_CI95_upper.between(0,1).all()
    for path in args.results.rglob('*.csv'):
        columns=pd.read_csv(path,nrows=0).columns
        assert not {'HHX','y_true','pred_prob','TARGET_FORGONE_COST','TARGET_DELAYED_COST'}.intersection(columns),str(path)
    drift=pd.read_csv(mi/'historical_runtime_drift_audit.csv');metrics=[c for c in drift if c.endswith('_difference')]
    maxima=drift.groupby('Model')[metrics].agg(lambda v:v.abs().max()).max(axis=1).to_dict()
    status={m:('PASS' if value<=1e-8 else 'FAIL') for m,value in maxima.items()}
    native=None
    import xgboost
    native=hashlib.sha256(Path(xgboost.core._LIB._name).read_bytes()).hexdigest()
    summary={'created_utc':datetime.now(timezone.utc).isoformat(),'artifact_integrity':'PASS','historical_reproduction_by_model':status,'historical_max_difference_by_model':maxima,'historical_all_models_passed':all(s=='PASS' for s in status.values()),'MI_performance_rows':240,'MI_SHAP_rows':2880,'MI_SHAP_additivity_audit_rows':120,'SHAP_max_additivity_residual':float(quality.Additivity_max_absolute_residual.max()),'legacy_sparse_dense_XGB_probability_max_difference':float(quality.Legacy_sparse_to_dense_probability_max_difference.max()),'KG_total_rows':76,'KG_subgroup_rows':74,'freeze_rows_unchanged':30,'platform':platform.platform(),'python':sys.version,'native_xgboost_SHA256':native,'status_boundary':'Artifact PASS does not imply all historical models reproduced or UHS approval.'}
    (args.results/'repair_validation_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    if args.require_historical_match and not summary['historical_all_models_passed']:raise SystemExit(2)


if __name__=='__main__':main()
