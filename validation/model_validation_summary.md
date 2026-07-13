# Model Validation Summary

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Conclusion

Observed champion `logistic_class_weight` has test PR-AUC **0.7786**, ROC-AUC **0.9814**, validation-locked test fraud recall **84.93%** and fraud-amount recall **69.36%**. Probability is Platt-calibrated outside test. Test was not used for model, calibration or threshold selection.

Data quality, split reconciliation, discrimination, calibration, threshold economics, stability and challenger comparison are evidenced in the linked CSV outputs. Remaining limitations are missing original timestamp semantics, small validation fraud count and PCA feature interpretability. Model use is restricted to educational benchmarking.
