# Alert Operations and Capacity Report

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Base outcome

- Investigation queue: **5,537 alerts** across 30 simulated arrival days.
- Average incoming volume: **184.6 alerts/day** versus locked capacity of **250**.
- Maximum end-of-day backlog: **0 alerts**.
- Confirmed synthetic fraud investigations: **419**.
- Legitimate transactions in queue (false-positive workload proxy): **5,057**.
- SLA breach rate: **0.00%**.

## Capacity sensitivity

| scenario | alerts_per_day | capacity_per_day | capacity_utilisation | daily_backlog_addition | required_analysts_7_5h | status |
| --- | --- | --- | --- | --- | --- | --- |
| Base | 184.5667 | 250.0000 | 0.7383 | 0.0000 | 6.0000 | PASS |
| Alert volume +25% | 230.7083 | 250.0000 | 0.9228 | 0.0000 | 8.0000 | PASS |
| Alert volume +50% | 276.8500 | 250.0000 | 1.1074 | 26.8500 | 9.0000 | BREACH |
| Handling time +20% | 184.5667 | 250.0000 | 0.7383 | 0.0000 | 8.0000 | PASS |
| Analyst absence 20% | 184.5667 | 200.0000 | 0.9228 | 0.0000 | 6.0000 | PASS |
| Threshold tightened | 249.1650 | 250.0000 | 0.9967 | 0.0000 | 9.0000 | PASS |
| Critical incident spike | 295.3067 | 225.0000 | 1.3125 | 70.3067 | 12.0000 | BREACH |

## Priority queue efficiency

| review_priority | alerts | fraud_labels | fraud_precision | legitimate_outcomes | non_fraud_alerts |
| --- | --- | --- | --- | --- | --- |
| CRITICAL | 152.0000 | 2.0000 | 1.32% | 126.0000 | 150.0000 |
| HIGH | 1527.0000 | 51.0000 | 3.34% | 1205.0000 | 1476.0000 |
| MEDIUM | 3858.0000 | 427.0000 | 11.07% | 2777.0000 | 3431.0000 |

## Critical-queue efficiency

Priority is severity-based rather than probability-ranked. The CRITICAL queue is dominated by simulated blacklist and privileged-override controls: RC_BLACKLIST: 148, RC_OVERRIDE_MISUSE: 4. Only **2** of the **152** alerts carry the synthetic fraud label.

The **82.89%** LEGITIMATE outcome share is one investigation disposition, not the complete false-positive rate; **150** of **152** CRITICAL alerts are non-fraud in the synthetic label. This is a material control-efficiency weakness. The rules should retain severity protection, but require blacklist-data validation, quality assurance, precision monitoring and tuning. High priority must not be interpreted as high predictive precision.

Management action: Owner = Fraud Strategy / Data Owner. Validate blacklist-generation quality, separate confirmed-list hits from proxy hits, monitor precision and require dual approval before rule tuning.

## Management interpretation

The queue is governed separately from automated step-up/decline actions. A capacity breach requires threshold/rule tuning, temporary staffing, priority protection for critical alerts and explicit backlog risk acceptance. The project does not claim that simulated handling times or outcomes represent a bank's actual fraud operation.
