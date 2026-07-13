# Alert Prioritisation Methodology

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

Alert priority combines calibrated synthetic fraud probability, potential loss, detection confidence, customer vulnerability and rule severity. Critical and high-priority cases are processed before lower priority cases. `DECLINE` and `BLOCK_ACCOUNT` actions enter a 20% quality-assurance sample; automated `STEP_UP` enters human review only when score is at least 0.20. This separates automated control actions from investigator workload.

The locked capacity is 250 alerts per simulated day. Handling-time assumptions are 25, 18, 12 and 8 minutes for critical, high, medium and low alerts, with seeded variation. These are educational staffing proxies, not market benchmarks.
