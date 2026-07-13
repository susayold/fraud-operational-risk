# Probability Calibration Report

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Decision

Platt/sigmoid calibration was required because the champion uses class weighting and its raw probability level is not a reliable prospective fraud probability. Isotonic calibration was rejected because validation contains only **59 fraud cases**, below the locked 200-event gate.

## Test result

- Observed test prevalence: **0.1332%**.
- Mean calibrated test probability: **0.1094%**.
- Absolute gap: **0.0238%**.
- Relative gap: **17.85%**.
- Brier score: **0.000464**.

The calibrated probability may be used only for clearly labelled prospective sensitivity. Realised threshold economics remains based on observed labels and realised transaction amount.
