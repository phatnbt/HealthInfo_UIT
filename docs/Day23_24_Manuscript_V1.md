# Survey-Aware Explainable Machine Learning for Cost-Related Unmet Medical Care in United States Adults

## Manuscript status and scope

This Day 23–24 version assembles the full first manuscript from the computational state frozen through Day 22. It reports all three retained model families and does not declare a universal winner. The numerical claims are traceable through `docs/Day23_24_Claim_Traceability.csv`; the required UHS decisions are separated in `docs/Day23_24_UHS_Review_Guide.md`.

## Abstract

### Background

Cost-related barriers can lead adults to delay or forgo needed medical care. Predictive models may help characterize these barriers, but uncommon outcomes, complex survey design, model explainability, and subgroup performance require joint evaluation.

### Methods

We analyzed the 2024 National Health Interview Survey Sample Adult public-use data. The primary outcome was needing but not receiving medical care because of cost during the previous 12 months (`MEDNG12M_A`); cost-related delayed care (`MEDDL12M_A`) was analyzed independently. Twelve prespecified demographic, socioeconomic, insurance, health-status, functioning, and chronic-burden constructs were used to compare Logistic Regression, Random Forest, and XGBoost. Respondents were assigned deterministically by household identifier to train, validation, and locked-test sets. Model selection, probability calibration, and operating-threshold selection were performed with separate validation roles. We compared unweighted and `WTFA_A`-weighted estimates, used SHAP for predictive attribution, audited subgroup discrimination, calibration, and errors, and assessed threshold, seed, missingness, and composite-outcome sensitivity.

### Results

The analytic cohorts included 32,354 adults for forgone care and 32,355 for delayed care. Population-weighted prevalence was 7.39% and 8.58%, respectively. Across the six outcome-model combinations, weighted locked-test AUROC ranged from 0.780 to 0.809 and AUPRC from 0.315 to 0.339. Operating-point behavior differed: Random Forest had lower false-negative rates but higher false-positive rates, while Logistic Regression or XGBoost generally reduced false-positive burden. SHAP rankings were stable between weighted and unweighted aggregation within a model but differed across model families. Insurance and age showed the largest threshold-level subgroup signals; notably, the Random Forest false-positive rate among eligible uninsured adults was 0.975 for forgone care and 1.000 for delayed care at the locked thresholds. Discrimination was stable across three prespecified seeds, whereas threshold changes affected recall and precision as expected. No model was uniformly best across outcomes, metrics, and subgroups.

### Conclusions

The models provided moderate discrimination but materially different error trade-offs. Survey weighting, explainability, and subgroup auditing changed the interpretation of performance without identifying a universal winner. Any operational model choice requires a prespecified use case and an explicit judgment about the relative harm of false negatives and false positives. The findings are predictive and cross-sectional, not causal or deployment-ready.

### Keywords

National Health Interview Survey; unmet medical care; delayed care; machine learning; survey weighting; SHAP; health equity; subgroup performance

## 1 Introduction

Affordable access to needed medical care is a core health-equity concern. In this study, cost-related unmet medical care refers primarily to needing medical care but not receiving it because of cost during the previous 12 months. Cost-related delayed care is examined as a complementary outcome. Prior National Health Interview Survey research has documented temporal and socioeconomic patterning in cost-related unmet care, including differences related to insurance, income, education, race and ethnicity, and age [5–7]. These findings support treating affordability barriers as a population health and health-services issue rather than solely an individual clinical characteristic.

The predictor framework combines Andersen's Behavioral Model of Health Services Use with a social-determinants-of-health perspective. Andersen's model organizes characteristics into predisposing, enabling, and need domains [1,2]. Social and economic conditions can shape opportunities to obtain care [3,4]. Food insecurity, for example, may reflect competing material needs and has been associated with cost-related medication underuse and delayed or forgone care [9–11]. Chronic-condition burden, self-rated health, disability, and psychological distress may represent health-care need or vulnerability, but their roles in a cross-sectional prediction model must not be interpreted as independent causal effects [8].

Machine learning can represent nonlinearities and interactions, but neither machine learning with social determinants nor SHAP-based interpretation is novel by itself [15–17,19]. Likewise, overall model performance is insufficient when performance or error rates may vary across population groups [18]. A contemporary analysis of cost-related care barriers therefore benefits from evaluating discrimination, precision-recall trade-offs, calibration, predictive attribution, and subgroup errors together.

