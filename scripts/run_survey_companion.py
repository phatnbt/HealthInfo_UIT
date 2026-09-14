"""Recompute Taylor and KG overall/subgroup tables without fitting predictors."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys
import numpy as np
import pandas as pd


def independent_taylor(frame,target,mask):
    """Array-based PSU totals independent of the original pandas grouping code."""
    w=frame.WTFA_A.to_numpy(float);y=frame[target].to_numpy(float)
    p=float(np.sum(w[mask]*y[mask])/w[mask].sum())
    linear=w*mask*(y-p)/w[mask].sum()
    keys=pd.MultiIndex.from_frame(frame[['PSTRAT','PPSU']])
    ids,unique=pd.factorize(keys,sort=True)
    totals=np.bincount(ids,weights=linear,minlength=len(unique))
    strata=np.array([k[0] for k in unique]);variance=0.;df=0
    for s in np.unique(strata):
        values=totals[strata==s];m=len(values)
        if m<2:raise ValueError('Singleton PSU requires an explicitly reviewed method.')
        variance+=m/(m-1)*float(np.square(values-values.mean()).sum());df+=m-1
    return p,float(np.sqrt(variance)),df


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from day11_13_survey_sensitivity import OUTCOMES,descriptive_rows,add_age_group,validate_design
    from run_repair_analysis import kg
    records=[];checks=[];inputs={}
    for outcome,spec in OUTCOMES.items():
        source=args.data_dir/spec['file'];frame=pd.read_csv(source)
        inputs[source.name]=hashlib.sha256(source.read_bytes()).hexdigest()
        assert frame.HHX.is_unique
        assert len(frame)=={'MEDNG':32354,'MEDDL':32355}[outcome]
        assert frame[spec['target']].isin([0,1]).all()
        design=validate_design(frame,outcome)
        overall,subgroups=descriptive_rows(frame,outcome,spec['target'])
        grouped=add_age_group(frame)
        for row in overall+subgroups:
            mask=np.ones(len(frame),bool) if row['Domain_variable']=='Overall' else grouped[row['Domain_variable']].astype(str).eq(str(row['Domain_value'])).to_numpy()
            p,se,df=independent_taylor(frame,spec['target'],mask)
            assert np.allclose([p,se],[row['Weighted_prevalence'],row['Taylor_SE']],atol=1e-12,rtol=0)
            assert df==row['Design_df']
            if not 0<p<1:raise ValueError('Boundary-proportion KG requires a separate reviewed implementation.')
            records.append({**row,**kg(row['Domain_N'],p,se,df)})
        checks.append({'Outcome':outcome,'Overall_rows':len(overall),'Subgroup_rows':len(subgroups),'Independent_Taylor_agreement':True,'Beta_F_KG_agreement':True,'Design':design})
    table=pd.DataFrame(records)
    assert len(table)==76 and table.Domain_variable.ne('Overall').sum()==74
    assert not table.duplicated(['Outcome','Domain_variable','Domain_value']).any()
    original=pd.read_csv(Path(__file__).resolve().parents[1]/'modeling/day11_13/day11_13_weighted_outcome_prevalence.csv').set_index('Outcome')
    for row in table.loc[table.Domain_variable.eq('Overall')].to_dict('records'):
        assert np.allclose([row['Weighted_prevalence'],row['Taylor_SE']],[original.loc[row['Outcome'],'Weighted_prevalence'],original.loc[row['Outcome'],'Taylor_SE']],atol=1e-12,rtol=0)
    table.to_csv(args.out_dir/'Korn_Graubard_companion.csv',index=False)
    table.loc[table.Domain_variable.ne('Overall')].to_csv(args.out_dir/'Korn_Graubard_subgroup_companion.csv',index=False)
    table.loc[:,list(overall[0])].to_csv(args.out_dir/'Taylor_prevalence_reconstructed.csv',index=False)
    (args.out_dir/'survey_companion_audit.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),'total_rows':76,'overall_rows':2,'subgroup_rows':74,'raw_cohort_SHA256':inputs,'checks':checks,'publication_boundary':'Aggregate subgroup results are local/Drive handoff material; not person-level microdata.','method':'Original full-cohort domain Taylor variance; independently recomputed using array PSU totals. KG Beta/F identity checked per row; NCHS size/width/review/complement flags. No official software validation claimed.'},indent=2),encoding='utf-8')
    print('PASS: 76 prevalence rows (2 overall + 74 subgroup); independent Taylor and Beta/F KG checks.')


if __name__=='__main__':main()
