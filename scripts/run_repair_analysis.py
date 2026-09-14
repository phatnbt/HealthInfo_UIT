"""Reproduce added Repair v2 aggregate sensitivity results; no person-level export."""
from pathlib import Path
import argparse, hashlib, importlib.metadata, io, json, platform, sys, zipfile
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from scipy.stats import beta, f, t
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def kg(n, p, se, df):
    if not (n > 1 and 0 < p < 1 and se > 0 and df > 0):
        raise ValueError('This companion implementation requires interior proportions and positive Taylor SE/df.')
    effective = min(n, p * (1-p) / se**2)
    adjusted = min(n, effective * (t.ppf(.975, n-1) / t.ppf(.975, df))**2)
    x = adjusted*p
    lo = float(beta.ppf(.025, x, adjusted-x+1))
    hi = float(beta.ppf(.975, x+1, adjusted-x))
    # Independent equivalent F-distribution formulation in Ward (2019), eqs 4-9.
    v1, v2, v3, v4 = 2*x, 2*(adjusted-x+1), 2*(x+1), 2*(adjusted-x)
    fl, fu = f.ppf(.025,v1,v2), f.ppf(.975,v3,v4)
    assert np.allclose([lo,hi],[v1*fl/(v2+v1*fl),v3*fu/(v4+v3*fu)],atol=1e-12,rtol=0)
    width = hi-lo
    reliable = n>=30 and effective>=30 and width<.30 and (width<=.05 or width/p<=1.30)
    complement = n>=30 and effective>=30 and width<.30 and (width<=.05 or width/(1-p)<=1.30)
    review = width<=.05 and df<8
    return dict(Effective_N=effective,DF_adjusted_effective_N=adjusted,
                KG_CI95_lower=lo,KG_CI95_upper=hi,Absolute_CI_width=width,
                Relative_CI_width_percent=100*width/p,
                Complement_relative_CI_width_percent=100*width/(1-p),
                Meets_size_and_width_criteria=bool(reliable),Requires_statistical_review=bool(review),
                Complement_meets_size_and_width_criteria=bool(complement))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference-dir',type=Path,required=True)
    parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--adult-zip',type=Path)
    parser.add_argument('--income-zip',type=Path)
    parser.add_argument('--n-jobs',type=int,default=4)
    parser.add_argument('--kg-only',action='store_true')
    parser.add_argument('--include-shap',action='store_true')
    parser.add_argument('--shap-sample-size',type=int,default=128,help='Fixed test sample per outcome, reused for all imputation/model/weighting arms.')
    args=parser.parse_args()
    out=args.out_dir; out.mkdir(parents=True,exist_ok=True)
    survey=out/'survey_prevalence'; survey.mkdir(exist_ok=True)
    original=pd.read_csv(args.reference_dir/'modeling/day11_13/day11_13_weighted_outcome_prevalence.csv')
    companion=[]
    for r in original.to_dict('records'):
        companion.append({**r,**kg(r['Domain_N'],r['Weighted_prevalence'],r['Taylor_SE'],r['Design_df'])})
    pd.DataFrame(companion).to_csv(survey/'Korn_Graubard_companion.csv',index=False)
    print('KG companion: 2 overall outcome rows; Beta/F formula agreement passed.',flush=True)
    if args.kg_only: return
    if importlib.metadata.version('xgboost') != '3.0.4':
        raise RuntimeError('Use locked xgboost==3.0.4 from requirements.txt before running MI.')
    sys.path.insert(0,str(args.reference_dir/'scripts'))
    import day8_10_modeling as locked
    if locked.XGBClassifier.__module__.split('.')[0] != 'xgboost':
        raise RuntimeError('Unexpected XGBoost implementation.')
    import xgboost
    if xgboost.__version__ != '3.0.4':
        raise RuntimeError('Imported XGBoost runtime must actually be 3.0.4.')
    from day11_13_survey_sensitivity import build_locked_model, evaluate, WeightedPlattScaler, normalize_training_weights
    if not args.adult_zip or not args.income_zip: raise ValueError('Both official raw ZIP inputs are required for MI.')
    raw={}
    for p,member,expected in [(args.adult_zip,'adult24.csv','6b0d5e572841ffef7b0f7df4ddfed556'),
                              (args.income_zip,'adultinc24.csv','14a1d5780100c1b0a13acce433e00360')]:
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            data=z.read(member)
        assert hashlib.md5(data).hexdigest()==expected,member+' input checksum mismatch'
        raw[member]=data
    adult=pd.read_csv(io.BytesIO(raw['adult24.csv']),dtype={'HHX':str})
    income=pd.read_csv(io.BytesIO(raw['adultinc24.csv']),dtype={'HHX':str})
    assert len(adult)==32629 and len(income)==326290
    assert adult.HHX.is_unique and not income.duplicated(['HHX','IMPNUM_A']).any()
    assert set(income.IMPNUM_A.unique())==set(range(1,11))
    assert income.groupby('HHX').size().eq(10).all()
    assert set(income.HHX)==set(adult.HHX)
    assert income.POVRATTC_A.between(0,11).all()
    domains=[['HYPEV_A'],['CHDEV_A','ANGEV_A','MIEV_A','STREV_A'],['ASEV_A'],['COPDEV_A'],
             ['CANEV_A'],['DIBEV_A'],['ARTHEV_A'],['KIDWEAKEV_A']]
    condition=[]
    for cols in domains:
        c=adult[cols]
        condition.append(np.where(c.eq(1).any(axis=1),1,np.where(c.eq(2).all(axis=1),0,np.nan)))
    count=np.array(condition).sum(axis=0)
    adult['CHRONIC_BURDEN_CAT']=[np.nan if np.isnan(v) else '0' if v==0 else '1' if v==1 else '2' if v==2 else '3+' for v in count]
    adult['SPLIT']=adult.HHX.map(locked.day5_bucket)
    cfg=json.loads((args.reference_dir/'modeling/day8_10/day8_10_config_log.json').read_text())
    selected=pd.read_csv(args.reference_dir/'modeling/day8_10/day8_10_validation_selection.csv').set_index(['Outcome','Model'])
    mi=out/'poverty_mi'; mi.mkdir(exist_ok=True)
    performances=[]; audit=[]; baselines=[]; shap_rows=[]; shap_audit=[]
    if args.include_shap:
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from mi_explainability import explain
        if args.shap_sample_size<30: raise ValueError('Use at least 30 explained records.')
    for outcome,spec in locked.OUTCOMES.items():
        cohort=adult.loc[adult[outcome+'12M_A'].isin([1,2])].copy().reset_index(drop=True)
        cohort[spec['target']]=cohort[outcome+'12M_A'].eq(1).astype(int)
        observed={s:(int(cohort.SPLIT.eq(s).sum()),int(cohort.loc[cohort.SPLIT.eq(s),spec['target']].sum())) for s in ['train','validation','test']}
        assert observed==spec['expected'],(outcome,observed)
        tr=cohort.SPLIT.eq('train').to_numpy(); va=cohort.SPLIT.eq('validation').to_numpy(); te=cohort.SPLIT.eq('test').to_numpy()
        y=cohort[spec['target']].to_numpy(); w=cohort.WTFA_A.to_numpy(float)
        cal=va & cohort.HHX.map(locked.validation_role).eq('calibration').to_numpy()
        assert not np.any(tr&cal) and not np.any(te&cal)
        clean=locked.clean_features(cohort)
        explain_indices=np.sort(np.random.default_rng(2026+1000*list(locked.OUTCOMES).index(outcome)).choice(int(te.sum()),min(args.shap_sample_size,int(te.sum())),replace=False))
        sample_hash=hashlib.sha256('\n'.join(cohort.loc[te,'HHX'].iloc[explain_indices]).encode()).hexdigest()
        split_hash=hashlib.sha256('\n'.join(cohort.HHX.astype(str)+'|'+cohort.SPLIT).encode()).hexdigest()
        for imp in range(0,11):
            X=clean.copy()
            if imp:
                ratio=income.loc[income.IMPNUM_A.eq(imp)].set_index('HHX').POVRATTC_A.reindex(cohort.HHX).to_numpy(float)
                assert not np.isnan(ratio).any()
                X=X.drop(columns='RATCAT_A'); X['POVRATTC_A']=ratio
                nums=['AGEP_A','POVRATTC_A']; cats=[c for c in locked.CAT if c!='RATCAT_A']
                prep=ColumnTransformer([
                    ('num',Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler())]),nums),
                    ('cat',Pipeline([('imputer',SimpleImputer(strategy='constant',fill_value='Missing')),('ohe',OneHotEncoder(handle_unknown='ignore',sparse_output=True))]),cats)])
            else: prep=locked.make_prep()
            train=prep.fit_transform(X.loc[tr]); calibration=prep.transform(X.loc[cal]); test=prep.transform(X.loc[te])
            for name in ['LR','RF','XGBoost']:
                params=cfg['best_params'][outcome][name]
                if name=='LR': params={'C':1.0}
                decision=selected.loc[(outcome,name)]
                threshold=float(decision.Threshold); probkind=str(decision.Selected_probability)
                for training in ['Unweighted','WTFA_A']:
                    model=build_locked_model(name,params,args.n_jobs)
                    kw={'sample_weight':normalize_training_weights(w[tr])} if training=='WTFA_A' else {}
                    model.fit(train,y[tr],**kw)
                    if imp and args.include_shap:
                        constructs=[c for c in locked.MAIN if c!='RATCAT_A']+['POVRATTC_A']
                        rows,quality=explain(model,name,train,test,list(prep.get_feature_names_out()),constructs,explain_indices,w[te],2026+1000*list(locked.OUTCOMES).index(outcome))
                        arm=dict(Outcome=outcome,Model=name,Training_weighting=training,IMPNUM_A=imp)
                        shap_rows.extend({**arm,**row} for row in rows)
                        shap_audit.append({**arm,**quality,'Sample_SHA256':sample_hash})
                        pd.DataFrame(shap_rows).to_csv(mi/'poverty_mi_shap_per_imputation.csv',index=False)
                        pd.DataFrame(shap_audit).to_csv(mi/'poverty_mi_shap_quality_audit.csv',index=False)
                    p=model.predict_proba(test)[:,1]
                    if probkind=='Platt':
                        cw=normalize_training_weights(w[cal]) if training=='WTFA_A' else None
                        scaler=WeightedPlattScaler().fit(model.predict_proba(calibration)[:,1],y[cal],sample_weight=cw)
                        p=scaler.transform(p)
                    assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
                    for weighting,ew in [('Unweighted',None),('WTFA_A',w[te])]:
                        row=dict(Outcome=outcome,Model=name,Training_weighting=training,Evaluation_weighting=weighting,
                                 IMPNUM_A=imp,Probability_version=probkind,Locked_threshold=threshold,
                                 **evaluate(y[te],p,threshold,sample_weight=ew))
                        (performances if imp else baselines).append(row)
            if imp:
                audit.append(dict(Outcome=outcome,IMPNUM_A=imp,Cohort_N=len(cohort),
                                  Train_N=int(tr.sum()),Calibration_N=int(cal.sum()),Test_N=int(te.sum()),
                                  Cohort_split_SHA256=split_hash,POVRATTC_min=float(ratio.min()),POVRATTC_max=float(ratio.max()),
                                  Same_cohort_and_split=True,Income_merge_complete=True))
            pd.DataFrame(performances).to_csv(mi/'poverty_mi_per_imputation_performance.csv',index=False)
            print(outcome,'baseline' if imp==0 else f'imputation {imp}/10','complete',flush=True)
    if args.include_shap:
        assert len(shap_rows)==2880 and len(shap_audit)==120
        sf=pd.DataFrame(shap_rows)
        keys_shap=['Outcome','Model','Training_weighting','Aggregation','Construct','Explained_output']
        assert sf.groupby(keys_shap).IMPNUM_A.nunique().eq(10).all()
        summary_shap=sf.groupby(keys_shap).agg(Mean_absolute_SHAP_mean=('Mean_absolute_SHAP','mean'),Mean_absolute_SHAP_SD=('Mean_absolute_SHAP','std'),Mean_absolute_SHAP_min=('Mean_absolute_SHAP','min'),Mean_absolute_SHAP_max=('Mean_absolute_SHAP','max'),Rank_mean=('Rank','mean'),Rank_min=('Rank','min'),Rank_max=('Rank','max'),Imputations=('IMPNUM_A','nunique')).reset_index()
        summary_shap.to_csv(mi/'poverty_mi_shap_sensitivity_summary.csv',index=False)
    performance=pd.DataFrame(performances); baseline=pd.DataFrame(baselines)
    assert len(performance)==240 and len(audit)==20 and len(baseline)==24
    keys=['Outcome','Model','Training_weighting','Evaluation_weighting']
    assert performance.groupby(keys).IMPNUM_A.nunique().eq(10).all()
    metrics=['AUROC','AUPRC','Brier','Recall','Precision','F1','Specificity']
    long=performance.melt(id_vars=keys+['IMPNUM_A'],value_vars=metrics,var_name='Metric',value_name='Value')
    aggregate=long.groupby(keys+['Metric']).Value.agg(['mean','std','min','max','count']).reset_index()
    aggregate.to_csv(mi/'poverty_mi_sensitivity_summary.csv',index=False)
    baseline.to_csv(mi/'RATCAT_same_environment_reference.csv',index=False)
    b=baseline.melt(id_vars=keys,value_vars=metrics,var_name='Metric',value_name='RATCAT_reference')
    delta=aggregate.merge(b,on=keys+['Metric'],validate='one_to_one')
    delta['Mean_minus_RATCAT']=delta['mean']-delta.RATCAT_reference
    delta.to_csv(mi/'poverty_mi_deltas_vs_RATCAT.csv',index=False)
    pd.DataFrame(audit).to_csv(mi/'poverty_mi_cohort_split_audit.csv',index=False)
    historic=pd.read_csv(args.reference_dir/'modeling/day11_13/day11_13_weighted_model_sensitivity.csv')
    drift=baseline.merge(historic,on=keys,suffixes=('_rerun','_historical'),validate='one_to_one')
    for m in metrics: drift[m+'_difference']=drift[m+'_rerun']-drift[m+'_historical']
    drift[keys+[m+'_difference' for m in metrics]].to_csv(mi/'historical_runtime_drift_audit.csv',index=False)
    runtime={n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','xgboost']}
    runtime['xgboost']=xgboost.__version__
    log=dict(status='COMPLETE_NEW_AGGREGATE_SENSITIVITY',created_utc=datetime.now(timezone.utc).isoformat(),
             python=sys.version.split()[0],runtime_versions=runtime,n_jobs=args.n_jobs,
             platform=platform.platform(),python_isolated_mode=bool(sys.flags.isolated),
             xgboost_build_info=xgboost.build_info(),performance_rows=240,imputations=10,
             outcomes=['MEDNG','MEDDL'],models=['LR','RF','XGBoost'],seed=2026,
             features='Replace RATCAT_A with continuous POVRATTC_A; 12 constructs; train-only preprocessing.',
             protocol='Reuse locked model parameters, probability choice and threshold. Refit selected Platt mapping on calibration-role validation only for each model/imputation; no retuning or test-based selection.',
             summaries='Mean, SD, min, max over imputations; not Rubin-pooled confidence intervals.',
             explanation_scope=('Performance and aggregate construct SHAP across ten imputations; deterministic test sample, base estimator output, no Platt probability explanation, no pooled inference.' if args.include_shap else 'Performance only; SHAP not performed.'),
             shap_sample_size=args.shap_sample_size if args.include_shap else None,shap_rows=len(shap_rows),shap_audit_rows=len(shap_audit),
             comparison='RATCAT reference rerun in the same environment. Historical-runtime drift audit supplied; no assertion of exact reproduction of all historical models.',
             raw_input_md5={n:hashlib.md5(d).hexdigest() for n,d in raw.items()},
             validation=dict(raw_checksums=True,raw_counts=True,income_unique_keys=True,all_ten_imputations=True,
                             income_coverage=True,locked_cohort_split_counts=True,per_arm_ten_runs=True,
                             no_person_level_export=True,beta_F_KG_agreement=True))
    maximum=float(drift[[m+'_difference' for m in metrics]].abs().max().max())
    log['historical_reproduction']=dict(max_absolute_metric_difference=maximum,tolerance=1e-8,
                                        passed=maximum<=1e-8,policy='Investigate discrepancies before integrating new results into historical primary claims.')
    (mi/'poverty_mi_run_config.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Completed 132 fits; 240 MI rows; 24 same-environment reference rows.',flush=True)


if __name__=='__main__': main()
