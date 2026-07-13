# Synthetic Controls Data Report

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Population

- Transactions: **250,000**.
- Synthetic transaction fraud cases: **3,019** (1.21%).
- Friendly-fraud disputes: **15,000**, evaluated in a separate post-transaction claim layer.
- Hidden-label intercept: `-11.203206`, calibrated before label sampling to an expected 1.2% transaction-fraud rate.

## Synthetic model test evidence

| score | pr_auc | roc_auc | brier_score | mean_score | observed_fraud_rate |
| --- | --- | --- | --- | --- | --- |
| raw | 0.0616 | 0.8011 | 0.1584 | 0.3455 | 0.0113 |
| platt_calibrated | 0.0616 | 0.8011 | 0.0109 | 0.0124 | 0.0113 |
| anomaly | 0.0178 | 0.6112 | 0.3305 | 0.4988 | 0.0113 |

## Anti-circularity

| test_id | measure | value | status |
| --- | --- | --- | --- |
| label_is_stochastic | fraud_label sampled from latent probability | 3019.0000 | PASS |
| obvious_rule_precision_below_100pct | precision | 0.0201 | PASS |
| obvious_rule_recall_below_100pct | recall | 0.2206 | PASS |
| fraud_without_obvious_rule_exists | fraud rows not firing obvious rule | 2353.0000 | PASS |
| legitimate_rule_hits_exist | legitimate rows firing obvious rule | 32499.0000 | PASS |
| hidden_fields_excluded_from_model | hidden feature count used | 0.0000 | PASS |

Hidden latent mechanisms create stochastic labels. Observable symptoms are imperfect, legitimate transactions can trigger controls, and fraud can avoid obvious indicators. Hidden variables are excluded from detection features and reason codes.

## Claim boundary

All performance in this layer is synthetic controls-testing evidence. It cannot be presented as observed fraud performance or a production control result.
