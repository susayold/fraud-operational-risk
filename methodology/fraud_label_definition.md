# Fraud Label Definition

## Layer A - Observed PCA Benchmark

Observed fraud label:

`fraud_flag = 1` means the transaction is labelled fraud in the public observed dataset.

`fraud_flag = 0` means the transaction is labelled non-fraud in the public observed dataset.

This label is suitable for model benchmarking, PR-AUC, recall, precision and fraud amount capture. It is not suitable for explaining fraud reason codes because the explanatory features are PCA-transformed.

## Layer B - Synthetic Transaction Fraud

Synthetic fraud labels must be generated from latent fraud mechanisms and stochastic outcomes, not copied from detection rules.

Allowed hidden drivers:

- account takeover propensity;
- unusual beneficiary risk;
- abnormal device behaviour;
- cross-border transaction stress;
- velocity spike;
- merchant/category exposure;
- customer-history risk.

Observable rule features must be generated separately from the hidden fraud label. A rule can help detect fraud, but it must not define fraud by itself.

## Anti-Circularity Standard

The following must be true after synthetic generation:

- rule precision is less than 100%;
- rule recall is less than 100%;
- legitimate transactions can trigger controls;
- fraud transactions can avoid obvious rules;
- model or anomaly score can add value beyond deterministic rules;
- deterministic rules can add governance value beyond model score.

## Friendly Fraud / Dispute Abuse

Friendly fraud is not a real-time transaction fraud label. It is a post-transaction dispute or claim-risk outcome. It must be generated and evaluated in a separate dispute dataset.
