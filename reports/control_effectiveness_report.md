# Control Effectiveness Report

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Senior conclusion

Controls are evaluated on fraud capture, amount capture, false positives, net benefit, customer friction, capacity and failure risk. High capture alone is not sufficient: controls with weak precision, excessive friction or no unique contribution require tuning or retirement.

| rule_id | rule_name | precision | fraud_recall | fraud_amount_captured | net_benefit | control_status | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FRD-031 | Amount spike and daily aggregation | 0.0101 | 0.0023 | 14223.0500 | 5133.1350 | Tune / monitor | Tune threshold and monitor overlap |
| FRD-011 | Unsafe device high amount | 0.0263 | 0.0010 | 5352.8100 | 2954.9670 | Tune / monitor | Tune threshold and monitor overlap |
| FRD-061 | Merchant-device risk | 0.0769 | 0.0010 | 4173.0600 | 2654.1420 | Partially effective | Tune threshold and monitor overlap |
| FRD-050 | Geography-device mismatch | 0.1867 | 0.0046 | 3462.2200 | 1926.5540 | Effective | Retain and monitor |
| FRD-020 | New beneficiary high risk | 0.0185 | 0.0010 | 4096.1300 | 1739.2910 | Tune / monitor | Tune threshold and monitor overlap |
| FRD-010 | Critical account takeover | 0.0349 | 0.0136 | 13991.3200 | 1650.9240 | Partially effective | Tune threshold and monitor overlap |
| FRD-051 | Impossible travel proxy | 0.0359 | 0.0030 | 3317.7500 | 583.4250 | Partially effective | Tune threshold and monitor overlap |
| FRD-070 | Privileged override misuse | 0.0000 | 0.0000 | 0.0000 | -154.0000 | Tune / monitor | Tune threshold and monitor overlap |
| FRD-060 | Night amount anomaly | 0.0139 | 0.0050 | 9698.4400 | -748.0920 | Tune / monitor | Tune threshold and monitor overlap |
| FRD-080 | Duplicate transaction | 0.0080 | 0.0003 | 0.5800 | -872.5940 | Tune / monitor | Tune threshold and monitor overlap |
| FRD-021 | Mule network concentration | 0.0249 | 0.0056 | 3944.4300 | -1992.8990 | Tune / monitor | Tune threshold and monitor overlap |
| FRD-032 | Card-testing burst | 0.0962 | 0.0099 | 95.1600 | -2057.3880 | Partially effective | Tune threshold and monitor overlap |
| FRD-001 | Known beneficiary blacklist | 0.0096 | 0.0023 | 753.2500 | -4540.7250 | Tune / monitor | Tune threshold and monitor overlap |
| FRD-040 | OTP failure | 0.0274 | 0.0298 | 24675.4400 | -5535.1920 | Tune / monitor | Tune threshold and monitor overlap |
| FRD-030 | Extreme 10-minute velocity | 0.0753 | 0.0484 | 1563.3600 | -12186.6480 | Partially effective | Tune threshold and monitor overlap |

All results are synthetic controls-testing evidence. Production effectiveness would require actual alert outcomes, control exposure, change history and independent validation.
