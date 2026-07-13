# Project 5 - Fraud Detection, Transaction Controls & Operational Risk

## Portfolio review path

- Start: `OPEN_THIS_FIRST.html`
- Decision summary: `EXECUTIVE_SUMMARY.md`
- Validation: `VALIDATION_SUMMARY.md`
- Limitations: `LIMITATIONS.md`
- Artifact map: `ARTIFACT_INDEX.md`

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Recruiter readout

This project demonstrates the full fraud-risk decision lifecycle: observed benchmark data -> model/anomaly scores -> separately labelled synthetic controls -> hybrid decisions -> alert operations -> incidents/KRIs -> management action.

| Evidence | Result | Meaning |
| --- | ---: | --- |
| Observed transactions | 284,807 | Public PCA fraud benchmark |
| Observed fraud cases | 492 | Extreme imbalance |
| Champion test PR-AUC | 0.7786 | Primary ranking metric |
| Test fraud recall | 84.93% | Validation-locked alert policy |
| Test fraud amount recall | 69.36% | Validation-locked alert policy |
| Synthetic transactions | 250,000 | Interpretable controls testing |
| UAT / SIT / Negative | 38 / 18 / 16 | Executable governance evidence |

Open `OPEN_THIS_FIRST.html` for the recruiter presentation and `excel/Project5_FraudOperationalRisk_Model.xlsx` for the management workbook.

Author automated self-validation completed. Independent model validation, production approval and organisational release sign-off were not performed.

## Two evidence layers

**Layer A - Observed PCA Fraud Benchmark:** observed discrimination, class imbalance, fraud amount capture, calibration and historical threshold economics. PCA variables never become investigator reason codes.

**Layer B - Synthetic Controls-Testing Environment:** interpretable device, beneficiary, velocity, authentication and behavioural indicators; deterministic rules; hybrid decisions; alert queue; investigation outcomes; incidents; risk appetite; UAT/SIT. Synthetic performance is never presented as observed performance.

Friendly fraud is a separate post-transaction dispute/claim label and is not a transaction-time decline rule.

The recommended observed policy is deliberately presented as a balanced candidate rather than a perfect appetite pass: transaction recall, precision, capacity and net benefit meet the decision criteria, while fraud-amount recall remains Amber. The committee must accept that residual risk or add high-value control overlays.

## Rebuild

```text
python scripts/01_load_validate_observed_data.py
python scripts/02_build_observed_fraud_benchmark.py
python scripts/03_generate_synthetic_control_data.py
python scripts/04_build_synthetic_features_and_labels.py
python scripts/05_build_fraud_rules.py
python scripts/06_build_hybrid_decision_engine.py
python scripts/07_build_alert_operations.py
python scripts/08_build_operational_risk_outputs.py
python scripts/09_generate_excel_and_reports.py
python scripts/10_validate_final_outputs.py
```

Quick reviewer validation: `python scripts/10_validate_final_outputs.py`.

## Main limitations

The original `Time` column is unavailable in Project 0, so ordered `monitoring_period` is a temporal proxy. The observed variables are PCA-transformed, cost assumptions are illustrative, and synthetic controls/workflow outcomes do not represent a live bank. Production use requires governed applicant/customer data, timestamp semantics, real loss/recovery and customer outcomes, integration testing, independent validation and approval.
