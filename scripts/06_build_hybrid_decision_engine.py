from __future__ import annotations

import numpy as np
import pandas as pd

from _project5_common import (
    ROOT,
    add_metadata,
    dataframe_to_markdown,
    get_logger,
    safe_div,
    threshold_for_alert_rate,
    write_csv,
    write_markdown,
)


def component_metrics(frame: pd.DataFrame, alert: pd.Series, component: str) -> dict:
    fraud = frame["transaction_fraud_label"].eq(1)
    fraud_alert = alert & fraud
    alerts = int(alert.sum())
    captured = int(fraud_alert.sum())
    captured_amount = float(frame.loc[fraud_alert, "amount"].sum())
    total_fraud_amount = float(frame.loc[fraud, "amount"].sum())
    false_positive = int((alert & ~fraud).sum())
    prevented_loss = captured_amount * 0.70
    investigation_cost = alerts * 5.0
    friction_cost = false_positive * 2.0
    return {
        "component_set": component,
        "transactions": len(frame),
        "alerts": alerts,
        "alert_rate": safe_div(alerts, len(frame)),
        "fraud_captured": captured,
        "fraud_recall": safe_div(captured, fraud.sum()),
        "fraud_amount_captured": captured_amount,
        "fraud_amount_recall": safe_div(captured_amount, total_fraud_amount),
        "false_positives": false_positive,
        "precision": safe_div(captured, alerts),
        "prevented_loss_proxy": prevented_loss,
        "investigation_cost": investigation_cost,
        "customer_friction_cost": friction_cost,
        "net_benefit_proxy": prevented_loss - investigation_cost - friction_cost,
    }


