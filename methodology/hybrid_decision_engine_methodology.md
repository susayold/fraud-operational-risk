# Hybrid Fraud Decision Engine Methodology

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

The engine combines calibrated synthetic model probability, anomaly percentile and observable deterministic controls. It returns `ALLOW`, `STEP_UP`, `HOLD`, `MANUAL_REVIEW`, `DECLINE`, `BLOCK_ACCOUNT` or `DATA_EXCEPTION` with traceable reason codes.

Priority is explicit: invalid inputs, blacklist/override controls, duplicate and account-takeover emergency controls, amount-aware high model risk, high-severity rules, combined signals, anomaly review, step-up and allow. Anomaly-only signals never create an automatic decline.

Validation-derived component thresholds used for incremental-value analysis are **0.1201** for the model and **0.9951** for anomaly percentile. The final hybrid routing uses the governed fixed boundaries in `rules/decision_matrix.csv`.

## Incremental value on synthetic test data

| component_set | alert_rate | precision | fraud_recall | fraud_amount_recall | net_benefit_proxy | unique_fraud_contribution |
| --- | --- | --- | --- | --- | --- | --- |
| Model only | 0.0114 | 0.1311 | 0.1314 | 0.0023 | -3052.8380 | 46.0000 |
| Rules only | 0.0352 | 0.0239 | 0.0742 | 0.0893 | -4900.0700 | 19.0000 |
| Anomaly only | 0.0055 | 0.0352 | 0.0169 | 0.1371 | 6550.8850 | 4.0000 |
| Model + rules | 0.0430 | 0.0463 | 0.1758 | 0.0911 | -6975.5190 | 0.0000 |
| Model + rules + anomaly | 0.0464 | 0.0451 | 0.1843 | 0.2030 | -1304.2670 | 0.0000 |
| Final hybrid actionable | 0.0244 | 0.0738 | 0.1589 | 0.1690 | 3056.5260 | 0.0000 |

Expected prevented loss is a prospective synthetic proxy (`score x amount x 70%`), while realised capture metrics use synthetic labels and amounts. These two views are not interchangeable.
