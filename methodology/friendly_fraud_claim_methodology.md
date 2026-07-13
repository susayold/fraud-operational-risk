# Friendly Fraud Claim Methodology

## Decision

Friendly fraud / dispute abuse is a post-transaction claim problem. It must not be generated like real-time account takeover, velocity fraud or beneficiary-risk transaction fraud.

## Required Dataset

`data/synthetic/synthetic_disputes.csv`

Required fields:

- `dispute_id`
- `transaction_id`
- `claim_date`
- `days_to_claim`
- `claim_reason`
- `prior_dispute_count`
- `merchant_category`
- `delivery_confirmation_proxy`
- `claim_amount`
- `friendly_fraud_label`
- `claim_outcome`

## Control Objective

Friendly-fraud controls support claim review, merchant review and repeat-dispute monitoring. They do not support real-time transaction blocking in this MVP unless a separate governance decision is made.

## Implementation Status

Implemented. `data/synthetic/synthetic_disputes.csv` contains 15,000 post-transaction claims with claim timing, prior-dispute history, merchant context, delivery-confirmation proxy, claim amount, a separate friendly-fraud label and claim outcome. Results are reported in `outputs/friendly_fraud_claim_risk_summary.csv`.

`transaction_fraud_label` and `friendly_fraud_label` remain separate. Friendly-fraud evidence is used only for post-transaction claim review, evidence requests, merchant review and account monitoring; it never triggers a real-time transaction decline in this project.