NHIS is a complex probability survey. Sampling weights change how observations contribute to population-relevant estimates, while strata and primary sampling units are needed for design-aware uncertainty. Prior methodological work shows that accounting for survey design can affect predictive modeling and interpretation [12–14]. For this reason, we distinguish conventional predictive evaluation from survey-weighted sensitivity and do not describe weighting alone as a complete design-based machine-learning solution.

This study asks three questions. First, how do Logistic Regression, Random Forest, and XGBoost compare when predicting cost-related forgone and delayed care from 12 prespecified constructs? Second, how stable are performance and SHAP patterns when population weights and prespecified robustness checks are considered? Third, do discrimination, calibration, or error rates vary across selected health-equity subgroups? The intended contribution is the joint, reproducible integration of these components for NHIS 2024, not a claim that any component is unprecedented.

## 2 Methods

### 2.1 Data source and analytic cohorts

We used the 2024 NHIS Sample Adult public-use file, which contained 32,629 records. Separate valid-response cohorts were retained for each outcome rather than restricting both analyses to a common complete-outcome sample. The forgone-care cohort contained 32,354 adults with 2,195 positive outcomes, and the delayed-care cohort contained 32,355 adults with 2,564 positive outcomes. A common cohort of 32,345 adults was used only for the prespecified composite sensitivity outcome representing either barrier.

### 2.2 Outcomes

The primary outcome was cost-related forgone care (`MEDNG12M_A`), coded positive when the respondent reported needing but not obtaining medical care because of cost during the previous 12 months. Cost-related delayed care (`MEDDL12M_A`) was modeled independently as a complementary outcome. Responses outside the valid yes/no codes were excluded only from the relevant outcome cohort. The composite `MEDNG OR MEDDL` outcome was analyzed separately and did not replace the independent outcomes.

### 2.3 Predictors

The main feature set was locked after codebook and UHS review. It contained age (`AGEP_A`), sex (`SEX_A`), race and ethnicity (`HISPALLP_A`), education (`EDUCP_A`), poverty category (`RATCAT_A`), employment or work status (`EMPWRKLSW1_A`), insurance coverage (`NOTCOV_A`), food-security category (`FDSCAT3_A`), self-rated health (`PHSTAT_A`), disability (`DISAB3_A`), psychological distress (`K6SPD_A`), and a derived chronic-condition burden category (`CHRONIC_BURDEN_CAT`). The chronic-burden construct grouped a count from eight selected chronic-condition domains into 0, 1, 2, and 3 or more conditions; unresolved source codes were not treated as absence. It is a predictive burden construct, not a validated clinical severity index.

Survey design variables (`WTFA_A`, `PSTRAT`, and `PPSU`), identifiers, and outcomes were excluded from predictors. Variable-specific missing and special codes were cleaned before train-fitted imputation or explicit categorical handling.

### 2.4 Data partitioning and leakage control

Respondents were assigned deterministically by `HHX` using the Day 5 SHA-256 rule to approximately 70% train, 10% validation, and 20% locked test sets. The forgone-care split contained 22,711 train, 3,226 validation, and 6,417 test records; the delayed-care split contained 22,711 train, 3,225 validation, and 6,419 test records. Preprocessing was fitted on the training set only. Validation observations were deterministically subdivided into model-selection, calibration, and threshold roles so that hyperparameter selection, calibration assessment, and threshold selection used distinct roles. The locked test set was not used to select features, hyperparameters, probability versions, thresholds, or random seeds.

### 2.5 Models, calibration, and operating thresholds

We compared Logistic Regression, Random Forest, and XGBoost. Logistic Regression remained the fixed baseline comparator. Random Forest and XGBoost underwent a moderate prespecified candidate search, with candidates selected by AUPRC in the validation model-selection role. Platt scaling was fitted in the validation calibration role, and raw versus Platt-scaled probabilities were selected using Brier score in the validation threshold role. Forgone-care models retained raw probabilities; delayed-care models used Platt-scaled probabilities. The operating threshold for each outcome-model pair maximized validation F1. These thresholds are analytical operating points, not clinical or policy cutoffs.

### 2.6 Performance and survey-aware sensitivity

