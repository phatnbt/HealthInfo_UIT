# Day 7 — Background and Related Work Draft

**Project:** Survey-Aware Explainable Machine Learning for Cost-Related Unmet Medical Care in U.S. Adults: A Health Equity Analysis of NHIS 2024

> **Role / ownership note:** This is a **UHS / collaborative literature working draft** under the original Day 5–7 division of labor. It supports the shared paper but is **not counted as the UIT technical Day 7 deliverable**. UIT Day 5–7 technical work consists of leakage-safe preprocessing, train/validation/test splitting, Logistic Regression baseline modeling, and weighting comparison.
>
> Status: targeted narrative-review draft. This is **not** a PRISMA systematic review and should be refined by UHS/supervisors for journal-specific style before submission.

## 1. Background

Affordable access to needed medical care remains an important dimension of health equity. In this project, cost-related unmet medical care is operationalized primarily as needing medical care but not receiving it because of cost during the previous 12 months (`MEDNG12M_A`), with cost-related delayed care (`MEDDL12M_A`) analyzed independently as a secondary outcome. Previous U.S. National Health Interview Survey (NHIS) analyses show that cost-related unmet health-care needs are socially patterned and remain relevant even when prevalence changes over time [6]. Among U.S. adults with diabetes, delayed or forgone care due to cost has also varied by insurance, income, education, race/ethnicity, and age [7]. These findings support treating affordability barriers as a health-services and health-equity problem rather than only an individual clinical characteristic.

The conceptual organization of predictors is guided primarily by Andersen's Behavioral Model of Health Services Use. Andersen's model distinguishes factors that predispose individuals to service use, resources that enable or impede access, and perceived or evaluated health-care need [1]. A systematic review of studies applying the model found recurring use of demographic characteristics, education, income, insurance, and health-status measures, while also documenting substantial variation in operationalization [2]. This matters in secondary-data research because a conceptual construct must be mapped carefully to the actual survey variable rather than inferred from a convenient label.

Healthy People 2030 social determinants of health (SDOH) provides a supplementary framework. SDOH include economic stability, education access and quality, health-care access and quality, neighborhood and built environment, and social/community context. This framing is consistent with literature emphasizing that upstream social and economic conditions shape health opportunities and inequities [3]. A recent systematic review of unmet primary-care need likewise identified socioeconomic resources, mental-health factors, and chronic conditions as recurring correlates, while noting heterogeneity across settings [4].

Several enabling/material predictors have direct empirical support. Food insecurity can represent competing material needs rather than simply duplicate income. National U.S. studies have linked food insecurity with cost-related medication underuse [9] and delayed or forgone medical care because of cost concerns [10]. Unmet social needs among low-income U.S. adults have also been associated with access problems such as inability to see a doctor because of cost [11]. These findings motivate inclusion of poverty, food security, employment/work status, education, and insurance as distinct but potentially correlated predictive constructs. Their model contributions must be interpreted as shared predictive information rather than independent causal effects.

Need-related factors are relevant because greater health burden can increase demand for care and exposure to affordability barriers. Research among U.S. adults with multimorbidity has examined delayed care due to cost [8]. This supports the project's selected chronic-condition burden construct, while avoiding the stronger claim that the engineered count is a validated clinical severity index. Self-rated health, functional disability, and psychological distress are similarly treated as health-status/functioning constructs that can carry predictive information, not as causes established by the cross-sectional model.

## 2. Health equity and subgroup performance

Health-care affordability and access differ across social groups. Long-term NHIS analyses have documented persistent racial and ethnic differences in health status, health-care access, and affordability measures [5]. The project therefore treats race/ethnicity as a social and structural equity stratifier, not a biological cause. It evaluates model performance across sex, age, poverty, insurance, and other prespecified subgroups.

Algorithmic fairness literature shows why overall predictive performance is insufficient when a model may perform differently across protected or disadvantaged groups. Rajkomar and colleagues describe pathways through which historical data, model design, and deployment can reproduce health inequities and argue for explicit group-level evaluation [18]. In this study, subgroup AUROC, AUPRC, recall, false-negative rate, false-positive rate, and calibration are diagnostic performance measures. A gap between groups is therefore a performance disparity requiring interpretation; it is **not** by itself proof of discrimination.

## 3. Machine learning and explainability

Machine learning can model nonlinearities and interactions that are difficult to capture with a simple main-effects logistic regression. However, using machine learning with social determinants is not itself novel. Nationwide U.S. work has used machine learning to study SDOH, cardiovascular disease, and health-care costs [16], and recent national-survey research has compared regression and machine-learning approaches for a health-services outcome [17]. The present study therefore does not claim novelty from Logistic Regression, Random Forest, or XGBoost as algorithms.

Explainable artificial intelligence (XAI) is used to make model predictions more interpretable. A systematic review of health-care XAI literature describes the growing use of explainability methods to clarify how predictive systems use input information [15]. Planned SHAP analysis is therefore intended to estimate **predictive contribution** at global and subgroup levels. SHAP values will not be interpreted as causal effects, and correlated predictors may share or redistribute importance.

## 4. Complex survey data and survey-aware prediction

NHIS is a complex probability survey rather than a simple random sample. This creates a methodological distinction between ordinary machine learning and analyses that account for survey design. MacNell and colleagues showed that incorporating sampling weights can affect gradient-boosting results in complex health-survey data [12]. A systematic review of logistic regression with complex survey data found frequent weaknesses in reporting and handling survey design, missing information, diagnostics, and validation [13]. More recent work continues to develop predictive methods that explicitly incorporate complex-survey information [14].

For this reason, the project compares conventional unweighted training with `WTFA_A`-weighted predictive training. This is described as **survey-weighted predictive sensitivity**, not full design-based inference. `PSTRAT` and `PPSU` remain survey-design variables and are not ordinary predictors. Formal population inference, standard errors, and confidence intervals require procedures that explicitly respect the full survey design.

## 5. Research gap and proposed contribution

The literature does not support claiming that machine learning has never been used for unmet health care, that SDOH have not been used in machine learning, or that SHAP/fairness analysis is new by itself. The defensible gap is narrower.

Existing work has examined cost-related unmet or delayed care in national surveys [6–8], SDOH and health-care access [3,4,9–11], machine learning with SDOH [16,17], explainability in health care [15], complex-survey-aware modeling [12–14], and fairness in health machine learning [18]. What remains comparatively under-examined is their **joint integration** for contemporary cost-related unmet medical care among nationally representative U.S. adults.

Accordingly, this study contributes a reproducible NHIS 2024 analysis that: (1) predicts cost-related unmet medical care using prespecified demographic, socioeconomic, health-status, and functioning constructs; (2) compares conventional and survey-weighted predictive modeling; (3) evaluates subgroup performance/fairness; and (4) uses explainability to examine global and subgroup-specific predictive patterns. Because NHIS 2024 is cross-sectional, all results are interpreted as contemporaneous prediction/association rather than future forecasting or causal inference.

## References
See `NHIS2024_Day6_Literature_Matrix_18.xlsx` for the full 18-paper matrix, source URLs, relevance notes, and limitations.
