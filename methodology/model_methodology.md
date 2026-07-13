# Observed Fraud Model Methodology

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Design

The benchmark uses `v1`-`v28` plus `log(1 + amount)`. Ordered monitoring-period proxy splits are train 1-17, validation 18-23 and test 24-29. Scaling, sampling and fitting occur on train only. Platt calibration is fitted on the true-prevalence validation population. The test set is used once after model and threshold design.

Five supervised strategies were compared: no-resampling logistic regression, class-weighted logistic regression, training-only random undersampling, training-only SMOTE and class-weighted histogram gradient boosting. Isolation Forest and PCA absolute-signal ordering are non-supervised/simple benchmarks.

## Selection

Champion: **logistic_class_weight**. Selection used validation evidence only, combining PR-AUC, fraud-amount capture, recall and workload. The test PR-AUC is **0.7786** and test fraud-amount recall at the validation-derived 0.5% alert threshold is **69.36%**.

## Leakage controls

- Test rows were excluded from training, calibration and threshold selection.
- SMOTE and undersampling were applied only inside the training pipeline.
- Amount is an authorisation-time field; fraud labels, amount bands and monitoring-period identifiers are not model features.
- `monitoring_period` is a row-order proxy, not a timestamp and not a model feature.
