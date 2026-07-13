# Threshold Economics Decision

## Locked Base Assumptions

| Assumption | Base value | Status |
|---|---:|---|
| Investigation cost per alert | 5.00 cost units | Locked before model review |
| Preventable loss rate | 70% of captured fraud amount | Locked before model review |
| Alert capacity | 250 alerts per day | Locked before model review |
| False-positive customer-friction cost | 2.00 cost units per false-positive action | Locked before model review |

These are educational cost-unit assumptions, not market benchmarks.

## Frozen Candidate Threshold Grid

Primary grid is expressed as alert rate:

0.05%, 0.10%, 0.20%, 0.50%, 1.00%, 2.00%, 5.00% of transactions alerted.

Model score cutoffs will be derived from validation-set quantiles corresponding to this grid. The final test set must remain untouched during threshold selection.

## Net Benefit Formula

Captured fraud amount = sum(amount where alerted and fraud_flag = 1)

Prevented loss = captured fraud amount x preventable_loss_rate

Investigation cost = alert_count x investigation_cost_per_alert

False-positive friction cost = false_positive_count x false_positive_friction_cost

Net benefit = prevented loss - investigation cost - false-positive friction cost

Capacity breach = alerts_per_day > alert_capacity_per_day

## Governance Rule

Primary threshold recommendation equals the result under the frozen Base assumptions.

Alternative assumptions are sensitivity results, not replacements for the Base recommendation.

## Formalised Selection Hierarchy

Eligible validation candidate:

1. Capacity status = PASS.
2. Backtest net benefit under disclosed cost assumptions > 0.
3. Fraud transaction recall >= 80%.
4. Precision >= 10%.
5. Fraud amount recall:
   - PASS if >=80%.
   - AMBER exception if 60%-80%.

Selection uses PASS candidates first. If no PASS candidate exists, eligible AMBER candidates may be used. Within the selected pool, maximise validation backtest net benefit under disclosed cost assumptions and use fraud-amount recall and precision as tie breakers. The final test set must not influence selection.

Formalised during v1.0.1 public remediation. Underlying code and selected threshold unchanged; not backdated as the original Phase 0 lock.

Any post-lock change requires a versioned change request, owner, approval, reason, before/after threshold impact and updated change log.
