# Day 7 — Background and Related Work Draft

**Project:** Survey-Aware Explainable Machine Learning for Cost-Related Unmet Medical Care in U.S. Adults: A Health Equity Analysis of NHIS 2024

> Status: targeted narrative-review draft. This is **not** a PRISMA systematic review and should be refined for journal-specific style before submission.

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

## References used in this draft

1. Andersen RM. *Revisiting the behavioral model and access to medical care: does it matter?* J Health Soc Behav. 1995;36(1):1–10.
2. Babitsch B, Gohl D, von Lengerke T. *Re-revisiting Andersen's Behavioral Model of Health Services Use: a systematic review of studies from 1998–2011.* Psychosoc Med. 2012;9:Doc11. doi:10.3205/psm000089.
3. Braveman P, Gottlieb L. *The social determinants of health: it's time to consider the causes of the causes.* Public Health Rep. 2014;129(Suppl 2):19–31. doi:10.1177/00333549141291S206.
4. Alemu FW, et al. *Social determinants of unmet need for primary care: a systematic review.* Syst Rev. 2024;13:252. doi:10.1186/s13643-024-02647-5.
5. Mahajan S, et al. *Trends in Differences in Health Status and Health Care Access and Affordability by Race and Ethnicity in the United States, 1999–2018.* JAMA. 2021;326(7):637–648. doi:10.1001/jama.2021.9907.
6. Cai J, Bidulescu A. *Trends in unmet health care needs among adults in the U.S., 2019–2021.* Prev Med. 2023;175:107699. doi:10.1016/j.ypmed.2023.107699.
7. Casagrande SS, Lawrence JM. *Trends in delaying and forgoing medical care due to cost and the association with insurance status among US adults with diabetes, 2009–2023.* BMJ Open Diabetes Res Care. 2025;13(6):e005446. doi:10.1136/bmjdrc-2025-005446.
8. Azubuike CD, Alawode OA. *Delayed Healthcare Due to Cost Among Adults with Multimorbidity in the United States.* Healthcare. 2024;12(22):2271. doi:10.3390/healthcare12222271.
9. Berkowitz SA, Seligman HK, Choudhry NK. *Treat or Eat: Food Insecurity, Cost-related Medication Underuse, and Unmet Needs.* Am J Med. 2014;127(4):303–310.e3. doi:10.1016/j.amjmed.2014.01.002.
10. Bertoldo J, et al. *Food Insecurity and Delayed or Forgone Medical Care During the COVID-19 Pandemic.* Am J Public Health. 2022;112(5):776–785. doi:10.2105/AJPH.2022.306724.
11. Cole MB, Nguyen KH. *Unmet social needs among low-income adults in the United States: Associations with health care access and quality.* Health Serv Res. 2020;55(Suppl 2):873–882. doi:10.1111/1475-6773.13555.
12. MacNell N, et al. *Implementing machine learning methods with complex survey data: Lessons learned on the impacts of accounting sampling weights in gradient boosting.* PLoS One. 2023;18(1):e0280387. doi:10.1371/journal.pone.0280387.
13. Dey D, et al. *The proper application of logistic regression model in complex survey data: a systematic review.* BMC Med Res Methodol. 2025;25:15. doi:10.1186/s12874-024-02454-5.
14. Matabuena M, Vidal JC, Ghosal R, Onnela JP. *Screening for diabetes mellitus in the US population using neural network-based modeling and complex survey designs.* Stat Methods Med Res. 2026;35(6):1257–1280. doi:10.1177/09622802261442893.
15. Loh HW, et al. *Application of explainable artificial intelligence for healthcare: A systematic review of the last decade (2011–2022).* Comput Methods Programs Biomed. 2022;226:107161. doi:10.1016/j.cmpb.2022.107161.
16. Sun F, et al. *Social Determinants, Cardiovascular Disease, and Health Care Cost: A Nationwide Study in the United States Using Machine Learning.* J Am Heart Assoc. 2023;12(5):e027919. doi:10.1161/JAHA.122.027919.
17. Wang RC, Sambamoorthi U. *Predicting Anticipated Telehealth Use: Development of the CONTEST Score and Machine Learning Models Using a National U.S. Survey.* Healthcare. 2026;14(4):500. doi:10.3390/healthcare14040500.
18. Rajkomar A, Hardt M, Howell MD, Corrado G, Chin MH. *Ensuring Fairness in Machine Learning to Advance Health Equity.* Ann Intern Med. 2018;169(12):866–872. doi:10.7326/M18-1990.

Full source URLs and row-level relevance/caution notes are maintained in `literature/literature_matrix_day6.csv`.
