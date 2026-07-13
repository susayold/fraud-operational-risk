# Project 5 Limitations and Claim Boundaries

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

1. Observed PCA inputs support ranking but not semantic fraud reason codes.
2. The original timestamp is unavailable; monitoring-period ordering is a proxy.
3. The observed label is treated as transaction fraud; recoveries, delayed confirmation and investigator outcomes are unavailable.
4. Threshold costs, preventable loss and capacity are illustrative cost-unit assumptions.
5. Synthetic transaction controls, fraud types, investigations, incidents and losses are controls-testing simulations.
6. Friendly fraud is a separate post-transaction dispute label.
7. Operational disparity diagnostics are not legal or demographic fairness conclusions.
8. Project 3 context is synthetic and non-causal.
9. This is not a real-time platform, AML system, regulatory model or production authorisation engine.
10. Anomaly-model evaluation is event-count constrained. Isolation Forest PR-AUC varies from 0.0346 on validation to 0.0784 on test, with fewer than 75 fraud events in each split. It is included as a complementary challenger, not a stable standalone fraud-decision model.
11. Author automated self-validation passed, but independent organisational validation, production approval and release sign-off were not performed.
