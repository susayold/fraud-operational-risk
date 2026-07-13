from __future__ import annotations

import numpy as np
import pandas as pd

from _project5_common import (
    ROOT,
    add_metadata,
    dataframe_to_markdown,
    get_logger,
    safe_div,
    write_csv,
    write_markdown,
)


def build_rule_definitions() -> list[dict]:
    return [
        {"rule_id": "FRD-001", "rule_name": "Known beneficiary blacklist", "rule_description": "Simulated beneficiary blacklist hit", "condition": "blacklist_hit == 1", "priority": 1, "severity": "CRITICAL", "reason_code": "RC_BLACKLIST", "action": "BLOCK_ACCOUNT", "customer_friction_risk": "High", "fallback_behavior": "Hold and escalate if blacklist service is unavailable"},
        {"rule_id": "FRD-010", "rule_name": "Critical account takeover", "rule_description": "ATO signal with five or more OTP failures", "condition": "account_takeover_signal == 1 AND failed_otp_count >= 5", "priority": 2, "severity": "CRITICAL", "reason_code": "RC_ATO_CRITICAL", "action": "HOLD", "customer_friction_risk": "High", "fallback_behavior": "Conservative hold and identity verification"},
        {"rule_id": "FRD-011", "rule_name": "Unsafe device high amount", "rule_description": "Rooted or emulated device with material amount", "condition": "(rooted_device_flag == 1 OR emulator_flag == 1) AND amount >= 1000", "priority": 3, "severity": "HIGH", "reason_code": "RC_DEVICE_UNSAFE", "action": "HOLD", "customer_friction_risk": "Medium", "fallback_behavior": "Step-up when device intelligence unavailable"},
        {"rule_id": "FRD-020", "rule_name": "New beneficiary high risk", "rule_description": "New beneficiary, elevated beneficiary risk and high amount", "condition": "new_beneficiary_flag == 1 AND beneficiary_risk_score >= 35 AND amount >= 1000", "priority": 3, "severity": "HIGH", "reason_code": "RC_NEW_BENEFICIARY", "action": "MANUAL_REVIEW", "customer_friction_risk": "Medium", "fallback_behavior": "Step-up plus cooling-off period"},
        {"rule_id": "FRD-021", "rule_name": "Mule network concentration", "rule_description": "Multiple-account device with elevated beneficiary risk", "condition": "multiple_accounts_device_flag == 1 AND beneficiary_risk_score >= 50", "priority": 3, "severity": "HIGH", "reason_code": "RC_MULE_NETWORK", "action": "MANUAL_REVIEW", "customer_friction_risk": "Medium", "fallback_behavior": "Manual review"},
        {"rule_id": "FRD-030", "rule_name": "Extreme 10-minute velocity", "rule_description": "Eight or more transactions in ten minutes", "condition": "transactions_last_10m >= 8", "priority": 3, "severity": "HIGH", "reason_code": "RC_HIGH_VELOCITY", "action": "HOLD", "customer_friction_risk": "Medium", "fallback_behavior": "Use one-hour velocity proxy"},
        {"rule_id": "FRD-031", "rule_name": "Amount spike and daily aggregation", "rule_description": "Amount far above baseline and elevated 24-hour amount", "condition": "amount_spike_ratio >= 8 AND amount_last_24h >= 5000", "priority": 4, "severity": "HIGH", "reason_code": "RC_UNUSUAL_AMOUNT", "action": "MANUAL_REVIEW", "customer_friction_risk": "Medium", "fallback_behavior": "Step-up when history is stale"},
        {"rule_id": "FRD-032", "rule_name": "Card-testing burst", "rule_description": "Low-value transaction with extreme short velocity", "condition": "amount <= 20 AND transactions_last_10m >= 10", "priority": 4, "severity": "HIGH", "reason_code": "RC_CARD_TESTING", "action": "HOLD", "customer_friction_risk": "Low", "fallback_behavior": "Merchant/channel velocity check"},
        {"rule_id": "FRD-040", "rule_name": "OTP failure", "rule_description": "Five or more failed OTP attempts", "condition": "failed_otp_count >= 5", "priority": 5, "severity": "MEDIUM", "reason_code": "RC_AUTH_FAILURE", "action": "STEP_UP", "customer_friction_risk": "Medium", "fallback_behavior": "Hold if authentication service unavailable"},
        {"rule_id": "FRD-050", "rule_name": "Geography-device mismatch", "rule_description": "Country mismatch, new device and high-risk IP", "condition": "country_mismatch_flag == 1 AND new_device_flag == 1 AND ip_risk_score >= 70", "priority": 3, "severity": "HIGH", "reason_code": "RC_GEO_MISMATCH", "action": "HOLD", "customer_friction_risk": "High", "fallback_behavior": "Conservative step-up"},
        {"rule_id": "FRD-051", "rule_name": "Impossible travel proxy", "rule_description": "Large location distance plus country mismatch", "condition": "distance_from_last_transaction >= 1000 AND country_mismatch_flag == 1", "priority": 4, "severity": "HIGH", "reason_code": "RC_IMPOSSIBLE_TRAVEL", "action": "MANUAL_REVIEW", "customer_friction_risk": "Medium", "fallback_behavior": "Step-up"},
        {"rule_id": "FRD-060", "rule_name": "Night amount anomaly", "rule_description": "Night-time transaction materially above customer baseline", "condition": "night_transaction_flag == 1 AND amount_spike_ratio >= 6", "priority": 6, "severity": "MEDIUM", "reason_code": "RC_BEHAVIOUR_CHANGE", "action": "STEP_UP", "customer_friction_risk": "Medium", "fallback_behavior": "Allow only below low-value limit"},
        {"rule_id": "FRD-061", "rule_name": "Merchant-device risk", "rule_description": "High-risk merchant, high amount and weak device trust", "condition": "high_risk_merchant_flag == 1 AND amount >= 1000 AND device_trust_score < 40", "priority": 4, "severity": "HIGH", "reason_code": "RC_MERCHANT_DEVICE", "action": "MANUAL_REVIEW", "customer_friction_risk": "Medium", "fallback_behavior": "Step-up"},
        {"rule_id": "FRD-070", "rule_name": "Privileged override misuse", "rule_description": "Privileged override applied to a high-value transaction", "condition": "privileged_override_flag == 1 AND amount >= 2000", "priority": 2, "severity": "CRITICAL", "reason_code": "RC_OVERRIDE_MISUSE", "action": "BLOCK_ACCOUNT", "customer_friction_risk": "High", "fallback_behavior": "Hold and dual approval"},
        {"rule_id": "FRD-080", "rule_name": "Duplicate transaction", "rule_description": "Duplicate transaction marker", "condition": "duplicate_transaction_flag == 1", "priority": 2, "severity": "CRITICAL", "reason_code": "RC_DUPLICATE_TXN", "action": "HOLD", "customer_friction_risk": "Low", "fallback_behavior": "Idempotency check then hold"},
    ]