def main() -> None:
    log = get_logger("phase4.hybrid")
    frame = pd.read_csv(ROOT / "outputs/synthetic_rule_hits.csv.gz")
    score = frame["synthetic_model_score"].to_numpy(dtype=float)
    anomaly = frame["synthetic_anomaly_score"].to_numpy(dtype=float)
    amount = frame["amount"].to_numpy(dtype=float)
    validation = frame["synthetic_split"].eq("validation")
    test = frame["synthetic_split"].eq("test")
    model_step_up_threshold = threshold_for_alert_rate(frame.loc[validation, "synthetic_model_score"], 0.05)
    model_review_threshold = threshold_for_alert_rate(frame.loc[validation, "synthetic_model_score"], 0.01)
    model_decline_threshold = threshold_for_alert_rate(frame.loc[validation, "synthetic_model_score"], 0.001)
    anomaly_review_threshold = threshold_for_alert_rate(frame.loc[validation, "synthetic_anomaly_score"], 0.005)
    quality_rule_ids = {"FRD-010", "FRD-030", "FRD-032", "FRD-040", "FRD-050", "FRD-051", "FRD-061"}
    quality_rule_overlay = frame["rule_hits"].fillna("").map(
        lambda value: any(rule_id in quality_rule_ids for rule_id in value.split(";") if rule_id)
    )

    decision = np.full(len(frame), "ALLOW", dtype=object)
    reason = np.full(len(frame), "RC_LOW_RISK", dtype=object)

    def assign(mask: np.ndarray | pd.Series, value: str, reason_code: str) -> None:
        decision[np.asarray(mask)] = value
        reason[np.asarray(mask)] = reason_code

    assign((frame["high_rule_hits"].ge(1) | (score >= model_step_up_threshold)), "STEP_UP", "RC_STEP_UP_RISK")
    assign((anomaly >= anomaly_review_threshold), "MANUAL_REVIEW", "RC_ANOMALY_HIGH")
    assign(
        ((quality_rule_overlay & (score >= 0.05)) | (frame["high_rule_hits"].ge(2) & (score >= model_step_up_threshold))),
        "MANUAL_REVIEW",
        "RC_COMBINED_RISK",
    )
    assign((score >= model_review_threshold), "MANUAL_REVIEW", "RC_MODEL_HIGH")
    assign((score >= model_decline_threshold) & (amount >= 1000), "DECLINE", "RC_MODEL_HIGH_AMOUNT")
    assign(frame["critical_rule_hits"].ge(1), "HOLD", "RC_CRITICAL_RULE")
    assign(frame["account_takeover_signal"].eq(1) & frame["failed_otp_count"].ge(5), "HOLD", "RC_ATO_CRITICAL")
    assign(frame["duplicate_transaction_flag"].eq(1), "HOLD", "RC_DUPLICATE_TXN")
    assign(frame["privileged_override_flag"].eq(1) & frame["amount"].ge(2000), "BLOCK_ACCOUNT", "RC_OVERRIDE_MISUSE")
    assign(frame["blacklist_hit"].eq(1), "BLOCK_ACCOUNT", "RC_BLACKLIST")

    invalid_score = frame["synthetic_model_score"].isna() | ~frame["synthetic_model_score"].between(0, 1)
    invalid_amount = frame["amount"].isna() | frame["amount"].lt(0)
    missing_identity = frame[["transaction_id", "customer_id", "transaction_time"]].isna().any(axis=1)
    assign(invalid_score | invalid_amount | missing_identity, "DATA_EXCEPTION", "RC_MISSING_DATA")

    output = frame.copy()
    output["decision"] = decision
    output["primary_reason_code"] = reason
    model_reason = np.where(score >= model_review_threshold, "RC_MODEL_HIGH", "")
    anomaly_reason = np.where(anomaly >= anomaly_review_threshold, "RC_ANOMALY_HIGH", "")
    all_reasons = []
    for primary, rule_reasons, model_code, anomaly_code in zip(
        reason, output["rule_reason_codes"].fillna(""), model_reason, anomaly_reason
    ):
        codes = [primary]
        codes.extend([value for value in str(rule_reasons).split(";") if value])
        if model_code:
            codes.append(model_code)
        if anomaly_code:
            codes.append(anomaly_code)
        all_reasons.append(";".join(dict.fromkeys(codes)))
    output["all_reason_codes"] = all_reasons
    output["expected_prevented_loss_proxy"] = (output["synthetic_model_score"] * output["amount"] * 0.70).round(4)
    output["customer_friction_risk"] = output["decision"].map(
        {
            "ALLOW": "Low",
            "STEP_UP": "Low-Medium",
            "MANUAL_REVIEW": "Medium",
            "HOLD": "High",
            "DECLINE": "High",
            "BLOCK_ACCOUNT": "Very High",
            "DATA_EXCEPTION": "Medium",
        }
    )
    output["review_priority"] = np.select(
        [
            output["decision"].isin(["BLOCK_ACCOUNT", "DECLINE"]),
            output["decision"].eq("HOLD"),
            output["decision"].eq("MANUAL_REVIEW") & output["amount"].ge(1000),
            output["decision"].isin(["MANUAL_REVIEW", "DATA_EXCEPTION"]),
            output["decision"].eq("STEP_UP"),
        ],
        ["CRITICAL", "HIGH", "HIGH", "MEDIUM", "LOW"],
        default="NONE",
    )
    output["sla_hours"] = output["review_priority"].map(
        {"CRITICAL": 1, "HIGH": 4, "MEDIUM": 24, "LOW": 48, "NONE": 0}
    )
    output["override_eligibility"] = np.select(
        [output["decision"].eq("BLOCK_ACCOUNT"), output["decision"].eq("DATA_EXCEPTION")],
        ["Dual approval only", "No business override"],
        default="Documented case override permitted",
    )
    output["decision_engine_version"] = "P5-HYBRID-1.0"
    output["model_step_up_threshold"] = model_step_up_threshold
    output["model_review_threshold"] = model_review_threshold
    output["model_decline_threshold"] = model_decline_threshold
    output["anomaly_review_threshold"] = anomaly_review_threshold
    output["data_layer"] = "Synthetic"
    output["data_status"] = "Derived"
    output["source_type"] = "Synthetic model, anomaly and deterministic rules"
    output["claim_boundary"] = "Controls-testing decisions only; no live payment action"
    write_csv(output, "outputs/hybrid_decision_output.csv.gz", compression="gzip")

    threshold_register = pd.DataFrame(
        [
            ["synthetic_model_step_up", "Model", "Top 5% validation risk", model_step_up_threshold, "STEP_UP", "Synthetic controls testing"],
            ["synthetic_model_review", "Model", "Top 1% validation risk", model_review_threshold, "MANUAL_REVIEW", "Synthetic controls testing"],
            ["synthetic_model_decline", "Model + amount", "Top 0.1% validation risk and amount >= 1000", model_decline_threshold, "DECLINE", "Synthetic controls testing"],
            ["synthetic_anomaly_review", "Anomaly", "Top 0.5% validation anomaly", anomaly_review_threshold, "MANUAL_REVIEW", "Synthetic controls testing"],
        ],
        columns=["threshold_id", "component", "validation_selection_rule", "locked_threshold", "linked_action", "status"],
    )
    threshold_register = add_metadata(
        threshold_register,
        "Synthetic",
        "Derived",
        "Validation-only synthetic threshold design",
        "Controls-testing thresholds; no live payment claim",
    )
    write_csv(threshold_register, "models/synthetic_hybrid_thresholds.csv")

    decision_matrix = pd.DataFrame(
        [
            ["Missing/invalid critical input", "Any", "Any", "DATA_EXCEPTION", "Exception queue"],
            ["Blacklist or override misuse", "Any", "Any", "BLOCK_ACCOUNT", "Immediate escalation"],
            ["Critical ATO or duplicate", "Any", "Any", "HOLD", "Identity/payment verification"],
            ["Extreme model risk and material amount", f">={model_decline_threshold:.6f}", "amount >= 1000", "DECLINE", "Validation top 0.1%; senior override only"],
            ["Model review band", f">={model_review_threshold:.6f}", "Any", "MANUAL_REVIEW", "Validation top 1%"],
            ["Anomaly review band", "Any", f">={anomaly_review_threshold:.6f}", "MANUAL_REVIEW", "Validation top 0.5%; no automatic decline"],
            ["Quality rule plus model support", ">=0.050000", "Governed quality rule", "MANUAL_REVIEW", "Reduce low-yield rule workload"],
            ["Moderate model/rule signal", f">={model_step_up_threshold:.6f}", "or high rule", "STEP_UP", "Validation top 5%"],
            ["Low combined risk", f"<{model_step_up_threshold:.6f}", "No material rule", "ALLOW", "Passive monitoring"],
        ],
        columns=["condition_group", "model_score_condition", "secondary_condition", "decision", "operational_action"],
    )
    decision_matrix = add_metadata(
        decision_matrix,
        "Synthetic",
        "Derived",
        "Validation-locked hybrid control design",
        "Illustrative controls-testing decisions",
    )
    write_csv(decision_matrix, "rules/decision_matrix.csv")

    test_frame = output.loc[test].copy()
    model_threshold = model_review_threshold
    anomaly_threshold = anomaly_review_threshold
    model_alert = test_frame["synthetic_model_score"].ge(model_threshold)
    rules_alert = test_frame["rule_hit_count"].gt(0)
    anomaly_alert = test_frame["synthetic_anomaly_score"].ge(anomaly_threshold)
    hybrid_action = test_frame["decision"].isin(["HOLD", "MANUAL_REVIEW", "DECLINE", "BLOCK_ACCOUNT", "DATA_EXCEPTION"])
    combinations = {
        "Model only": model_alert,
        "Rules only": rules_alert,
        "Anomaly only": anomaly_alert,
        "Model + rules": model_alert | rules_alert,
        "Model + rules + anomaly": model_alert | rules_alert | anomaly_alert,
        "Final hybrid actionable": hybrid_action,
    }
    rows = [component_metrics(test_frame, alert, name) for name, alert in combinations.items()]
    incremental = pd.DataFrame(rows)
    base_model_fraud = model_alert & test_frame["transaction_fraud_label"].eq(1)
    base_rules_fraud = rules_alert & test_frame["transaction_fraud_label"].eq(1)
    anomaly_fraud = anomaly_alert & test_frame["transaction_fraud_label"].eq(1)
    incremental["unique_fraud_contribution"] = 0
    incremental.loc[incremental["component_set"].eq("Model only"), "unique_fraud_contribution"] = int((base_model_fraud & ~rules_alert & ~anomaly_alert).sum())
    incremental.loc[incremental["component_set"].eq("Rules only"), "unique_fraud_contribution"] = int((base_rules_fraud & ~model_alert & ~anomaly_alert).sum())
    incremental.loc[incremental["component_set"].eq("Anomaly only"), "unique_fraud_contribution"] = int((anomaly_fraud & ~model_alert & ~rules_alert).sum())
    incremental["model_threshold_locked_on_validation"] = model_threshold
    incremental["anomaly_threshold_locked_on_validation"] = anomaly_threshold
    incremental = add_metadata(
        incremental,
        "Synthetic",
        "Derived",
        "Synthetic test population; validation-derived component thresholds",
        "Incremental controls-testing evidence only",
    )
    write_csv(incremental, "outputs/hybrid_incremental_value.csv")

    decision_summary = (
        output.groupby("decision", as_index=False)
        .agg(
            transactions=("transaction_id", "size"),
            fraud_transactions=("transaction_fraud_label", "sum"),
            transaction_amount=("amount", "sum"),
            fraud_amount=("amount", lambda values: values[output.loc[values.index, "transaction_fraud_label"].eq(1)].sum()),
            expected_prevented_loss_proxy=("expected_prevented_loss_proxy", "sum"),
        )
    )
    decision_summary["population_share"] = decision_summary["transactions"] / len(output)
    decision_summary["fraud_rate"] = decision_summary["fraud_transactions"] / decision_summary["transactions"]
    decision_summary = add_metadata(
        decision_summary,
        "Synthetic",
        "Derived",
        "Synthetic hybrid decision engine",
        "Illustrative action routing only",
    )
    write_csv(decision_summary, "outputs/hybrid_decision_summary.csv")

    write_markdown(
        "methodology/hybrid_decision_engine_methodology.md",
        "Hybrid Fraud Decision Engine Methodology",
        f"""The engine combines calibrated synthetic model probability, anomaly percentile and observable deterministic controls. It returns `ALLOW`, `STEP_UP`, `HOLD`, `MANUAL_REVIEW`, `DECLINE`, `BLOCK_ACCOUNT` or `DATA_EXCEPTION` with traceable reason codes.

Priority is explicit: invalid inputs, blacklist/override controls, duplicate and account-takeover emergency controls, amount-aware high model risk, high-severity rules, combined signals, anomaly review, step-up and allow. Anomaly-only signals never create an automatic decline.

Validation-derived component thresholds used for incremental-value analysis are **{model_threshold:.4f}** for the model and **{anomaly_threshold:.4f}** for anomaly percentile. The final hybrid routing uses the governed fixed boundaries in `rules/decision_matrix.csv`.

## Incremental value on synthetic test data

{dataframe_to_markdown(incremental[["component_set", "alert_rate", "precision", "fraud_recall", "fraud_amount_recall", "net_benefit_proxy", "unique_fraud_contribution"]])}

Expected prevented loss is a prospective synthetic proxy (`score x amount x 70%`), while realised capture metrics use synthetic labels and amounts. These two views are not interchangeable.
""",
    )
    log.info("Hybrid engine completed: actionable_rate=%.4f", hybrid_action.mean())
    print(f"Hybrid engine PASS | actionable test rate={hybrid_action.mean():.2%}")


if __name__ == "__main__":
    main()
