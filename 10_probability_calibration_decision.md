# Probability Calibration Decision

## Decision

Probability calibration is mandatory when model probabilities are used in transaction-level expected-loss or net-benefit economics.

Default method:

Platt / sigmoid calibration.

Isotonic calibration may be used only if the calibration population contains at least 200 fraud observations or cross-validated evidence clearly supports it.

## Fitting Rule

Calibration must be fitted on validation/calibration data with true fraud prevalence. It must never be fitted on the final test set.

## Trigger Conditions

Calibration review is triggered when:

- training data was over-sampled or under-sampled;
- class weights materially changed probability interpretation;
- mean predicted probability differs from observed validation fraud rate by more than 0.05 percentage points absolute or 20% relative;
- calibration slope/intercept is materially poor;
- probability is used in transaction-level expected-loss economics.

## Required Test Reporting

Mean calibrated probability on the untouched test set must be compared with the observed test fraud rate. Approximately 0.17% is an expected dataset characteristic, not a hard-coded target.