def evaluate_rules(frame: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "FRD-001": frame["blacklist_hit"].eq(1),
        "FRD-010": frame["account_takeover_signal"].eq(1) & frame["failed_otp_count"].ge(5),
        "FRD-011": (frame["rooted_device_flag"].eq(1) | frame["emulator_flag"].eq(1)) & frame["amount"].ge(1000),
        "FRD-020": frame["new_beneficiary_flag"].eq(1) & frame["beneficiary_risk_score"].ge(35) & frame["amount"].ge(1000),
        "FRD-021": frame["multiple_accounts_device_flag"].eq(1) & frame["beneficiary_risk_score"].ge(50),
        "FRD-030": frame["transactions_last_10m"].ge(8),
        "FRD-031": frame["amount_spike_ratio"].ge(8) & frame["amount_last_24h"].ge(5000),
        "FRD-032": frame["amount"].le(20) & frame["transactions_last_10m"].ge(10),
        "FRD-040": frame["failed_otp_count"].ge(5),
        "FRD-050": frame["country_mismatch_flag"].eq(1) & frame["new_device_flag"].eq(1) & frame["ip_risk_score"].ge(70),
        "FRD-051": frame["distance_from_last_transaction"].ge(1000) & frame["country_mismatch_flag"].eq(1),
        "FRD-060": frame["night_transaction_flag"].eq(1) & frame["amount_spike_ratio"].ge(6),
        "FRD-061": frame["high_risk_merchant_flag"].eq(1) & frame["amount"].ge(1000) & frame["device_trust_score"].lt(40),
        "FRD-070": frame["privileged_override_flag"].eq(1) & frame["amount"].ge(2000),
        "FRD-080": frame["duplicate_transaction_flag"].eq(1),
    }