Because both outcomes were uncommon, AUPRC was treated as the primary discrimination metric and AUROC as complementary. We also reported recall, precision, F1, specificity, Brier score, false-negative rate, and false-positive rate. Conventional unweighted evaluation and `WTFA_A`-weighted evaluation were reported in parallel. Population prevalence used `WTFA_A` with Taylor-linearized uncertainty based on `PSTRAT` and `PPSU`. Survey-aware performance uncertainty used stratified primary-sampling-unit bootstrap sensitivity intervals. These procedures improve population relevance but do not substitute for every official NCHS variance procedure.

### 2.7 Explainability

SHAP was calculated for the six locked estimators on the locked test set. Logistic Regression explanations used base-estimator log-odds, Random Forest used positive-class probability, and XGBoost used raw margin or log-odds. One-hot contributions were summed within each respondent to recover the 12 original constructs. Global importance was summarized using mean absolute SHAP with and without `WTFA_A`; signed and category-level summaries were used only to describe fitted-model patterns. Because output scales differ, absolute SHAP magnitudes were not compared across model families. SHAP was not interpreted as causal effect, biological difference, or fairness evidence.

### 2.8 Subgroup performance and fairness audit

We audited race and ethnicity, poverty, insurance, sex, and age. `SEX_A` was interpreted as sex, not gender, and race and ethnicity were treated as social and structural stratifiers rather than biological causes. Subgroup metrics used the same locked threshold within an outcome-model pair. Comparative gaps required at least 100 test observations, 20 positive outcomes, and 20 negative outcomes. Underpowered groups were recorded as skipped and were not pooled after results were seen. Recall span provided descriptive equal-opportunity information, with FPR reported separately; no single scalar was labeled equalized odds, and a gap was not treated as proof of discrimination.

### 2.9 Error analysis and robustness

Aggregate false-negative and false-positive profiles were evaluated overall and across eligible subgroups. Robustness checks multiplied each locked threshold by 0.8, 1.0, and 1.2; refitted stochastic models with seeds 2026, 2037, and 2048; compared test records with and without any cleaned-feature missingness; and fitted the separate composite outcome while reusing locked forgone-care hyperparameters. None of these test analyses was used to replace a locked choice.

### 2.10 Reproducibility and privacy

The computational state was frozen with SHA-256 hashes of 30 code and output artifacts after the controlled `CHRONIC_BURDEN_CAT` report-layer correction. Validators reproduced the locked analysis arms and checked schema, invariants, figures, and hashes. Only aggregate tables, figures, and manifests were exported. Household identifiers, person-level probabilities, predictions, and SHAP matrices were not committed.

## 3 Results

### 3.1 Outcome prevalence and overall performance

Population-weighted prevalence was 7.39% for forgone care (95% CI 6.99%–7.78%) and 8.58% for delayed care (95% CI 8.15%–9.01%). In the locked test sets, weighted AUROC ranged from 0.780 to 0.809 and weighted AUPRC from 0.315 to 0.339. The 95% bootstrap intervals for conventional AUROC and AUPRC overlapped substantially across models, and no model dominated all metrics.

For forgone care, XGBoost had the highest weighted AUROC (0.809) and weighted F1 (0.363), Random Forest had the highest weighted AUPRC (0.328) and recall (0.583), and XGBoost had the highest precision (0.310) and specificity (0.926). For delayed care, XGBoost had the highest weighted AUROC (0.802), Random Forest had the highest weighted AUPRC (0.339) and recall (0.699), while Logistic Regression had the highest weighted precision (0.334), F1 (0.389), and specificity (0.910). These differences represent trade-offs rather than a universal ranking.

### 3.2 Operating-point errors

For forgone care, weighted FNR was 0.504 for Logistic Regression, 0.417 for Random Forest, and 0.562 for XGBoost; corresponding FPR was 0.100, 0.159, and 0.074. For delayed care, weighted FNR was 0.535, 0.301, and 0.467, while FPR was 0.090, 0.255, and 0.126. Thus, Random Forest reduced missed positives at the cost of more false-positive classifications, whereas Logistic Regression or XGBoost generally reduced false-positive burden.

### 3.3 Predictive attribution

The weighted and unweighted construct rankings were highly concordant within each model, with Spearman correlations from 0.979 to 1.000. However, leading constructs differed across model families. For forgone care, the top weighted constructs were self-rated health, age, and employment for Logistic Regression; food security, insurance, and age for Random Forest; and race and ethnicity, psychological distress, and insurance for XGBoost. For delayed care, age, self-rated health, and employment led Logistic Regression; insurance, food security, and age led Random Forest; and race and ethnicity, psychological distress, and poverty led XGBoost. `CHRONIC_BURDEN_CAT` ranked fifth in the weighted forgone-care XGBoost explanation but lower in the other global rankings. These patterns describe allocation of predictive attribution within each fitted model and do not establish causal mechanisms.

