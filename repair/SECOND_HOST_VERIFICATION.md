# Second-host verification — Linux

Independent GitHub-hosted Azure runner, Ubuntu24.04, Python3.12.10. The repository was checked out at c730c8167601cd1cc36145c8f32ff3e4cf2df0e1; official NHIS inputs downloaded again and verified by MD5/count. Runtime dependencies installed from the repair lock. This is a remote host, separate from the Windows workstation.

[Completed132-fit MI/SHAP/KG workflow](https://github.com/phatnbt/HealthInfo_UIT/actions/runs/34880716053).

| Model | Maximum historical metric difference | Tolerance | Result |
|---|---:|---:|---|
| LR | 1.970645868709653e-15 | 1e-8 | PASS |
| RF | 9.714451465470121e-17 | 1e-8 | PASS |
| XGBoost | 1.1102230246251563e-16 | 1e-8 | PASS |

All240 MI performance rows,2880 sampled constructSHAP rows,120 additivity audits,76 KG rows and all four historical stored-artifact gates passed. Maximum sampled SHAP additivity residual7.62939453125e-6. Native Linux XGB library SHA-256: 0a3db9e83649ac38711e12a09519070e8b215b1255b735c78b05ad333b63be53.

This validates a Linux reference runtime that reproduces historical metrics; it does not prove byte identity to unavailable historical model/prediction files. Windows XGB wheel still fails historical tolerance. Do not describe arbitrary xgboost3.0.4 builds as interchangeable.

[Full-test corrected primary SHAP workflow](https://github.com/phatnbt/HealthInfo_UIT/actions/runs/34881598998) runs on the same validated Linux runtime, with strict reproduction gates and native CSR TreeSHAP. Read its completed validation before treating generated explanations as the corrected primary report layer.

Final UHS/venue review and scope decisions remain separate from computational validation.
