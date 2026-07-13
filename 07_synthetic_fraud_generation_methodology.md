# Synthetic Fraud Generation Methodology

## Objective

Create an interpretable controls-testing environment that supports deterministic rules, reason codes, alert queues, incident simulation, KRIs and UAT/SIT.

## Entity Design

Synthetic layer will contain:

- customers;
- devices;
- beneficiaries;
- merchants/categories;
- transactions;
- dispute/claim records for friendly fraud;
- incidents and control failures.

## Generation Flow

1. Generate customers with tenure, transaction frequency and synthetic risk segment.
2. Generate devices with trusted/new status and relationship to customers.
3. Generate beneficiaries with age, history and risk flags.
4. Generate transactions with amount, channel, geography, merchant category and timestamp.
5. Generate hidden latent fraud archetype and latent fraud probability.
6. Generate observable features separately from the hidden label.
7. Generate synthetic fraud label using stochastic outcome logic.
8. Generate deterministic rule triggers from observable fields only.
9. Generate alert decision and investigation outcome.
10. Generate incidents and control failures after transactions.

## Required Fraud Archetypes

- account takeover style transaction risk;
- new beneficiary / mule-risk style transaction risk;
- high-velocity transaction risk;
- cross-border unusual activity risk;
- merchant/category exposure risk.

Friendly fraud is handled separately as post-transaction dispute/claim risk.

## Anti-Circularity Controls

The label generation code must keep hidden drivers separate from rule conditions. Detection rules cannot read hidden fraud archetype or latent fraud probability directly.

Validation must prove that rules do not perfectly recreate the label.