### 3.4 Subgroup performance

Insurance produced the largest threshold-level audit signal. Across outcome-model pairs, insured-uninsured weighted AUROC spans were comparatively small, while recall and FPR spans were large. At the Random Forest thresholds, the eligible uninsured group had recall of 1.000 for both outcomes and FPR of 0.975 for forgone care and 1.000 for delayed care. The result indicates that nearly all eligible uninsured negatives were flagged; it is not evidence of good screening, discriminatory intent, or causal harm.

Age also showed substantial recall variation. The largest eligible-group weighted recall spans ranged from 0.307 to 0.487 for forgone care and from 0.213 to 0.405 for delayed care across models. Age 75 and older was excluded from comparative metrics because of insufficient positive events. Only Hispanic, non-Hispanic White, and non-Hispanic Black groups met the event gate for race and ethnicity comparisons. Sex point-estimate spans were smaller than the insurance and age signals, but this did not establish absence of disparity.

### 3.5 Robustness and composite sensitivity

Across threshold multipliers, weighted F1 ranged from 0.297 to 0.363 for forgone care and from 0.285 to 0.389 for delayed care. Lower thresholds generally increased recall and decreased precision or specificity; higher thresholds produced the reverse pattern. Across seeds 2026, 2037, and 2048, weighted AUPRC varied by at most approximately 0.006 and weighted AUROC by at most approximately 0.005 within an outcome-model pair. Missingness-stratum estimates were less stable because only 375–376 test observations, including 36 positives for each outcome, had at least one cleaned-feature missing value.

The composite sensitivity included 32,345 adults with 3,014 positive outcomes. Weighted test prevalence was 10.18%. Weighted AUROC and AUPRC were 0.788 and 0.390 for Logistic Regression, 0.797 and 0.393 for Random Forest, and 0.806 and 0.382 for XGBoost. Random Forest had the highest recall, XGBoost the highest AUROC, and Logistic Regression the highest precision, F1, and specificity. The composite analysis therefore also did not identify a universal winner and did not replace separate outcome reporting.

## 4 Discussion

### 4.1 Principal findings

Three findings are central. First, all three models achieved moderate discrimination, but the apparent ranking depended on the outcome and metric. Second, population weighting and SHAP aggregation did not radically reorder performance or within-model attribution, yet they changed prevalence and several precision-recall and subgroup estimates enough to affect interpretation. Third, the largest practical concern emerged at the operating threshold rather than in overall AUROC: models with similar ranking performance could have markedly different false-negative and false-positive behavior, especially by insurance status.

The absence of a universal winner is not a failure of the analysis. A model that captures more positive cases may also consume more follow-up resources by flagging more negative cases. Random Forest illustrates this trade-off: its higher recall was accompanied by lower precision and specificity and, among eligible uninsured adults, extreme false-positive rates at the locked thresholds. XGBoost or Logistic Regression reduced false-positive burden in several comparisons but missed more positives. Selecting a primary operational model therefore requires a use case and a prespecified utility function or error-cost judgment that were not available in this methodological study.

### 4.2 Interpretation of predictor patterns

The models repeatedly relied on enabling and need-related information, including insurance, food security, poverty, employment, self-rated health, psychological distress, and chronic burden. This is consistent with conceptual and empirical literature on material resources, health-care need, and affordability barriers [1–4,8–11]. However, model-specific rankings differed substantially. XGBoost assigned high attribution to race and ethnicity and psychological distress, while Logistic Regression and Random Forest distributed importance differently. Correlation, categorical coding, nonlinear splits, and the sharing of predictive information can all produce such differences. Accordingly, these rankings should guide domain review and hypothesis generation, not causal claims or targeted intervention rules.

The chronic-burden result needs particular care. `CHRONIC_BURDEN_CAT` is an engineered count category, not a clinical severity score. A controlled reporting correction preserved the `3+` category instead of merging it with missing values; model fitting and global or encoded SHAP importance were unchanged. Manuscript interpretation should therefore use the corrected category labels while retaining the frozen model results.

