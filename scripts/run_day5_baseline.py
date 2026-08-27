import pandas as pd, numpy as np, hashlib, json, warnings
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score, brier_score_loss, confusion_matrix
from xgboost import XGBClassifier
warnings.filterwarnings('ignore')
SEED=2026
BASE=Path('/mnt/data/NHIS2024_Day4_POST_UHS_FINAL_PACKAGE')
OUT=Path('/mnt/data/NHIS2024_Day5_FINAL'); OUT.mkdir(exist_ok=True)
MAIN=['AGEP_A','SEX_A','HISPALLP_A','EDUCP_A','RATCAT_A','EMPWRKLSW1_A','NOTCOV_A','FDSCAT3_A','PHSTAT_A','DISAB3_A','K6SPD_A','CHRONIC_BURDEN_CAT']
NUM=['AGEP_A']; CAT=[c for c in MAIN if c not in NUM]
SPECIAL={'AGEP_A':{97,98,99},'SEX_A':{7,8,9},'HISPALLP_A':{97,98,99},'EDUCP_A':{97,98,99},'RATCAT_A':{98},'EMPWRKLSW1_A':{7,8,9},'NOTCOV_A':{7,8,9},'FDSCAT3_A':{8},'PHSTAT_A':{7,8,9},'DISAB3_A':{9},'K6SPD_A':{8}}
def bucket(h):
 x=int(hashlib.sha256((f'NHIS2024_DAY5|{h}').encode()).hexdigest()[:12],16)%10
 return 'test' if x in (0,1) else ('validation' if x==2 else 'train')
def clean(df):
 x=df[MAIN].copy()
 for c,vals in SPECIAL.items():
  x[c]=pd.to_numeric(x[c],errors='coerce'); x.loc[x[c].isin(vals),c]=np.nan
 for c in CAT:
  if c=='CHRONIC_BURDEN_CAT': x[c]=x[c].where(x[c].notna(),'Missing/indeterminate').astype(str)
  else: x[c]=x[c].map(lambda v: np.nan if pd.isna(v) else str(int(v)) if float(v).is_integer() else str(v))
 return x
def make_prep():
 return ColumnTransformer([('num',Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler())]),NUM),('cat',Pipeline([('imputer',SimpleImputer(strategy='constant',fill_value='Missing')),('ohe',OneHotEncoder(handle_unknown='ignore',sparse_output=True))]),CAT)])
def specificity(y,pred,w=None):
 tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1],sample_weight=w).ravel(); return tn/(tn+fp) if tn+fp else np.nan
def metrics(y,p,w=None,thr=.5):
 pred=(p>=thr).astype(int); kw={'sample_weight':w} if w is not None else {}
 return {'AUROC':roc_auc_score(y,p,**kw),'AUPRC':average_precision_score(y,p,**kw),'Recall':recall_score(y,pred,zero_division=0,**kw),'Precision':precision_score(y,pred,zero_division=0,**kw),'F1':f1_score(y,pred,zero_division=0,**kw),'Specificity':specificity(y,pred,w),'Brier':brier_score_loss(y,p,**kw),'Predicted_positive_rate':np.average(pred,weights=w) if w is not None else pred.mean(),'Mean_predicted_probability':np.average(p,weights=w) if w is not None else p.mean(),'Observed_prevalence':np.average(y,weights=w) if w is not None else y.mean()}
def model(name):
 if name=='LR': return LogisticRegression(max_iter=2000,solver='lbfgs',C=1.0,random_state=SEED)
 if name=='RF': return RandomForestClassifier(n_estimators=250,max_features='sqrt',min_samples_leaf=5,n_jobs=-1,random_state=SEED)
 return XGBClassifier(n_estimators=250,max_depth=4,learning_rate=.05,subsample=.85,colsample_bytree=.85,min_child_weight=2,reg_lambda=1.0,objective='binary:logistic',eval_metric='logloss',tree_method='hist',n_jobs=4,random_state=SEED)
