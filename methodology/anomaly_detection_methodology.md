# Observed Anomaly Detection Methodology

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

Isolation Forest is fitted only on a reproducible training sample after train-fitted standardisation. Its decision function is converted to an empirical anomaly percentile using the train distribution. It is a benchmark for unusual patterns, not proof of fraud and not automatically selected as champion. Its incremental contribution is tested again in the synthetic hybrid controls layer.