### 4.3 Survey design and health equity

The weighted prevalence estimates were higher than their unweighted counterparts, showing why sample proportions alone should not be presented as population estimates. At the same time, the weighted-versus-unweighted predictive differences were generally smaller than the operating-point subgroup differences. This distinction matters: survey weighting addresses population representation, whereas subgroup auditing asks whether a fixed model and threshold behave similarly across groups. Neither analysis replaces the other.

The insurance signal should be described as a threshold-level performance disparity requiring investigation. Higher outcome prevalence among uninsured adults partly affects AUPRC and Brier comparisons, and insurance was itself a predictor. Those facts do not explain away the near-universal positive classification by Random Forest, but they prevent a simple conclusion of fairness or discrimination. The correct next step is to define the intended decision context, examine uncertainty and resource consequences, and, if deployment is contemplated, validate prospectively in an external sample before choosing or redesigning thresholds.

### 4.4 Relation to prior work and contribution

Prior studies have examined cost-related care barriers in NHIS, social determinants of unmet care, machine learning with health-services outcomes, complex-survey methods, SHAP, and health algorithm fairness [5–19]. Kim et al. used multiple machine-learning models and SHAP for unmet medical needs in a Korean panel population [19], demonstrating that the combination of machine learning and SHAP is not itself new. The narrower contribution here is a reproducible integration of contemporary NHIS 2024 outcomes, survey-weighted sensitivity, model-specific explainability, locked-threshold subgroup auditing, and robustness checks. This contribution remains methodological and descriptive; it does not demonstrate clinical utility.

### 4.5 Implications

For research use, the analysis supports reporting multiple metrics, keeping weighted and unweighted views distinguishable, and evaluating subgroup errors before making a model-selection claim. For public-health use, the results indicate which trade-offs and population groups require closer evaluation. They do not support individual eligibility decisions, automated outreach, or micro-targeting. Any future applied workflow would need stakeholder-defined costs, capacity constraints, prospective calibration, external validation, privacy review, and monitoring for subgroup harms.

## 5 Limitations

This study has several limitations. First, NHIS 2024 is cross-sectional. The models classify contemporaneously reported barriers and cannot establish temporal prediction or causal effects. Second, the outcomes are self-reported and may be affected by recall, interpretation, and nonresponse. Third, the 12-construct feature set was prespecified for interpretability and scope control; omitted social, contextual, or health-system factors may contain relevant information.

Fourth, weighted predictive analysis is not identical to full design-based model estimation. Although `WTFA_A`, `PSTRAT`, and `PPSU` were used for population estimates and survey-aware sensitivity intervals, the ML estimators do not implement every official NCHS variance procedure. Fifth, thresholds optimized validation F1 and were not derived from clinical utility, intervention capacity, or policy cost. Subgroup error disparities may therefore change under another prespecified operating policy.

Sixth, subgroup results were limited by event counts. Several race and ethnicity levels and adults aged 75 or older did not meet the stability gate, and missingness-stratum estimates were based on small positive-event counts. A skipped comparison is evidence of insufficient precision, not evidence of equality. Seventh, SHAP is model- and scale-specific; correlated or differently encoded predictors can redistribute attribution. SHAP values do not estimate causal effects.

Eighth, the composite outcome reused forgone-care hyperparameters to avoid test-driven tuning and is therefore a sensitivity analysis rather than an independently optimized endpoint. Ninth, the analysis lacks external and prospective validation. Performance in other years, surveys, countries, or care systems is unknown. In particular, findings from United States NHIS data must not be directly generalized to Vietnam or the Mekong Delta. Such settings are appropriate for future locally designed studies, not for direct transport of these estimates.

## 6 Conclusions

Logistic Regression, Random Forest, and XGBoost offered different discrimination and operating-point trade-offs for cost-related forgone and delayed care in NHIS 2024. Population weighting, SHAP, subgroup auditing, and robustness analysis added distinct information but did not identify a universal winner. The most defensible current result is a transparent comparison with explicit uncertainty and interpretation boundaries. Before any model is selected for operational use, stakeholders must define the use case, the relative cost of missed versus unnecessary flags, and the acceptable subgroup behavior, followed by prospective and external validation.

## Data availability

The analysis uses the publicly available 2024 NHIS Sample Adult public-use data. The repository retains aggregate outputs, code, configuration, and checksums; person-level analytic data and identifiers are not distributed.

