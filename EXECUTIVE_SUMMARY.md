# Executive Summary

## Decision supported

Choose a fraud alert strategy that balances fraud capture, customer friction, investigation capacity and governance, while separating observed benchmark evidence from synthetic control-workflow evidence.

## Headline evidence

- 284,807 observed PCA-anonymized transactions and a separate 250,000-event synthetic control environment.
- Champion test PR-AUC: 0.7786.
- Locked test alert policy captures 84.93% of fraud transactions and 69.36% of fraud amount at 28.44% precision.
- Fraud-amount recall remains an Amber appetite exception.
- 15 governed rules, 250-alert/day capacity, 38 UAT, 18 SIT and 16 executable negative tests.

## Recommendation

Retain the locked alert policy as a benchmark candidate, explicitly accept or remediate the fraud-amount capture exception, add high-value controls and monitor workload, SLA, incidents and residual risk before any production consideration.

## Boundary

Observed performance belongs only to the anonymized benchmark. Interpretable control, workload and incident results belong to a separate synthetic environment.
