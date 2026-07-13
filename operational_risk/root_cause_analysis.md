# Operational Incident Root Cause Analyses

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## RCA 1: Model score delivered as 0-100

- **Event:** Model score delivered as 0-100.
- **Impact:** 125 customer/transaction records; gross loss proxy 42,000.00; net loss proxy 34,000.00 cost units.
- **Detection:** KRI threshold, validation check or investigation escalation.
- **Immediate containment:** Invoke governed fallback, isolate affected component and preserve logs.
- **Root cause:** Data weakness in Model scoring API.
- **Contributing factors:** Incomplete pre-release guardrail, dependency concentration and delayed operational detection.
- **Corrective action:** Repair configuration/data flow and reconcile all affected decisions.
- **Preventive action:** Add boundary test, monitoring trigger and release evidence requirement.
- **Owner:** Operational Risk.
- **Due date:** 2026-02-06.
- **Validation evidence:** SIT regression, negative test and independent checklist sign-off.
- **Residual risk:** Medium until action closure.

## RCA 2: Velocity feature stopped refreshing

- **Event:** Velocity feature stopped refreshing.
- **Impact:** 48 customer/transaction records; gross loss proxy 18,500.00; net loss proxy 16,000.00 cost units.
- **Detection:** KRI threshold, validation check or investigation escalation.
- **Immediate containment:** Invoke governed fallback, isolate affected component and preserve logs.
- **Root cause:** Data weakness in Velocity service.
- **Contributing factors:** Incomplete pre-release guardrail, dependency concentration and delayed operational detection.
- **Corrective action:** Repair configuration/data flow and reconcile all affected decisions.
- **Preventive action:** Add boundary test, monitoring trigger and release evidence requirement.
- **Owner:** Fraud Operations.
- **Due date:** 2026-03-13.
- **Validation evidence:** SIT regression, negative test and independent checklist sign-off.
- **Residual risk:** Medium until action closure.

## RCA 3: New-device rule alert spike

- **Event:** New-device rule alert spike.
- **Impact:** 310 customer/transaction records; gross loss proxy 9,200.00; net loss proxy 9,200.00 cost units.
- **Detection:** KRI threshold, validation check or investigation escalation.
- **Immediate containment:** Invoke governed fallback, isolate affected component and preserve logs.
- **Root cause:** Rule configuration weakness in Decision engine.
- **Contributing factors:** Incomplete pre-release guardrail, dependency concentration and delayed operational detection.
- **Corrective action:** Repair configuration/data flow and reconcile all affected decisions.
- **Preventive action:** Add boundary test, monitoring trigger and release evidence requirement.
- **Owner:** Fraud Operations.
- **Due date:** 2026-03-18.
- **Validation evidence:** SIT regression, negative test and independent checklist sign-off.
- **Residual risk:** High until action closure.

## RCA 4: Legitimate payroll transactions blocked

- **Event:** Legitimate payroll transactions blocked.
- **Impact:** 640 customer/transaction records; gross loss proxy 15,500.00; net loss proxy 8,300.00 cost units.
- **Detection:** KRI threshold, validation check or investigation escalation.
- **Immediate containment:** Invoke governed fallback, isolate affected component and preserve logs.
- **Root cause:** Rule configuration weakness in Payments rules.
- **Contributing factors:** Incomplete pre-release guardrail, dependency concentration and delayed operational detection.
- **Corrective action:** Repair configuration/data flow and reconcile all affected decisions.
- **Preventive action:** Add boundary test, monitoring trigger and release evidence requirement.
- **Owner:** Fraud Operations.
- **Due date:** 2026-03-23.
- **Validation evidence:** SIT regression, negative test and independent checklist sign-off.
- **Residual risk:** Medium until action closure.

## RCA 5: Device intelligence vendor outage

- **Event:** Device intelligence vendor outage.
- **Impact:** 820 customer/transaction records; gross loss proxy 26,500.00; net loss proxy 22,500.00 cost units.
- **Detection:** KRI threshold, validation check or investigation escalation.
- **Immediate containment:** Invoke governed fallback, isolate affected component and preserve logs.
- **Root cause:** Vendor weakness in Device vendor.
- **Contributing factors:** Incomplete pre-release guardrail, dependency concentration and delayed operational detection.
- **Corrective action:** Repair configuration/data flow and reconcile all affected decisions.
- **Preventive action:** Add boundary test, monitoring trigger and release evidence requirement.
- **Owner:** Fraud Operations.
- **Due date:** 2026-03-28.
- **Validation evidence:** SIT regression, negative test and independent checklist sign-off.
- **Residual risk:** Medium until action closure.

## RCA 6: Duplicate transactions generated duplicate alerts

- **Event:** Duplicate transactions generated duplicate alerts.
- **Impact:** 390 customer/transaction records; gross loss proxy 7,600.00; net loss proxy 5,100.00 cost units.
- **Detection:** KRI threshold, validation check or investigation escalation.
- **Immediate containment:** Invoke governed fallback, isolate affected component and preserve logs.
- **Root cause:** System weakness in Alert gateway.
- **Contributing factors:** Incomplete pre-release guardrail, dependency concentration and delayed operational detection.
- **Corrective action:** Repair configuration/data flow and reconcile all affected decisions.
- **Preventive action:** Add boundary test, monitoring trigger and release evidence requirement.
- **Owner:** Fraud Operations.
- **Due date:** 2026-04-02.
- **Validation evidence:** SIT regression, negative test and independent checklist sign-off.
- **Residual risk:** Medium until action closure.

## RCA 7: Investigator backlog delayed fraud action

- **Event:** Investigator backlog delayed fraud action.
- **Impact:** 190 customer/transaction records; gross loss proxy 33,800.00; net loss proxy 28,800.00 cost units.
- **Detection:** KRI threshold, validation check or investigation escalation.
- **Immediate containment:** Invoke governed fallback, isolate affected component and preserve logs.
- **Root cause:** Capacity weakness in Case management.
- **Contributing factors:** Incomplete pre-release guardrail, dependency concentration and delayed operational detection.
- **Corrective action:** Repair configuration/data flow and reconcile all affected decisions.
- **Preventive action:** Add boundary test, monitoring trigger and release evidence requirement.
- **Owner:** Fraud Operations.
- **Due date:** 2026-04-07.
- **Validation evidence:** SIT regression, negative test and independent checklist sign-off.
- **Residual risk:** Medium until action closure.

## RCA 8: Override misuse bypassed high-risk block

- **Event:** Override misuse bypassed high-risk block.
- **Impact:** 37 customer/transaction records; gross loss proxy 68,000.00; net loss proxy 56,000.00 cost units.
- **Detection:** KRI threshold, validation check or investigation escalation.
- **Immediate containment:** Invoke governed fallback, isolate affected component and preserve logs.
- **Root cause:** Governance weakness in Decision override.
- **Contributing factors:** Incomplete pre-release guardrail, dependency concentration and delayed operational detection.
- **Corrective action:** Repair configuration/data flow and reconcile all affected decisions.
- **Preventive action:** Add boundary test, monitoring trigger and release evidence requirement.
- **Owner:** Operational Risk.
- **Due date:** 2026-03-13.
- **Validation evidence:** SIT regression, negative test and independent checklist sign-off.
- **Residual risk:** Medium until action closure.