allm=[]; splits=[]; audits=[]; preds=[]; featrows=[]
for outcome,fn,target in [('MEDNG','analysis_ready_MEDNG_FINAL_FEATURELOCK_RAWCODES.csv','TARGET_FORGONE_COST'),('MEDDL','analysis_ready_MEDDL_FINAL_FEATURELOCK_RAWCODES.csv','TARGET_DELAYED_COST')]:
 df=pd.read_csv(BASE/fn); df['SPLIT']=df.HHX.map(bucket); X=clean(df); y=df[target].astype(int).to_numpy(); w=df.WTFA_A.astype(float).to_numpy(); sp=df.SPLIT.to_numpy(); tr=sp=='train'; te=sp=='test'
 for s in ['train','validation','test']:
  m=sp==s; splits.append({'Outcome':outcome,'Split':s,'N':int(m.sum()),'Positive_N':int(y[m].sum()),'Positive_rate':float(y[m].mean()),'WTFA_weighted_prevalence':float(np.average(y[m],weights=w[m]))})
 prep=make_prep(); Xtr=prep.fit_transform(X.loc[tr]); Xte=prep.transform(X.loc[te]); featrows.append({'Outcome':outcome,'Encoded_feature_count':Xtr.shape[1],'Train_N':Xtr.shape[0],'Test_N':Xte.shape[0]})
 for name in ['LR','RF','XGBoost']:
  for tw in ['Unweighted','WTFA_A']:
   est=model(name); fitkw={}
   if tw=='WTFA_A': fitkw['sample_weight']=w[tr]/w[tr].mean()
   est.fit(Xtr,y[tr],**fitkw); p=est.predict_proba(Xte)[:,1]
   for ewname in ['Unweighted','WTFA_A']:
    ew=None if ewname=='Unweighted' else w[te]; allm.append({'Outcome':outcome,'Model':name,'Train_weighting':tw,'Evaluation_weighting':ewname,'Threshold':.5,**metrics(y[te],p,ew)})
   for h,yy,pp,ww in zip(df.loc[te,'HHX'],y[te],p,w[te]): preds.append({'Outcome':outcome,'HHX':h,'Model':name,'Train_weighting':tw,'y_true':int(yy),'pred_prob':float(pp),'WTFA_A':float(ww)})
 for c in MAIN:
  miss=((X[c]=='Missing/indeterminate').sum() if c=='CHRONIC_BURDEN_CAT' else X[c].isna().sum()); miss_tr=((X.loc[tr,c]=='Missing/indeterminate').sum() if c=='CHRONIC_BURDEN_CAT' else X.loc[tr,c].isna().sum())
  audits.append({'Outcome':outcome,'Variable':c,'Cohort_N':len(df),'Missing_or_indeterminate_N':int(miss),'Missing_or_indeterminate_pct':float(miss/len(df)),'Train_N':int(tr.sum()),'Train_missing_N':int(miss_tr),'Train_missing_pct':float(miss_tr/tr.sum())})
metrics_df=pd.DataFrame(allm); split_df=pd.DataFrame(splits); audit_df=pd.DataFrame(audits); pred_df=pd.DataFrame(preds); feat_df=pd.DataFrame(featrows)
metrics_df.to_csv(OUT/'day5_model_metrics.csv',index=False); split_df.to_csv(OUT/'day5_split_audit.csv',index=False); audit_df.to_csv(OUT/'day5_preprocessing_missing_audit.csv',index=False); pred_df.to_csv(OUT/'day5_test_predictions.csv',index=False); feat_df.to_csv(OUT/'day5_encoded_feature_audit.csv',index=False)
matched=metrics_df[((metrics_df.Train_weighting=='Unweighted')&(metrics_df.Evaluation_weighting=='Unweighted'))|((metrics_df.Train_weighting=='WTFA_A')&(metrics_df.Evaluation_weighting=='WTFA_A'))].copy(); matched.to_csv(OUT/'day5_primary_matched_summary.csv',index=False)
best=[]
for outcome in matched.Outcome.unique():
 for tw in ['Unweighted','WTFA_A']:
  sub=matched[(matched.Outcome==outcome)&(matched.Train_weighting==tw)]; best.append(sub.loc[sub.AUPRC.idxmax()].to_dict())
pd.DataFrame(best).to_csv(OUT/'day5_best_by_auprc.csv',index=False)
manifest={'day':'Day 5','status':'COMPLETE_BASELINE_MODELING','seed':SEED,'split':'Deterministic HHX SHA-256 buckets: 70% train / 10% validation / 20% test; validation reserved and unused in baseline fit.','main_constructs':MAIN,'models':{'LR':'LogisticRegression C=1, lbfgs, max_iter=2000','RF':'250 trees, max_features=sqrt, min_samples_leaf=5','XGBoost':'250 trees, depth=4, learning_rate=.05, subsample=.85, colsample=.85'},'weighting':'Unweighted vs WTFA_A train sample weighting normalized to mean 1. No SMOTE/resampling/class balancing in Day 5 baseline to preserve probability interpretation.','evaluation':'Held-out test only; both unweighted and WTFA_A-weighted metrics; threshold metrics at 0.5 are baseline only.','notes':['PPSU/PSTRAT/WTFA_A/HHX are not predictors.','MEDNG and MEDDL modeled independently.','No SHAP/fairness audit/threshold optimization in Day 5.']}
(OUT/'DAY5_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Day 5 baseline complete')
