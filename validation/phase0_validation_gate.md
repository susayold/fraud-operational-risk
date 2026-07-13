# Phase 0 Validation Gate

## Gate Question

Can the observed PCA data and the proposed synthetic controls layer be combined without mixing claims, creating label leakage or building circular fraud rules, while threshold assumptions, probability calibration, friendly-fraud timing and fairness diagnostics are locked before model review?

## Phase 0 Answer

Yes - PASS with explicit claim boundaries.

## PASS Conditions

- Observed PCA data is used only for observed fraud benchmark performance.
- Synthetic controls data is used only for interpretable controls, reason codes, alert workflow and governance.
- Mandatory output fields are locked: data_layer, data_status, source_type and claim_boundary.
- Threshold economics assumptions are frozen before model review.
- Probability calibration policy is frozen before model review.
- Friendly fraud is separated as post-transaction dispute/claim risk.
- Operational segment fairness diagnostics are specified before modelling.
- No model training has been performed in Phase 0.

## Build Authorization

Phase 1 observed benchmark may begin only after the validation checks in `validation/phase0_validation_gate.csv` show no unresolved critical FAIL.
