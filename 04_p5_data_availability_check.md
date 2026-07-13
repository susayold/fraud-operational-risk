# Project 5 Data Availability Check

Generated: 2026-07-11 03:35:36

## Available Project 0 Sources

| Layer | Path | Status | Use |
|---|---|---|---|
| Raw observed | Project 0 canonical source | Available in Project 0 data pool | Source lineage; current copy has PCA fields, Amount and Class but not Time |
| Silver observed | Project 0 canonical silver fraud source | Available in Project 0 data pool | Primary Project 5 observed benchmark input |
| Gold KRI | Project 0 canonical gold KRI source | Available in Project 0 data pool | Reference KRI aggregation from Project 0 |

## Observed Data Profile

| Metric | Value |
|---|---:|
| Rows | 284,807 |
| Fraud cases | 492 |
| Non-fraud cases | 284,315 |
| Fraud rate | 0.1727% |
| Transaction amount | 25,162,590.01 cost units |
| Fraud amount | 60,127.97 cost units |
| Minimum amount | 0.00 |
| Maximum amount | 25,691.16 |
| Monitoring period range | 1 to 29 |
| Duplicate transaction IDs | 0 |

## Availability Decision

The observed fraud benchmark is available and sufficient for Phase 1 modelling. The dataset has extreme class imbalance, which is appropriate for PR-AUC, recall/precision, fraud amount capture and threshold economics.

The current Project 0 raw copy does not expose original `Time`. Project 5 will use `monitoring_period` as a documented time-order/stability proxy unless the original Time field is recovered later.

## Data Claim Boundary

Observed PCA data supports predictive benchmarking only. It does not support reason-code or rule explanations such as device trust, cross-border risk, beneficiary age, OTP failure or account takeover. Those concepts belong only to the synthetic controls-testing layer.