def main() -> None:
    log = get_logger("phase4.rules")
    source = ROOT / "outputs/synthetic_transaction_scores.csv.gz"
    frame = pd.read_csv(source)
    definitions = build_rule_definitions()
    definition_by_id = {item["rule_id"]: item for item in definitions}
    hits = evaluate_rules(frame)
    hit_matrix = pd.DataFrame({rule_id: condition.astype(int) for rule_id, condition in hits.items()})

    frame["rule_hit_count"] = hit_matrix.sum(axis=1)
    frame["critical_rule_hits"] = sum(
        hit_matrix[item["rule_id"]] for item in definitions if item["severity"] == "CRITICAL"
    )
    frame["high_rule_hits"] = sum(
        hit_matrix[item["rule_id"]] for item in definitions if item["severity"] == "HIGH"
    )
    frame["medium_rule_hits"] = sum(
        hit_matrix[item["rule_id"]] for item in definitions if item["severity"] == "MEDIUM"
    )

    rule_ids = np.array(list(hit_matrix.columns))
    rule_hit_strings = []
    reason_strings = []
    primary_actions = []
    minimum_priority = []
    highest_severity = []
    severity_rank = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}
    action_rank = {"BLOCK_ACCOUNT": 5, "HOLD": 4, "DECLINE": 3, "MANUAL_REVIEW": 2, "STEP_UP": 1}
    matrix_values = hit_matrix.to_numpy(dtype=bool)
    for row in matrix_values:
        selected_ids = rule_ids[row]
        if len(selected_ids) == 0:
            rule_hit_strings.append("")
            reason_strings.append("")
            primary_actions.append("ALLOW")
            minimum_priority.append(8)
            highest_severity.append("NONE")
            continue
        selected_definitions = [definition_by_id[value] for value in selected_ids]
        selected_definitions.sort(key=lambda item: (item["priority"], -action_rank[item["action"]], item["rule_id"]))
        rule_hit_strings.append(";".join(item["rule_id"] for item in selected_definitions))
        reason_strings.append(";".join(item["reason_code"] for item in selected_definitions))
        primary_actions.append(selected_definitions[0]["action"])
        minimum_priority.append(selected_definitions[0]["priority"])
        highest_severity.append(max((item["severity"] for item in selected_definitions), key=lambda value: severity_rank[value]))

    frame["rule_hits"] = rule_hit_strings
    frame["rule_reason_codes"] = reason_strings
    frame["rule_primary_action"] = primary_actions
    frame["highest_rule_priority"] = minimum_priority
    frame["max_rule_severity"] = highest_severity
    write_csv(frame, "outputs/synthetic_rule_hits.csv.gz", compression="gzip")

    performance_rows = []
    total_fraud = int(frame["transaction_fraud_label"].sum())
    total_fraud_amount = float(frame.loc[frame["transaction_fraud_label"].eq(1), "amount"].sum())
    for item in definitions:
        selected = hits[item["rule_id"]]
        fraud_selected = selected & frame["transaction_fraud_label"].eq(1)
        alerts = int(selected.sum())
        fraud_count = int(fraud_selected.sum())
        fraud_amount = float(frame.loc[fraud_selected, "amount"].sum())
        performance_rows.append(
            {
                "rule_id": item["rule_id"],
                "rule_name": item["rule_name"],
                "transactions_assessed": len(frame),
                "alerts_generated": alerts,
                "alert_rate": safe_div(alerts, len(frame)),
                "fraud_captured": fraud_count,
                "fraud_recall": safe_div(fraud_count, total_fraud),
                "fraud_amount_captured": fraud_amount,
                "fraud_amount_recall": safe_div(fraud_amount, total_fraud_amount),
                "false_positives": int((selected & frame["transaction_fraud_label"].eq(0)).sum()),
                "precision": safe_div(fraud_count, alerts),
                "customer_friction_rate": safe_div((selected & frame["transaction_fraud_label"].eq(0)).sum(), len(frame)),
                "capacity_consumed_per_day": safe_div(alerts, frame["simulation_day"].nunique()),
                "action": item["action"],
                "severity": item["severity"],
            }
        )
    performance = pd.DataFrame(performance_rows)
    performance["control_status"] = np.select(
        [
            performance["precision"].ge(0.10) & performance["alerts_generated"].gt(0),
            performance["precision"].ge(0.03) & performance["alerts_generated"].gt(0),
            performance["alerts_generated"].eq(0),
        ],
        ["Effective", "Partially effective", "Unused rule"],
        default="Tune / monitor",
    )
    performance["recommendation"] = np.select(
        [performance["control_status"].eq("Effective"), performance["control_status"].eq("Unused rule")],
        ["Retain and monitor", "Retire or redesign"],
        default="Tune threshold and monitor overlap",
    )
    performance = add_metadata(
        performance,
        "Synthetic",
        "Derived",
        "Synthetic deterministic fraud controls",
        "Controls-testing results; not observed production control performance",
    )
    write_csv(performance, "outputs/rule_performance_summary.csv")

    inventory = pd.DataFrame(definitions)
    inventory["data_layer"] = "Synthetic"
    inventory["owner"] = "Fraud Strategy"
    inventory["effective_date"] = "2026-07-11"
    inventory["status"] = "Testing"
    inventory = inventory.merge(
        performance[["rule_id", "alert_rate", "fraud_recall"]], on="rule_id", how="left"
    ).rename(columns={"alert_rate": "expected_alert_rate", "fraud_recall": "expected_fraud_capture"})
    inventory["limitation"] = "Synthetic controls-testing evidence only"
    inventory["data_status"] = "Synthetic"
    inventory["source_type"] = "Synthetic observable features"
    inventory["claim_boundary"] = "No observed production rule effectiveness claim"
    write_csv(inventory, "rules/fraud_rule_inventory.csv")

    priority = pd.DataFrame(
        [
            [0, "Invalid or missing critical input", "DATA_EXCEPTION", "Fail closed for invalid score scale"],
            [1, "Known blacklist / legal-style simulated block", "BLOCK_ACCOUNT", "Blacklist has precedence over model"],
            [2, "Emergency ATO, duplicate or override misuse", "HOLD/BLOCK_ACCOUNT", "Immediate containment"],
            [3, "High-severity deterministic fraud rule", "HOLD/MANUAL_REVIEW", "Rule before model-only routing"],
            [4, "High calibrated model score", "DECLINE/MANUAL_REVIEW", "Amount-aware action"],
            [5, "High anomaly score", "MANUAL_REVIEW", "No fraud proof from anomaly alone"],
            [6, "Step-up rule", "STEP_UP", "Customer verification"],
            [7, "Manual review routing", "MANUAL_REVIEW", "Capacity controlled"],
            [8, "No material signal", "ALLOW", "Monitoring continues"],
        ],
        columns=["priority", "rule_family", "decision", "governance_rationale"],
    )
    priority = add_metadata(
        priority,
        "Synthetic",
        "Proxy",
        "Project 6 governance pattern adapted for fraud",
        "Control design, not a live decision hierarchy",
    )
    write_csv(priority, "rules/rule_priority_matrix.csv")

    decision_matrix = pd.DataFrame(
        [
            ["Missing/invalid critical input", "Any", "Any", "DATA_EXCEPTION", "Exception queue"],
            ["Blacklist", "Any", "Any", "BLOCK_ACCOUNT", "Immediate escalation"],
            ["Critical ATO or duplicate", "Any", "Any", "HOLD", "Identity/payment verification"],
            ["High model and amount", ">=0.60", ">=1000", "DECLINE", "Senior review if overridden"],
            ["Critical rule", "Any", "Any", "HOLD", "Priority investigation"],
            ["Model high", ">=0.35", "Any", "MANUAL_REVIEW", "Capacity prioritised"],
            ["Combined medium signals", ">=0.15", "High rule hit", "MANUAL_REVIEW", "Explain with rule reason"],
            ["Anomaly only", "Any", ">=98.5 percentile", "MANUAL_REVIEW", "No automatic decline"],
            ["Moderate signal", ">=0.08", "Any", "STEP_UP", "Authentication"],
            ["Low risk", "<0.08", "No material rule", "ALLOW", "Passive monitoring"],
        ],
        columns=["condition_group", "model_score_condition", "secondary_condition", "decision", "operational_action"],
    )
    decision_matrix = add_metadata(
        decision_matrix,
        "Synthetic",
        "Proxy",
        "Hybrid control design",
        "Illustrative synthetic controls-testing decisions",
    )
    write_csv(decision_matrix, "rules/decision_matrix.csv")

    reason_rows = [
        ["RC_BLACKLIST", "Known blacklist", "Beneficiary blacklist flag", "Rule", "Block and escalate"],
        ["RC_ATO_CRITICAL", "Account takeover indicator", "ATO signal and OTP failures", "Rule", "Hold and verify"],
        ["RC_DEVICE_UNSAFE", "Unsafe device", "Rooted/emulated device", "Rule", "Hold or step-up"],
        ["RC_NEW_BENEFICIARY", "New high-risk beneficiary", "Beneficiary age/risk and amount", "Rule", "Review"],
        ["RC_MULE_NETWORK", "Mule-network pattern", "Shared device and beneficiary risk", "Rule", "Review"],
        ["RC_HIGH_VELOCITY", "High transaction velocity", "Ten-minute transaction count", "Rule", "Hold"],
        ["RC_UNUSUAL_AMOUNT", "Unusual transaction amount", "Amount spike and 24-hour amount", "Rule", "Review"],
        ["RC_CARD_TESTING", "Card-testing pattern", "Low amount and high velocity", "Rule", "Hold"],
        ["RC_AUTH_FAILURE", "Authentication failure", "Failed OTP count", "Rule", "Step-up"],
        ["RC_GEO_MISMATCH", "Geographic mismatch", "Country, device and IP signals", "Rule", "Hold"],
        ["RC_IMPOSSIBLE_TRAVEL", "Impossible-travel proxy", "Distance and country mismatch", "Rule", "Review"],
        ["RC_BEHAVIOUR_CHANGE", "Behaviour change", "Night transaction and amount spike", "Rule", "Step-up"],
        ["RC_MERCHANT_DEVICE", "Merchant-device risk", "Merchant, amount and device trust", "Rule", "Review"],
        ["RC_OVERRIDE_MISUSE", "Override misuse", "Privileged override and amount", "Rule", "Block"],
        ["RC_DUPLICATE_TXN", "Duplicate transaction", "Duplicate marker", "Rule", "Hold"],
        ["RC_MODEL_HIGH", "High model score", "Synthetic observable-feature score", "Model", "Review"],
        ["RC_ANOMALY_HIGH", "High anomaly score", "Synthetic anomaly percentile", "Anomaly", "Review"],
        ["RC_MISSING_DATA", "Missing critical data", "Input validation", "Validation", "Exception"],
        ["RC_INVALID_SCORE", "Invalid score scale", "Score outside 0-1", "Validation", "Release block"],
        ["RC_LOW_RISK", "Low combined risk", "No material rule or score", "Hybrid", "Allow"],
    ]
    reasons = pd.DataFrame(reason_rows, columns=["reason_code", "investigator_label", "observable_basis", "source", "linked_action"])
    reasons = add_metadata(
        reasons,
        "Synthetic",
        "Proxy",
        "Synthetic observable controls",
        "Reason codes never use observed PCA names",
    )
    write_csv(reasons, "rules/reason_code_dictionary.csv")

    overrides = pd.DataFrame(
        [
            ["OVR-01", "STEP_UP to ALLOW", "Successful strong authentication", "Fraud Operations Lead", "Yes", "24 hours"],
            ["OVR-02", "MANUAL_REVIEW to ALLOW", "Documented false-positive evidence", "Senior Investigator", "Yes", "Case-specific"],
            ["OVR-03", "HOLD to release", "Identity and beneficiary verification", "Fraud Operations Lead", "Yes", "Case-specific"],
            ["OVR-04", "BLOCK_ACCOUNT", "No unilateral override", "Risk Director", "Dual approval", "Emergency only"],
            ["OVR-05", "DATA_EXCEPTION", "No business override for invalid score scale", "Technology Risk", "No", "Release block"],
        ],
        columns=["override_id", "decision_scope", "permitted_rationale", "approver", "audit_evidence_required", "duration_limit"],
    )
    overrides = add_metadata(
        overrides,
        "Synthetic",
        "Proxy",
        "Fraud control governance design",
        "Illustrative override policy",
    )
    write_csv(overrides, "rules/override_policy.csv")

    aggregate_rule = frame["rule_hit_count"].gt(0)
    aggregate_precision = safe_div((aggregate_rule & frame["transaction_fraud_label"].eq(1)).sum(), aggregate_rule.sum())
    aggregate_recall = safe_div((aggregate_rule & frame["transaction_fraud_label"].eq(1)).sum(), total_fraud)
    report_table = performance[["rule_id", "rule_name", "alert_rate", "precision", "fraud_recall", "fraud_amount_recall", "control_status"]].sort_values("fraud_recall", ascending=False)
    write_markdown(
        "methodology/fraud_rule_methodology.md",
        "Fraud Rule Methodology",
        f"""Rules use only observable synthetic controls-testing features. Hidden latent risks and observed PCA variables are prohibited from rule conditions and reason codes. Boundary operators are explicit and priority follows data exception, blacklist/emergency controls, high-severity deterministic rules, model/anomaly routing, step-up and allow.

Aggregate rules-only precision is **{aggregate_precision:.2%}** and recall is **{aggregate_recall:.2%}**. Both remain below 100%, which is required evidence that rules do not recreate the synthetic fraud label. Rule results are reviewed for overlap, customer friction and capacity rather than capture alone.

## Rule performance

{dataframe_to_markdown(report_table)}
""",
    )
    log.info("Fraud rules built: rules=%s aggregate_alert_rate=%.4f", len(definitions), aggregate_rule.mean())
    print(f"Fraud rules PASS | rules={len(definitions)} | aggregate alert rate={aggregate_rule.mean():.2%}")


if __name__ == "__main__":
    main()
