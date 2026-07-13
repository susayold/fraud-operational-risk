# Observed Fraud EDA

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Executive readout

- Eligible population: **284,807** transactions.
- Confirmed fraud labels: **492**, equal to **0.1727%**.
- Observed fraud amount: **60,127.97 cost units**, or **0.2390%** of total amount.
- Class imbalance: **577.9 legitimate transactions per fraud transaction**.
- Exact duplicate transaction IDs, invalid targets, negative amounts and missing model features: **0**.

## Ordered split

| split | rows | fraud_count | fraud_rate | first_period | last_period |
| --- | --- | --- | --- | --- | --- |
| test | 54807.0000 | 73.0000 | 0.0013 | 24.0000 | 29.0000 |
| train | 170000.0000 | 360.0000 | 0.0021 | 1.0000 | 17.0000 |
| validation | 60000.0000 | 59.0000 | 0.0010 | 18.0000 | 23.0000 |

The source no longer exposes the original `Time` field. `monitoring_period` preserves row ordering in blocks and is therefore used as a temporal-order proxy. It must not be interpreted as a real calendar period. Train uses periods 1-17, validation 18-23 and test 24-29. The final test population remains untouched until model lock.

## Senior interpretation

Accuracy is unsuitable because a model predicting every transaction as legitimate would exceed 99.8% accuracy while capturing no fraud. Primary evidence will be PR-AUC, fraud recall, fraud-amount recall, alert rate, false-positive workload and net benefit. Amount alone is retained only as a simple benchmark.

## Claim boundary

The observed PCA layer supports predictive benchmarking and realised amount-capture analysis. It does not support device, beneficiary, authentication, customer-behaviour or investigator reason-code claims.
