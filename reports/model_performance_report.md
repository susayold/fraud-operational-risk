# Observed Model Performance Report

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Outcome

Champion: **logistic_class_weight**. It was selected without consulting final-test performance. Test PR-AUC is **0.7786**, materially more informative than accuracy under the 0.17% class prevalence.

## Test comparison

| model | model_role | pr_auc | roc_auc | precision | recall | fraud_amount_recall | alert_rate | brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistic_class_weight | Champion | 0.7786 | 0.9814 | 0.2844 | 0.8493 | 0.6936 | 0.0040 | 0.0005 |
| logistic_smote | Challenger/benchmark | 0.7370 | 0.9797 | 0.2460 | 0.8356 | 0.6920 | 0.0045 | 0.0006 |
| hist_gradient_boosting | Challenger/benchmark | 0.7095 | 0.9262 | 0.2415 | 0.7808 | 0.6237 | 0.0043 | 0.0005 |
| logistic_random_undersampling | Challenger/benchmark | 0.6980 | 0.9815 | 0.2531 | 0.8356 | 0.6629 | 0.0044 | 0.0007 |
| logistic_no_resampling | Transparent baseline | 0.6897 | 0.9714 | 0.2120 | 0.8219 | 0.6916 | 0.0052 | 0.0007 |
| isolation_forest | Challenger/benchmark | 0.0784 | 0.9487 | 0.1313 | 0.3562 | 0.0448 | 0.0036 | 0.4174 |
| pca_signal_simple_benchmark | Challenger/benchmark | 0.0576 | 0.9526 | 0.0913 | 0.2603 | 0.0306 | 0.0038 | 0.3435 |

## Champion selection versus tree challenger

Class-weighted Logistic Regression was selected on locked validation evidence. It exceeded HistGradientBoosting on validation PR-AUC (**0.7528** versus **0.7212**). The untouched test set then confirmed stronger PR-AUC (**0.7786** versus **0.7095**), fraud recall (**84.93%** versus **78.08%**), fraud-amount recall (**69.36%** versus **62.37%**) and Brier score (**0.000464** versus **0.000527**). The selection was not based on the final-test result.

## Anomaly-model stability

Isolation Forest achieved PR-AUC of **0.0346** on validation and **0.0784** on test. It remained above the simple PCA-signal benchmark on both splits (**0.0254** validation and **0.0576** test), but it was materially weaker than supervised candidates. Validation and test contain only **59** and **73** fraud events, so anomaly PR-AUC and fraud-amount capture are high-variance. Isolation Forest is retained only as a complementary challenger and control component, not as a standalone champion.

## Statistical uncertainty

Point estimates are directionally strong but uncertain because the untouched test set contains only **73** fraud events. Confidence intervals should be considered when interpreting differences between models.

| metric | point_estimate | ci_method | ci_low | ci_high | event_count | denominator |
| --- | --- | --- | --- | --- | --- | --- |
| fraud_recall | 0.8493 | Wilson 95% | 0.7500 | 0.9137 | 73.0000 | 73.0000 |
| precision | 0.2844 | Wilson 95% | 0.2287 | 0.3476 | 62.0000 | 218.0000 |
| pr_auc | 0.7786 | Bootstrap 95% | 0.6762 | 0.8718 | 73.0000 | 54807.0000 |
| fraud_amount_recall | 0.6936 | Bootstrap 95% | 0.4021 | 0.9512 | 73.0000 | 54807.0000 |

## Senior interpretation

The champion is a ranking benchmark, not a production fraud engine. Its value is measured by fraud and fraud amount captured at constrained alert rates. The logistic baseline and anomaly detector remain governed challengers. PCA features make the observed layer unsuitable for human-readable fraud reason codes; that capability belongs exclusively to the separately labelled synthetic controls-testing layer.
