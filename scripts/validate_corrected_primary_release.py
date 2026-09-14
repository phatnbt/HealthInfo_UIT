from pathlib import Path
import hashlib,json,os,platform,sys,subprocess
from datetime import datetime,timezone
import numpy as np
import pandas as pd
import xgboost

def main():
    folder=Path('modeling/day14_16_corrected_linux');audit=pd.read_csv(folder/'day14_16_locked_reproduction_audit.csv')
    assert len(audit)==6 and audit.Status.eq('PASS').all()
    assert audit.Max_absolute_metric_difference.le(1e-8).all()
    assert audit.loc[audit.Model.eq('XGBoost'),'SHAP_additivity_max_residual'].le(3e-5).all()
    cfg=json.loads((folder/'day14_16_config_log.json').read_text())
    assert cfg['n_explained']=={'MEDNG':6417,'MEDDL':6419}
    global_shap=pd.read_csv(folder/'day14_16_shap_global_importance.csv')
    assert len(global_shap)==144 and global_shap.groupby(['Outcome','Model','Aggregation']).Feature_construct.nunique().eq(12).all()
    for path in folder.rglob('*.csv'):
        assert not {'HHX','y_true','pred_prob'}.intersection(pd.read_csv(path,nrows=0).columns)
    native=hashlib.sha256(Path(xgboost.core._LIB._name).read_bytes()).hexdigest()
    assert native=='0a3db9e83649ac38711e12a09519070e8b215b1255b735c78b05ad333b63be53'
    summary={'created_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_REPRODUCED_PRIMARY_SPARSE_CORRECT_FULL_SHAP','source_commit':os.environ.get('GITHUB_SHA'),'run_url':'https://github.com/phatnbt/HealthInfo_UIT/actions/runs/'+os.environ.get('GITHUB_RUN_ID',''),'platform':platform.platform(),'python':sys.version,'native_xgboost_SHA256':native,'full_test_N':cfg['n_explained'],'reproduction_rows':6,'maximum_historical_metric_drift':float(audit.Max_absoluteMetric_difference.max()) if 'Max_absoluteMetric_difference' in audit else float(audit.Max_absolute_metric_difference.max()),'XGB_SHAP_max_additivity_residual':float(audit.loc[audit.Model.eq('XGBoost'),'SHAP_additivity_max_residual'].max()),'interpretation':'Corrected full-test native CSR explanation of reproducible historical primary estimators; old XGB SHAP is superseded. No parameter, split, threshold or calibration choice changed.'}
    out=Path('repair/linux_verified');out.mkdir(parents=True,exist_ok=True)
    (out/'corrected_primary_validation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
