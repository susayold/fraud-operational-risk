# Fraud Risk Committee Memo

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Executive conclusion

The observed benchmark contains 284,807 transactions and 492 fraud cases. `logistic_class_weight` is champion with test PR-AUC **0.7786**. The validation-selected **top 0.50% alert policy** captures **84.93%** of test fraud transactions and **69.36%** of test fraud amount at precision **28.44%**.

## Economics and workload

Test realised net benefit is **2,349.01 cost units** under frozen illustrative assumptions. The separate synthetic controls environment creates **5,537 investigation alerts**; capacity and SLA results are workload proxies, not observed operations.

## Synthetic hybrid economics context

The final hybrid actionable strategy produces **3,056.5 cost units** of simulated net benefit on **41,632 synthetic test transactions**, equivalent to approximately **0.073 cost units per transaction**.

This result must not be linearly scaled to production. The synthetic test fraud prevalence is **1.13%**, compared with **0.17%** in the observed PCA population. Actual value would depend on production fraud prevalence, transaction amounts, preventable-loss rates, recoveries, rule precision, operations costs and customer-friction costs.

Observed threshold economics and synthetic hybrid economics are separate analytical layers.

## Controls

Fifteen observable rules cover device, beneficiary, velocity, authentication, geography, behaviour, override and duplicate patterns. Rule precision/recall are imperfect by design, and incremental value is measured against model-only and anomaly-only strategies.

## Decisions required

1. Approve the observed threshold as an educational backtest recommendation only.
2. Require production re-estimation using real timestamp throughput, recoveries and customer outcomes.
3. Retain hard release blocks for invalid score scale and missing critical inputs.
4. Protect critical alert capacity and require explicit acceptance for backlog breaches.
5. Review flagged operational-segment disparities before any analogous production use.