## Ethics and privacy

This secondary analysis uses public-use survey data. Outputs in the reproducibility package are aggregate. No person-level prediction, probability, SHAP matrix, or household identifier is exported.

## References

1. Andersen RM. Revisiting the behavioral model and access to medical care: does it matter? 1995. https://pubmed.ncbi.nlm.nih.gov/7738325/
2. Babitsch B, Gohl D, von Lengerke T. Re-revisiting Andersen's Behavioral Model of Health Services Use: a systematic review of studies from 1998–2011. 2012. https://pmc.ncbi.nlm.nih.gov/articles/PMC3488807/
3. Braveman P, Gottlieb L. The social determinants of health: it's time to consider the causes of the causes. 2014. https://pmc.ncbi.nlm.nih.gov/articles/PMC3863696/
4. Alemu FW et al. Social determinants of unmet need for primary care: a systematic review. 2024. https://pubmed.ncbi.nlm.nih.gov/39358748/
5. Mahajan S et al. Trends in Differences in Health Status and Health Care Access and Affordability by Race and Ethnicity in the United States, 1999–2018. 2021. https://pubmed.ncbi.nlm.nih.gov/34402830/
6. Cai J, Bidulescu A. Trends in unmet health care needs among adults in the U.S., 2019–2021. 2023. https://pubmed.ncbi.nlm.nih.gov/37690672/
7. Casagrande SS, Lawrence JM. Trends in delaying and forgoing medical care due to cost and the association with insurance status among US adults with diabetes, 2009–2023. 2025. https://pubmed.ncbi.nlm.nih.gov/41469085/
8. Azubuike CD, Alawode OA. Delayed Healthcare Due to Cost Among Adults with Multimorbidity in the United States. 2024. https://pubmed.ncbi.nlm.nih.gov/39595468/
9. Berkowitz SA, Seligman HK, Choudhry NK. Treat or Eat: Food Insecurity, Cost-related Medication Underuse, and Unmet Needs. 2014. https://doi.org/10.1016/j.amjmed.2014.01.002
10. Bertoldo J et al. Food Insecurity and Delayed or Forgone Medical Care During the COVID-19 Pandemic. 2022. https://pmc.ncbi.nlm.nih.gov/articles/PMC9010899/
11. Cole MB, Nguyen KH. Unmet social needs among low-income adults in the United States: Associations with health care access and quality. 2020. https://pubmed.ncbi.nlm.nih.gov/32880945/
12. MacNell N et al. Implementing machine learning methods with complex survey data: Lessons learned on the impacts of accounting sampling weights in gradient boosting. 2023. https://pubmed.ncbi.nlm.nih.gov/36638125/
13. Dey D et al. The proper application of logistic regression model in complex survey data: a systematic review. 2025. https://pubmed.ncbi.nlm.nih.gov/39844030/
14. Matabuena M, Vidal JC, Ghosal R, Onnela JP. Screening for diabetes mellitus in the US population using neural network-based modeling and complex survey designs. 2026. https://pubmed.ncbi.nlm.nih.gov/42095565/
15. Loh HW et al. Application of explainable artificial intelligence for healthcare: A systematic review of the last decade 2011–2022. 2022. https://pubmed.ncbi.nlm.nih.gov/36228495/
16. Sun F et al. Social Determinants, Cardiovascular Disease, and Health Care Cost: A Nationwide Study in the United States Using Machine Learning. 2023. https://pmc.ncbi.nlm.nih.gov/articles/PMC10111459/
17. Wang RC, Sambamoorthi U. Predicting Anticipated Telehealth Use: Development of the CONTEST Score and Machine Learning Models Using a National U.S. Survey. 2026. https://doi.org/10.3390/healthcare14040500
18. Rajkomar A, Hardt M, Howell MD, Corrado G, Chin MH. Ensuring Fairness in Machine Learning to Advance Health Equity. 2018. https://pubmed.ncbi.nlm.nih.gov/30508424/
19. Kim J, Ji SM, Kim IS, Jang HY, Yoo CH, Kim JH, et al. Machine learning approach for unmet medical needs among middle-aged adults in South Korea: a cross-sectional study. 2025. https://doi.org/10.1186/s12913-025-12754-1

These entries are reproduced from the authoritative 19-source matrix in `literature/literature_matrix_day6.csv`. UHS should verify the bibliographic details and convert them to the target journal style during Day 25–28.
