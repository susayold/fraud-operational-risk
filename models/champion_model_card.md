# Observed Champion Model Card

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Intended use

Observed PCA fraud-classification benchmark and ranking input for realised threshold economics.

## Champion

`logistic_class_weight` selected on validation evidence. Test PR-AUC: **0.7786**; ROC-AUC: **0.9814**; recall at locked validation 0.5% alert threshold: **84.93%**; precision: **28.44%**; fraud-amount recall: **69.36%**.

## Calibration

Platt calibration used the validation population with original fraud prevalence. On test, observed fraud rate is **0.1332%** and mean calibrated probability is **0.1094%**. Test was not used to fit calibration.

## Prohibited use

No production authorisation, customer adverse action, AML decision, semantic interpretation of PCA variables or claim that amount captured equals loss prevented.

## Key limitations

The original timestamp is unavailable; the ordered split uses a proxy. Validation has only 59 fraud cases. PCA variables prevent business-level reason codes, and the public benchmark can differ from live payment populations.
