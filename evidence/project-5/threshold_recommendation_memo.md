# Observed Threshold Recommendation Memo

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Recommendation

Use the validation-selected **top 0.50% alert-rate policy**, equivalent to calibrated score threshold **0.004029** for this benchmark version.

## Validation rationale

- Alerts: **300** or **50.0 per monitoring-period proxy**.
- Fraud recall: **81.36%**.
- Fraud-amount recall: **63.46%**.
- Precision: **16.00%**.
- Backtest net benefit under disclosed cost assumptions: **3,431.07 cost units**.
- Capacity: **PASS**.

## Formal threshold-selection hierarchy

Eligible validation candidate:

1. Capacity status = PASS.
2. Backtest net benefit under disclosed cost assumptions > 0.
3. Fraud transaction recall >= 80%.
4. Precision >= 10%.
5. Fraud amount recall:
   - PASS if >=80%.
   - AMBER exception if 60%-80%.

Selection uses PASS candidates first. If no PASS candidate exists, eligible AMBER candidates may be used. Within the selected pool, the project maximises validation backtest net benefit under disclosed cost assumptions and uses fraud-amount recall and precision as tie breakers. The final test set must not influence selection.

This hierarchy was formalised during v1.0.1 public remediation. The underlying code and selected threshold were unchanged, and this is not backdated as the original Phase 0 lock.

## Untouched test confirmation

- Actual alert rate: **0.40%**.
- Fraud recall: **84.93%**.
- Fraud-amount recall: **69.36%**.
- Precision: **28.44%**.
- Backtest net benefit under disclosed cost assumptions: **2,349.01 cost units**.

This is an observed historical backtest recommendation under illustrative cost assumptions. It is not a live authorisation threshold and requires re-estimation against real calendar throughput, recoveries, customer outcomes and investigator capacity before production use.

The recommendation prioritises a balanced risk candidate over the absolute net-benefit maximum. Where fraud-amount recall remains Amber rather than Green, implementation requires documented Risk Committee acceptance and a complementary high-value/rules strategy.
