# Transparent Logistic Challenger Model Card

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

The transparent baseline is `logistic_no_resampling`. It provides a stable linear comparator with test PR-AUC **0.6897** and test ROC-AUC **0.9714**. It is not used for business explanations because the inputs remain PCA-transformed. Challenger promotion would require materially better ranking or calibration without breaching workload, stability and governance controls.
