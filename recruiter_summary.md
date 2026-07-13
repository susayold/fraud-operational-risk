# Project 5 Recruiter Summary

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Business problem

How should Risk combine transaction indicators, predictive models, deterministic controls and operational governance to reduce fraud loss without unacceptable customer friction or alert workload?

## What I built

- An observed 284,807-row PCA fraud benchmark with logistic, tree, SMOTE/undersampling and anomaly challengers.
- Validation-only model/threshold selection using PR-AUC, fraud-amount capture, capacity and net benefit.
- A separate 250,000-row synthetic controls environment with hidden stochastic fraud mechanisms, interpretable features and a distinct friendly-fraud dispute layer.
- Fifteen governed fraud rules, hybrid decisions, reason codes, fallbacks and overrides.
- Alert priority, 250-alert/day capacity, investigation outcomes, backlog/SLA sensitivity, incidents, KRIs, risk appetite and RCA.
- 38 UAT, 18 SIT and 16 executable negative tests plus a 14-sheet Excel management model.

## Headline result

Observed champion test PR-AUC is **0.7786**. The locked test alert policy captures **84.93%** of fraud transactions and **69.36%** of fraud amount at **28.44%** precision. Fraud-amount recall remains an Amber appetite exception requiring management acceptance and complementary high-value controls. These are benchmark results, not production claims.

## Value to an employer

I can connect fraud analytics to decisions, workload, controls, incidents and management action while preserving data lineage, claim boundaries and validation evidence.
