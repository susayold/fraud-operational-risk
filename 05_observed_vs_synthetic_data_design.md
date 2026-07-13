# Observed vs Synthetic Data Design

## Core Principle

Project 5 uses two data layers because one public observed fraud dataset cannot answer every fraud-management question.

| Layer | Data status | Main use | Permitted claim | Prohibited claim |
|---|---|---|---|---|
| Layer A | Observed | Predictive benchmark and class-imbalance modelling | Observed fraud classification performance, PR-AUC, fraud amount capture | Device rule, beneficiary rule, OTP failure, account takeover reason code |
| Layer B | Synthetic | Controls testing and operational governance | Rule logic, alert workflow, UAT/SIT, KRI, incident process | Real-world fraud model performance |

## Mandatory Output Fields

Every downstream output must include:

- `data_layer`
- `data_status`
- `source_type`
- `claim_boundary`

Allowed values include Observed, Derived, Proxy, Synthetic and Unavailable.

## Senior Risk Rationale

The split prevents two common portfolio errors:

1. Using PCA variables to invent business explanations that the data cannot support.
2. Presenting synthetic rule performance as if it were observed real-world fraud performance.

Project 5 can still tell one coherent story: observed data proves modelling discipline; synthetic data proves risk-system and operational-control thinking.
