# Operational Segment Fairness Specification

## Scope

This is an operational segment diagnostic. It is not a legal fairness assessment and does not claim demographic fairness.

## Minimum Comparison Groups

- new versus established customers;
- domestic versus cross-border transactions;
- trusted versus new device;
- low versus high transaction-frequency customers;
- synthetic customer segment, where non-sensitive and explicitly synthetic.

## Metrics

- fraud recall / true-positive rate;
- false-positive rate;
- precision;
- step-up rate;
- manual-review rate;
- decline/block rate;
- customer-friction cost.

## Review Trigger

Flag absolute group gap greater than 10 percentage points between material comparison groups.

Also report rate ratios where useful.

## Minimum Evidence Rule

At least 1,000 transactions per group and at least 20 fraud events are required for fraud-capture comparisons.

If the threshold is breached, document driver, business justification, mitigation, owner and residual risk.

Approved wording if no breach is identified:

No material disparity was identified within the tested operational segments.
