# Operational Segment Disparity Diagnostic

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Result

**1 operational dimensions breached the 10 percentage-point review trigger.** A breach is a review flag, not proof of unlawful or demographic unfairness.

| dimension | group | transactions | fraud_events | max_dimension_gap_pp | required_action |
| --- | --- | --- | --- | --- | --- |
| transaction_frequency | High_frequency | 25759.0000 | 844.0000 | 55.2053 | Root-cause, business justification, mitigation and owner required |
| transaction_frequency | Low_normal_frequency | 224241.0000 | 2175.0000 | 55.2053 | Root-cause, business justification, mitigation and owner required |

## Root cause and action

| dimension | root_cause_driver | business_justification | mitigation | residual_risk | owner | status |
| --- | --- | --- | --- | --- | --- | --- |
| transaction_frequency | High-frequency is both a synthetic fraud-mechanism symptom and a direct velocity-control input; prevalence and feature design both contribute. | Velocity controls are intended to detect card testing and mule bursts, but a high false-positive/control rate is not acceptable without secondary evidence. | Require model or second-rule support for manual review, monitor high-frequency legitimate merchants separately, cap repetitive low-value alerts and test segment-specific thresholds. | Medium | Fraud Strategy with Conduct Risk review | OPEN_MONITORING_ACTION |

## Governance interpretation

Results are synthetic operational diagnostics. Each flagged dimension is decomposed into prevalence, feature-design and threshold effects, with business justification, mitigation, residual risk and accountable owner. Groups with fewer than 1,000 transactions or 20 fraud events are marked insufficient for fraud-capture comparison. A trigger does not establish legal or demographic unfairness.
