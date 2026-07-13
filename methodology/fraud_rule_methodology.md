# Fraud Rule Methodology

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

Rules use only observable synthetic controls-testing features. Hidden latent risks and observed PCA variables are prohibited from rule conditions and reason codes. Boundary operators are explicit and priority follows data exception, blacklist/emergency controls, high-severity deterministic rules, model/anomaly routing, step-up and allow.

Aggregate rules-only precision is **3.39%** and recall is **9.97%**. Both remain below 100%, which is required evidence that rules do not recreate the synthetic fraud label. Rule results are reviewed for overlap, customer friction and capacity rather than capture alone.

## Rule performance

| rule_id | rule_name | alert_rate | precision | fraud_recall | fraud_amount_recall | control_status |
| --- | --- | --- | --- | --- | --- | --- |
| FRD-030 | Extreme 10-minute velocity | 0.0078 | 0.0753 | 0.0484 | 0.0030 | Partially effective |
| FRD-040 | OTP failure | 0.0131 | 0.0274 | 0.0298 | 0.0479 | Tune / monitor |
| FRD-010 | Critical account takeover | 0.0047 | 0.0349 | 0.0136 | 0.0271 | Partially effective |
| FRD-032 | Card-testing burst | 0.0012 | 0.0962 | 0.0099 | 0.0002 | Partially effective |
| FRD-021 | Mule network concentration | 0.0027 | 0.0249 | 0.0056 | 0.0076 | Tune / monitor |
| FRD-060 | Night amount anomaly | 0.0043 | 0.0139 | 0.0050 | 0.0188 | Tune / monitor |
| FRD-050 | Geography-device mismatch | 0.0003 | 0.1867 | 0.0046 | 0.0067 | Effective |
| FRD-051 | Impossible travel proxy | 0.0010 | 0.0359 | 0.0030 | 0.0064 | Partially effective |
| FRD-031 | Amount spike and daily aggregation | 0.0028 | 0.0101 | 0.0023 | 0.0276 | Tune / monitor |
| FRD-001 | Known beneficiary blacklist | 0.0029 | 0.0096 | 0.0023 | 0.0015 | Tune / monitor |
| FRD-011 | Unsafe device high amount | 0.0005 | 0.0263 | 0.0010 | 0.0104 | Tune / monitor |
| FRD-020 | New beneficiary high risk | 0.0006 | 0.0185 | 0.0010 | 0.0079 | Tune / monitor |
| FRD-061 | Merchant-device risk | 0.0002 | 0.0769 | 0.0010 | 0.0081 | Partially effective |
| FRD-080 | Duplicate transaction | 0.0005 | 0.0080 | 0.0003 | 0.0000 | Tune / monitor |
| FRD-070 | Privileged override misuse | 0.0001 | 0.0000 | 0.0000 | 0.0000 | Tune / monitor |
