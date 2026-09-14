"""Aggregate-only imputation SHAP; preserves native sparse XGBoost semantics."""
import hashlib
import numpy as np
from scipy.special import expit


def explain(model, name, train, test, encoded_names, constructs, indices, weights, seed):
    """Return construct summaries and an additivity/representation audit."""
    from scipy import sparse
    dense=lambda x:x.toarray() if sparse.issparse(x) else np.asarray(x)
    selected=test[indices]
    data=dense(selected)
    legacy_difference=0.0
    if name=='LR':
        background_indices=np.sort(np.random.default_rng(seed+202).choice(train.shape[0],min(500,train.shape[0]),replace=False))
        reference=dense(train[background_indices]).mean(axis=0)
        values=(data-reference)*model.coef_[0]
        base=float(model.intercept_[0]+reference@model.coef_[0])
        expected=model.decision_function(selected)
        scale='base_estimator_log_odds'
        method='Independent/interventional linear SHAP; fixed 500-row train background'
    elif name=='RF':
        import shap
        explainer=shap.TreeExplainer(model,feature_perturbation='tree_path_dependent')
        result=explainer(data,check_additivity=True)
        values=np.asarray(result.values)
        if values.ndim==3:values=values[:,:,1]
        base=float(np.asarray(explainer.expected_value)[1])
        expected=model.predict_proba(selected)[:,1]
        scale='base_estimator_positive_class_probability'
        method='Exact tree-path-dependent TreeSHAP'
    elif name=='XGBoost':
        import xgboost
        matrix=xgboost.DMatrix(selected)
        contributions=model.get_booster().predict(matrix,pred_contribs=True,approx_contribs=False)
        values=contributions[:,:-1];base=contributions[:,-1]
        expected=model.get_booster().predict(matrix,output_margin=True)
        probabilities=model.predict_proba(selected)[:,1]
        assert np.allclose(expit(expected),probabilities,atol=1e-6,rtol=0)
        legacy_difference=float(np.max(np.abs(probabilities-model.predict_proba(data)[:,1])))
        scale='base_estimator_raw_margin_log_odds'
        method='Exact native TreeSHAP; DMatrix retains CSR implicit-missing semantics'
    else:raise ValueError(name)
    assert values.shape==(len(indices),len(encoded_names))
    residual=float(np.max(np.abs(values.sum(axis=1)+base-expected)))
    if not np.isfinite(values).all() or residual>3e-5:
        raise RuntimeError(f'{name} SHAP additivity failed: {residual}')
    mapped=[]
    for encoded in encoded_names:
        variable=encoded.split('__',1)[-1]
        found=[c for c in constructs if variable==c or variable.startswith(c+'_')]
        if len(found)!=1:raise RuntimeError('Ambiguous encoded construct: '+encoded)
        mapped.append(found[0])
    grouped=np.column_stack([values[:,np.array(mapped)==c].sum(axis=1) for c in constructs])
    assert np.allclose(grouped.sum(axis=1),values.sum(axis=1),atol=1e-6,rtol=1e-6)
    rows=[]
    for aggregation,w in [('Unweighted',None),('WTFA_A',weights[indices])]:
        importance=np.average(np.abs(grouped),axis=0,weights=w)
        signed=np.average(grouped,axis=0,weights=w)
        order=np.argsort(-importance,kind='stable');ranks=np.empty(len(order),int);ranks[order]=np.arange(1,len(order)+1)
        total=float(importance.sum())
        for j,c in enumerate(constructs):
            rows.append(dict(Construct=c,Aggregation=aggregation,Mean_absolute_SHAP=float(importance[j]),Mean_signed_SHAP=float(signed[j]),Rank=int(ranks[j]),Importance_share=float(importance[j]/total) if total else 0,Explained_output=scale,Explained_N=len(indices)))
    return rows,dict(Method=method,Explained_N=len(indices),Encoded_features=len(encoded_names),Additivity_max_absolute_residual=residual,Additivity_passed=True,Legacy_sparse_to_dense_probability_max_difference=legacy_difference,Explained_output=scale)
