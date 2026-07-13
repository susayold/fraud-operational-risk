from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from _project5_common import (
    ROOT,
    SEED,
    add_metadata,
    dataframe_to_markdown,
    get_logger,
    safe_div,
    write_csv,
    write_markdown,
)


def appetite_status(value: float, green_test: bool, amber_test: bool) -> str:
    if green_test:
        return "GREEN"
    if amber_test:
        return "AMBER"
    return "RED"


def main() -> None:
    log = get_logger("phase6.operational_risk")
    rng = np.random.default_rng(SEED + 3)
    decisions = pd.read_csv(ROOT / "outputs/hybrid_decision_output.csv.gz")
    alerts = pd.read_csv(ROOT / "outputs/alert_queue.csv.gz")
    rule_performance = pd.read_csv(ROOT / "outputs/rule_performance_summary.csv")
    observed_kpis = pd.read_csv(ROOT / "outputs/observed_fraud_kpi_summary.csv")
    threshold = pd.read_csv(ROOT / "outputs/threshold_economics.csv")
    selected_test = threshold.loc[
        threshold["population"].eq("test") & threshold["recommended_threshold_flag"].eq(1)
    ].iloc[0]

    rule_performance_core = rule_performance.copy()
    rule_performance_core["net_benefit"] = (
        rule_performance_core["fraud_amount_captured"] * 0.70
        - rule_performance_core["alerts_generated"] * 5.0
        - rule_performance_core["false_positives"] * 2.0
    )
    rule_performance_core["control_failures"] = np.where(
        rule_performance_core["control_status"].isin(["Unused rule", "Tune / monitor"]), 1, 0
    )
    rule_performance_core["residual_risk"] = np.select(
        [
            rule_performance_core["control_status"].eq("Effective"),
            rule_performance_core["control_status"].eq("Partially effective"),
        ],
        ["Low-Medium", "Medium"],
        default="High",
    )
    controls = rule_performance_core[
        [
            "rule_id",
            "rule_name",
            "transactions_assessed",
            "alerts_generated",
            "fraud_captured",
            "fraud_amount_captured",
            "false_positives",
            "precision",
            "fraud_recall",
            "net_benefit",
            "customer_friction_rate",
            "capacity_consumed_per_day",
            "control_failures",
            "residual_risk",
            "control_status",
            "recommendation",
        ]
    ].copy()
    controls = add_metadata(
        controls,
        "Synthetic",
        "Derived",
        "Synthetic rule outcomes",
        "Controls-testing effectiveness only",
    )
    write_csv(controls, "outputs/control_effectiveness_summary.csv")

    failure_library = pd.DataFrame(
        [
            ["CF-01", "Model score scale mismatch", "Model/Data", "Score arrives 0-100 instead of 0-1", "Release-block validation", "Technology Risk", "High"],
            ["CF-02", "Velocity feature stale", "Data", "Streaming aggregation stops refreshing", "Freshness KRI and rules-only fallback", "Fraud Platform", "High"],
            ["CF-03", "New-device rule spike", "Rule configuration", "Vendor or rule change creates alert surge", "Volume guardrail and rollback", "Fraud Strategy", "Medium"],
            ["CF-04", "Payroll false-positive block", "Customer treatment", "Legitimate recurring payments trigger control", "Segment exclusion with monitoring", "Fraud Strategy", "High"],
            ["CF-05", "Device vendor outage", "Vendor", "External device intelligence unavailable", "Conservative step-up fallback", "Vendor Management", "High"],
            ["CF-06", "Duplicate alert creation", "System", "Idempotency failure produces repeated alerts", "Transaction-ID de-duplication", "Payments Technology", "Medium"],
            ["CF-07", "Investigation backlog", "Capacity", "Incoming alerts exceed staffed capacity", "Priority queue and surge staffing", "Fraud Operations", "High"],
            ["CF-08", "Override misuse", "Governance", "High-risk block bypassed without dual approval", "Override audit and access removal", "Operational Risk", "Critical"],
            ["CF-09", "Missing reason code", "Process", "Decision cannot be explained to investigator", "Release validation", "Model Governance", "Medium"],
            ["CF-10", "Alert queue outage", "System", "Cases cannot enter investigator queue", "Hold critical / allow low-risk fallback", "Fraud Platform", "Critical"],
        ],
        columns=["failure_id", "control_failure", "root_cause_category", "failure_mode", "preventive_control", "owner", "inherent_severity"],
    )
    failure_library = add_metadata(
        failure_library,
        "Synthetic",
        "Proxy",
        "Operational control failure library",
        "Educational scenario design",
    )
    write_csv(failure_library, "operational_risk/control_failure_library.csv")

    incident_templates = [
        ("Model score delivered as 0-100", "Model/control failure", "Data", "Model scoring API", "SCORE_SCALE_MISMATCH", 42000, 8000, 125, "Critical"),
        ("Velocity feature stopped refreshing", "Data failure", "Data", "Velocity service", "VELOCITY_STALE", 18500, 2500, 48, "High"),
        ("New-device rule alert spike", "Process failure", "Rule configuration", "Decision engine", "RULE_ALERT_SPIKE", 9200, 0, 310, "High"),
        ("Legitimate payroll transactions blocked", "Customer-treatment failure", "Rule configuration", "Payments rules", "PAYROLL_FALSE_BLOCK", 15500, 7200, 640, "High"),
        ("Device intelligence vendor outage", "Third-party failure", "Vendor", "Device vendor", "DEVICE_VENDOR_OUTAGE", 26500, 4000, 820, "High"),
        ("Duplicate transactions generated duplicate alerts", "System failure", "System", "Alert gateway", "DUPLICATE_ALERTS", 7600, 2500, 390, "Medium"),
        ("Investigator backlog delayed fraud action", "Process failure", "Capacity", "Case management", "BACKLOG_DELAY", 33800, 5000, 190, "High"),
        ("Override misuse bypassed high-risk block", "Internal fraud", "Governance", "Decision override", "OVERRIDE_MISUSE", 68000, 12000, 37, "Critical"),
        ("OTP service outage", "Third-party failure", "Vendor", "Authentication", "OTP_OUTAGE", 21000, 3500, 1400, "High"),
        ("Alert queue unavailable", "System failure", "System", "Case management", "QUEUE_OUTAGE", 47000, 6000, 480, "Critical"),
        ("Reason-code mapping failed", "Process failure", "Model", "Decision engine", "REASON_CODE_FAILURE", 3800, 0, 85, "Medium"),
        ("Data latency breached scoring SLA", "Data failure", "Data", "Feature pipeline", "DATA_LATENCY", 12800, 1800, 260, "High"),
        ("Beneficiary blacklist feed delayed", "Third-party failure", "Vendor", "Blacklist service", "BLACKLIST_DELAY", 29500, 4000, 72, "High"),
        ("Monitoring report missed threshold breach", "Governance", "Governance", "KRI reporting", "MONITORING_MISS", 6400, 0, 0, "Medium"),
        ("Recovery file reconciliation failed", "Process failure", "Process", "Recovery operations", "RECOVERY_RECON", 11200, 5200, 18, "Medium"),
        ("Model artifact unavailable during deployment", "Model/control failure", "System", "Model registry", "MODEL_UNAVAILABLE", 17400, 2700, 95, "High"),
        ("Rule priority conflict", "Model/control failure", "Rule configuration", "Decision engine", "RULE_PRIORITY_CONFLICT", 8900, 1300, 44, "Medium"),
        ("Excessive cross-border step-up", "Customer-treatment failure", "Rule configuration", "Decision engine", "SEGMENT_FRICTION", 5600, 800, 920, "Medium"),
    ]
    incident_rows = []
    start = date(2026, 1, 2)
    for index, template in enumerate(incident_templates, start=1):
        title, incident_type, root_cause, system, control_failure, gross, recovery, customers, severity = template
        incident_date = start + timedelta(days=(index * 5) % 85)
        status = "Closed" if index % 3 else "Open remediation"
        incident_rows.append(
            {
                "incident_id": f"INC-{index:04d}",
                "incident_date": incident_date.isoformat(),
                "incident_title": title,
                "incident_type": incident_type,
                "business_line": "Digital Payments",
                "process": "Fraud detection and response",
                "system": system,
                "fraud_type": "Multiple / control event",
                "root_cause_category": root_cause,
                "gross_loss": gross,
                "recovery": recovery,
                "net_loss": gross - recovery,
                "customer_count": customers,
                "regulatory_impact_flag": int(severity == "Critical"),
                "control_failure": control_failure,
                "detection_source": "KRI/incident simulation",
                "severity": severity,
                "owner": "Operational Risk" if severity == "Critical" else "Fraud Operations",
                "action_due_date": (incident_date + timedelta(days=30 if severity == "Critical" else 60)).isoformat(),
                "status": status,
                "residual_risk": "High" if status != "Closed" and severity in ("Critical", "High") else "Medium",
                "lessons_learned": "Strengthen preventive validation, fallback and evidence retention",
            }
        )
    incidents = add_metadata(
        pd.DataFrame(incident_rows),
        "Synthetic",
        "Synthetic",
        "Operational incident scenario generator",
        "Simulated incident and loss data; not observed bank events",
    )
    write_csv(incidents, "operational_risk/incident_register.csv")
    write_csv(incidents, "data/synthetic/synthetic_incidents.csv")

    loss_summary = (
        incidents.groupby(["incident_type", "root_cause_category"], as_index=False)
        .agg(
            incident_count=("incident_id", "size"),
            gross_loss=("gross_loss", "sum"),
            recovery=("recovery", "sum"),
            net_loss=("net_loss", "sum"),
            customer_count=("customer_count", "sum"),
            open_actions=("status", lambda values: values.ne("Closed").sum()),
        )
    )
    loss_summary["recovery_rate"] = loss_summary["recovery"] / loss_summary["gross_loss"]
    loss_summary = add_metadata(
        loss_summary,
        "Synthetic",
        "Derived",
        "Synthetic incident register",
        "Operational loss scenario summary only",
    )
    write_csv(loss_summary, "operational_risk/loss_event_summary.csv")

    scenario_templates = [
        ("Fraud-model outage", "Occasional", 90000, 0.18, 0.65, "Rules-only mode"),
        ("Device-intelligence vendor outage", "Likely", 65000, 0.10, 0.55, "Conservative step-up"),
        ("OTP-service outage", "Occasional", 80000, 0.12, 0.60, "Hold high risk / alternate authentication"),
        ("Rule deployment error", "Occasional", 120000, 0.08, 0.45, "Rollback ruleset"),
        ("Alert-volume spike", "Likely", 70000, 0.07, 0.50, "Priority protection and surge capacity"),
        ("Score-scale mismatch", "Rare", 180000, 0.05, 0.35, "Release block"),
        ("Duplicate payment processing", "Occasional", 95000, 0.30, 0.55, "Idempotency and reversal"),
        ("Data-latency incident", "Likely", 55000, 0.10, 0.60, "Stale-data flag and fallback"),
        ("Insider override abuse", "Rare", 250000, 0.15, 0.30, "Dual approval and access suspension"),
        ("Third-party compromise", "Rare", 400000, 0.20, 0.25, "Vendor isolation and emergency controls"),
    ]
    scenario_rows = []
    for index, (name, frequency, gross, recovery_rate, effectiveness, action) in enumerate(scenario_templates, start=1):
        recovery = gross * recovery_rate
        net = gross - recovery
        residual = "Critical" if net >= 250000 else "High" if net >= 100000 else "Medium"
        scenario_rows.append(
            {
                "scenario_id": f"SCN-{index:02d}",
                "scenario": name,
                "frequency": frequency,
                "severity": "Severe" if gross >= 180000 else "Material",
                "gross_loss_estimate": gross,
                "recovery_estimate": recovery,
                "net_loss_estimate": net,
                "customer_impact": int(gross / 100),
                "control_effectiveness": effectiveness,
                "residual_risk": residual,
                "management_action": action,
                "escalation_threshold": "Immediate Risk Committee" if residual in ("Critical", "High") else "Monthly monitoring",
            }
        )
    scenarios = add_metadata(
        pd.DataFrame(scenario_rows),
        "Synthetic",
        "Proxy",
        "Operational-risk scenario assumptions",
        "Educational scenario estimates, not regulatory capital outputs",
    )
    write_csv(scenarios, "operational_risk/scenario_analysis.csv")

    fairness_rows = []
    pair_definitions = {
        "customer_tenure": np.where(decisions["account_age_days"].lt(90), "New", "Established"),
        "transaction_geography": np.where(decisions["country_mismatch_flag"].eq(1), "Cross_border", "Domestic"),
        "device_status": np.where(decisions["new_device_flag"].eq(1), "New_device", "Trusted_or_existing"),
        "transaction_frequency": np.where(decisions["transactions_last_1h"].ge(8), "High_frequency", "Low_normal_frequency"),
        "customer_segment": decisions["customer_segment"].to_numpy(),
    }
    controlled = decisions["decision"].ne("ALLOW")
    manual = decisions["decision"].eq("MANUAL_REVIEW")
    step_up = decisions["decision"].eq("STEP_UP")
    decline_block = decisions["decision"].isin(["DECLINE", "BLOCK_ACCOUNT"])
    fraud = decisions["transaction_fraud_label"].eq(1)
    for dimension, groups in pair_definitions.items():
        temp = decisions.assign(_group=groups)
        for group, indexes in temp.groupby("_group").groups.items():
            idx = pd.Index(indexes)
            group_fraud = fraud.loc[idx]
            group_controlled = controlled.loc[idx]
            true_positive = int((group_fraud & group_controlled).sum())
            false_positive = int((~group_fraud & group_controlled).sum())
            rows = len(idx)
            fraud_count = int(group_fraud.sum())
            alert_count = int(group_controlled.sum())
            sufficient = rows >= 1000 and fraud_count >= 20
            fairness_rows.append(
                {
                    "dimension": dimension,
                    "group": group,
                    "transactions": rows,
                    "fraud_events": fraud_count,
                    "evidence_sufficient": int(sufficient),
                    "fraud_recall_tpr": safe_div(true_positive, fraud_count),
                    "false_positive_rate": safe_div(false_positive, int((~group_fraud).sum())),
                    "precision": safe_div(true_positive, alert_count),
                    "step_up_rate": float(step_up.loc[idx].mean()),
                    "manual_review_rate": float(manual.loc[idx].mean()),
                    "decline_block_rate": float(decline_block.loc[idx].mean()),
                    "customer_friction_cost": float(false_positive * 2.0),
                }
            )
    fairness = pd.DataFrame(fairness_rows)
    metric_columns = ["fraud_recall_tpr", "false_positive_rate", "precision", "step_up_rate", "manual_review_rate", "decline_block_rate"]
    fairness["max_dimension_gap_pp"] = 0.0
    fairness["review_trigger"] = "NOT_EVALUATED"
    for dimension, indexes in fairness.groupby("dimension").groups.items():
        sufficient_index = [idx for idx in indexes if fairness.at[idx, "evidence_sufficient"] == 1]
        if len(sufficient_index) >= 2:
            gaps = []
            for metric in metric_columns:
                values = fairness.loc[sufficient_index, metric]
                gaps.append(float(values.max() - values.min()))
            max_gap = max(gaps)
            fairness.loc[indexes, "max_dimension_gap_pp"] = max_gap * 100
            fairness.loc[indexes, "review_trigger"] = "FLAG" if max_gap > 0.10 else "PASS"
    fairness["required_action"] = np.where(
        fairness["review_trigger"].eq("FLAG"),
        "Root-cause, business justification, mitigation and owner required",
        np.where(fairness["review_trigger"].eq("PASS"), "Continue monitoring", "Insufficient fraud evidence"),
    )
    fairness = add_metadata(
        fairness,
        "Synthetic",
        "Derived",
        "Synthetic operational segments",
        "Operational disparity diagnostic only; no legal/demographic fairness claim",
    )
    write_csv(fairness, "validation/operational_segment_fairness.csv")

    segment_summary = (
        decisions.groupby(["customer_segment", "channel"], as_index=False)
        .agg(
            transactions=("transaction_id", "size"),
            fraud_transactions=("transaction_fraud_label", "sum"),
            average_model_score=("synthetic_model_score", "mean"),
            average_amount=("amount", "mean"),
            controlled_transactions=("decision", lambda values: values.ne("ALLOW").sum()),
        )
    )
    segment_summary["fraud_rate"] = segment_summary["fraud_transactions"] / segment_summary["transactions"]
    segment_summary["control_rate"] = segment_summary["controlled_transactions"] / segment_summary["transactions"]
    segment_summary = add_metadata(
        segment_summary,
        "Synthetic",
        "Derived",
        "Synthetic customer/channel segments",
        "Controls-testing segment diagnostics only",
    )
    write_csv(segment_summary, "outputs/segment_risk_summary.csv")

    observed_lookup = dict(zip(observed_kpis["metric"], observed_kpis["value"]))
    alert_precision = safe_div(alerts["transaction_fraud_label"].sum(), len(alerts))
    queue_false_positive_rate = float(alerts["transaction_fraud_label"].eq(0).mean())
    sla_breach = float(alerts["sla_breach_flag"].mean())
    max_backlog_days = safe_div(
        max(0, len(alerts) - 250 * decisions["simulation_day"].nunique()), 250
    )
    fraud_appetite_rows = [
        ["Observed fraud transaction rate", observed_lookup["fraud_rate"], "<=0.15%", "0.15%-0.30%", ">0.30%", appetite_status(observed_lookup["fraud_rate"], observed_lookup["fraud_rate"] <= 0.0015, observed_lookup["fraud_rate"] <= 0.003), "Observed"],
        ["Observed fraud amount rate", observed_lookup["fraud_amount_rate"], "<=0.10%", "0.10%-0.25%", ">0.25%", appetite_status(observed_lookup["fraud_amount_rate"], observed_lookup["fraud_amount_rate"] <= 0.001, observed_lookup["fraud_amount_rate"] <= 0.0025), "Observed"],
        ["Observed test fraud-amount recall", selected_test["fraud_amount_recall"], ">=80%", "60%-80%", "<60%", appetite_status(selected_test["fraud_amount_recall"], selected_test["fraud_amount_recall"] >= 0.80, selected_test["fraud_amount_recall"] >= 0.60), "Observed backtest"],
        ["Synthetic alert precision", alert_precision, ">=10%", "5%-10%", "<5%", appetite_status(alert_precision, alert_precision >= 0.10, alert_precision >= 0.05), "Synthetic"],
        ["Synthetic false-positive share", queue_false_positive_rate, "<=90%", "90%-95%", ">95%", appetite_status(queue_false_positive_rate, queue_false_positive_rate <= 0.90, queue_false_positive_rate <= 0.95), "Synthetic"],
        ["Synthetic critical alert SLA breach", sla_breach, "<=2%", "2%-5%", ">5%", appetite_status(sla_breach, sla_breach <= 0.02, sla_breach <= 0.05), "Synthetic"],
        ["Synthetic alert backlog days", max_backlog_days, "<=1", "1-3", ">3", appetite_status(max_backlog_days, max_backlog_days <= 1, max_backlog_days <= 3), "Synthetic"],
    ]
    fraud_appetite = pd.DataFrame(
        fraud_appetite_rows,
        columns=["metric", "current_value", "green_threshold", "amber_threshold", "red_threshold", "status", "evidence_layer"],
    )
    fraud_appetite["threshold_status"] = "Illustrative educational assumption"
    fraud_appetite["owner"] = "Head of Fraud Risk"
    fraud_appetite["action_if_red"] = "Immediate escalation, containment and documented remediation"
    fraud_appetite = add_metadata(
        fraud_appetite,
        "Mixed",
        "Derived/Proxy",
        "Observed benchmark and synthetic operations outputs",
        "Evidence layer stated per metric; no cross-layer performance blending",
    )
    write_csv(fraud_appetite, "governance/fraud_risk_appetite_register.csv")

    net_loss = float(incidents["net_loss"].sum())
    high_incidents = int(incidents["severity"].isin(["High", "Critical"]).sum())
    repeat_incidents = int(incidents["control_failure"].duplicated().sum())
    overdue = int((incidents["status"].ne("Closed")).sum())
    recovery_rate = safe_div(incidents["recovery"].sum(), incidents["gross_loss"].sum())
    operational_appetite = pd.DataFrame(
        [
            ["Net operational loss", net_loss, "<=250k", "250k-500k", ">500k", "RED" if net_loss > 500000 else "AMBER" if net_loss > 250000 else "GREEN"],
            ["High/Critical incidents", high_incidents, "<=2", "3-5", ">5", "RED" if high_incidents > 5 else "AMBER" if high_incidents > 2 else "GREEN"],
            ["Repeat incidents", repeat_incidents, "0", "1", ">1", "RED" if repeat_incidents > 1 else "AMBER" if repeat_incidents == 1 else "GREEN"],
            ["Open remediation actions", overdue, "<=2", "3-5", ">5", "RED" if overdue > 5 else "AMBER" if overdue > 2 else "GREEN"],
            ["Recovery rate", recovery_rate, ">=30%", "15%-30%", "<15%", "GREEN" if recovery_rate >= 0.30 else "AMBER" if recovery_rate >= 0.15 else "RED"],
        ],
        columns=["metric", "current_value", "green_threshold", "amber_threshold", "red_threshold", "status"],
    )
    operational_appetite["threshold_status"] = "Illustrative educational assumption"
    operational_appetite["owner"] = "Operational Risk Committee"
    operational_appetite = add_metadata(
        operational_appetite,
        "Synthetic",
        "Proxy",
        "Synthetic incident register",
        "Scenario risk appetite only; not regulatory capital",
    )
    write_csv(operational_appetite, "governance/operational_risk_appetite_register.csv")

    owners = pd.DataFrame(
        [
            ["Observed fraud model", "Fraud Analytics", "Model Risk", "Risk Committee", "Quarterly"],
            ["Threshold economics", "Fraud Strategy", "Head of Fraud Risk", "Risk Committee", "Monthly"],
            ["Fraud rules", "Fraud Strategy", "Fraud Operations", "Change Advisory Board", "Monthly"],
            ["Hybrid decision engine", "Fraud Platform", "Model Governance", "Risk Committee", "Monthly"],
            ["Alert operations", "Fraud Operations", "Head of Operations", "Operations Committee", "Daily"],
            ["Operational incidents", "Operational Risk", "Business Owner", "Operational Risk Committee", "Monthly"],
            ["Synthetic methodology", "Fraud Analytics", "Independent Validation", "Model Risk Committee", "At change"],
        ],
        columns=["artifact_or_process", "owner", "reviewer", "approver", "review_frequency"],
    )
    owners = add_metadata(owners, "Governance", "Proxy", "Project governance RACI", "Educational ownership design")
    write_csv(owners, "governance/owner_approver_matrix.csv")

    monitoring = pd.DataFrame(
        [
            ["Observed PR-AUC", "Observed", "Monthly", "<80% of baseline", "Model review", "Fraud Analytics"],
            ["Score PSI", "Observed", "Monthly", ">0.25", "Investigate drift and recalibrate", "Model Risk"],
            ["Fraud amount recall", "Observed", "Weekly", "<60%", "Threshold/rule review", "Fraud Strategy"],
            ["Alert precision", "Synthetic/production analogue", "Daily", "<5%", "Tune rules and queue", "Fraud Operations"],
            ["Alerts per day", "Synthetic/production analogue", "Daily", ">250", "Capacity escalation", "Fraud Operations"],
            ["Critical SLA breach", "Synthetic/production analogue", "Daily", ">5%", "Immediate incident", "Fraud Operations"],
            ["Critical rule failure", "Control", "Continuous", ">0", "Fail-safe and rollback", "Fraud Platform"],
            ["Device vendor outage", "Control", "Continuous", ">30 minutes", "Fallback mode", "Vendor Management"],
            ["Override misuse", "Control", "Weekly", ">0", "Access suspension and RCA", "Operational Risk"],
            ["Operational segment gap", "Synthetic/production analogue", "Monthly", ">10pp", "Root-cause and mitigation", "Conduct Risk"],
        ],
        columns=["metric", "evidence_layer", "frequency", "trigger", "management_action", "owner"],
    )
    monitoring = add_metadata(monitoring, "Governance", "Proxy", "Monitoring design", "Illustrative controls and triggers")
    write_csv(monitoring, "governance/monitoring_plan.csv")

    actions = pd.DataFrame(
        [
            ["ACT-01", "Alert backlog breach", "Protect critical queue, surge staffing, tune low-value rules", "Fraud Operations", "24 hours"],
            ["ACT-02", "Fraud amount recall red", "Lower governed threshold and review missed fraud", "Fraud Strategy", "5 days"],
            ["ACT-03", "Critical rule failure", "Fail-safe mode and rollback", "Fraud Platform", "Immediate"],
            ["ACT-04", "Model drift", "Recalibration/challenger review", "Fraud Analytics", "10 days"],
            ["ACT-05", "Operational disparity >10pp", "Driver analysis, mitigation and residual-risk acceptance", "Conduct Risk", "20 days"],
            ["ACT-06", "Override misuse", "Suspend access, preserve logs, launch RCA", "Operational Risk", "Immediate"],
            ["ACT-07", "Vendor outage", "Invoke fallback, vendor escalation, impact review", "Vendor Management", "Immediate"],
        ],
        columns=["action_id", "trigger", "management_action", "owner", "target_timeline"],
    )
    actions = add_metadata(actions, "Governance", "Proxy", "Management action library", "Educational governance design")
    write_csv(actions, "governance/management_action_library.csv")

    exceptions = pd.DataFrame(
        [
            ["EXC-01", "Original Time unavailable", "Observed split uses monitoring-period proxy", "Medium", "Fraud Analytics", "Open limitation", "Recover original source Time"],
            ["EXC-02", "PCA features uninterpretable", "No observed-layer reason codes", "High", "Model Risk", "Accepted for benchmark", "Use synthetic observable layer for controls testing"],
            ["EXC-03", "Validation fraud count below isotonic gate", "Platt calibration only", "Medium", "Model Risk", "Accepted", "Reassess with larger production sample"],
            ["EXC-04", "Synthetic operations outcomes", "Cannot claim realised operational performance", "High", "Operational Risk", "Permanent claim boundary", "Replace with governed production data before deployment"],
        ],
        columns=["exception_id", "exception", "impact", "severity", "owner", "status", "remediation"],
    )
    exceptions = add_metadata(exceptions, "Governance", "Proxy", "Known limitation register", "No production waiver")
    write_csv(exceptions, "governance/exception_register.csv")

    model_use = pd.DataFrame(
        [
            ["Observed champion", "Observed PCA benchmark", "Ranking and historical economics", "No live decisions or reason codes", "Fraud Analytics"],
            ["Observed anomaly", "Observed PCA benchmark", "Challenger analysis", "No automatic decline", "Model Risk"],
            ["Synthetic controls model", "Synthetic", "Controls and UAT testing", "No observed performance claim", "Fraud Strategy"],
            ["Hybrid engine", "Synthetic", "Decision governance demonstration", "No live payment action", "Fraud Platform"],
            ["Friendly-fraud claim score", "Synthetic disputes", "Post-transaction claim review", "No transaction-time decline", "Disputes Team"],
        ],
        columns=["model_or_engine", "data_layer", "permitted_use", "prohibited_use", "owner"],
    )
    model_use = add_metadata(model_use, "Governance", "Proxy", "Model/use governance", "Educational use only")
    write_csv(model_use, "governance/model_use_register.csv")

    audit = pd.DataFrame(
        [
            ["AE-01", "Phase 0 assumptions locked", "governance/assumption_register.csv", "PASS", "Model Risk"],
            ["AE-02", "Observed population reconciled", "data_contract/population_reconciliation.csv", "PASS", "Data Owner"],
            ["AE-03", "Train/validation/test separated", "data_contract/observed_split_reconciliation.csv", "PASS", "Independent Validation"],
            ["AE-04", "Threshold selected on validation", "models/selected_observed_threshold.json", "PASS", "Fraud Strategy"],
            ["AE-05", "Synthetic anti-circularity", "validation/synthetic_anti_circularity_tests.csv", "PASS", "Independent Validation"],
            ["AE-06", "Rule inventory and priority", "rules/fraud_rule_inventory.csv", "PASS", "Fraud Strategy"],
            ["AE-07", "Alert capacity evidence", "outputs/alert_capacity_daily.csv", "PASS", "Fraud Operations"],
            ["AE-08", "Incident ownership", "operational_risk/incident_register.csv", "PASS", "Operational Risk"],
            ["AE-09", "Fairness diagnostic", "validation/operational_segment_fairness.csv", "PASS", "Conduct Risk"],
            ["AE-10", "Final validation", "validation/validation_report.md", "PENDING_PHASE7", "Independent Validation"],
        ],
        columns=["evidence_id", "control_objective", "artifact", "status", "owner"],
    )
    audit = add_metadata(audit, "Governance", "Derived", "Project artifact evidence", "Portfolio audit evidence only")
    write_csv(audit, "governance/audit_evidence_checklist.csv")

    rca_titles = [template[0] for template in incident_templates[:8]]
    rca_sections = []
    for index, title in enumerate(rca_titles, start=1):
        incident = incidents.iloc[index - 1]
        rca_sections.append(
            f"""## RCA {index}: {title}

- **Event:** {title}.
- **Impact:** {incident['customer_count']:,} customer/transaction records; gross loss proxy {incident['gross_loss']:,.2f}; net loss proxy {incident['net_loss']:,.2f} cost units.
- **Detection:** KRI threshold, validation check or investigation escalation.
- **Immediate containment:** Invoke governed fallback, isolate affected component and preserve logs.
- **Root cause:** {incident['root_cause_category']} weakness in {incident['system']}.
- **Contributing factors:** Incomplete pre-release guardrail, dependency concentration and delayed operational detection.
- **Corrective action:** Repair configuration/data flow and reconcile all affected decisions.
- **Preventive action:** Add boundary test, monitoring trigger and release evidence requirement.
- **Owner:** {incident['owner']}.
- **Due date:** {incident['action_due_date']}.
- **Validation evidence:** SIT regression, negative test and independent checklist sign-off.
- **Residual risk:** {incident['residual_risk']} until action closure.
"""
        )
    write_markdown("operational_risk/root_cause_analysis.md", "Operational Incident Root Cause Analyses", "\n".join(rca_sections))
    write_markdown(
        "methodology/operational_risk_methodology.md",
        "Operational Risk Methodology",
        """Operational incidents are simulated independently from observed fraud performance. Each event records gross loss, recovery, net loss, customer impact, root cause, control failure, owner, due date, status and residual risk. `Net Loss = Gross Loss - Recovery`; avoided loss and pending exposure are reported separately where used.

Scenarios evaluate model/vendor/OTP outages, rule deployment error, alert spikes, score-scale mismatch, duplicate processing, data latency, override abuse and third-party compromise. Frequency, loss and control-effectiveness values are educational assumptions, not regulatory capital estimates. Material events require containment, RCA, corrective/preventive action and validation evidence before closure.""",
    )

    flagged = fairness.loc[fairness["review_trigger"].eq("FLAG"), ["dimension", "group", "transactions", "fraud_events", "max_dimension_gap_pp", "required_action"]]
    fairness_action_rows = []
    for dimension in sorted(flagged["dimension"].unique()):
        if dimension == "transaction_frequency":
            driver = "High-frequency is both a synthetic fraud-mechanism symptom and a direct velocity-control input; prevalence and feature design both contribute."
            justification = "Velocity controls are intended to detect card testing and mule bursts, but a high false-positive/control rate is not acceptable without secondary evidence."
            mitigation = "Require model or second-rule support for manual review, monitor high-frequency legitimate merchants separately, cap repetitive low-value alerts and test segment-specific thresholds."
            residual = "Medium"
            owner = "Fraud Strategy with Conduct Risk review"
        else:
            driver = "Synthetic prevalence, observable feature design and threshold interaction require decomposition."
            justification = "No control justification is accepted without evidence of fraud/loss benefit and customer impact."
            mitigation = "Run segment-specific threshold sensitivity, remove unnecessary proxy effects and strengthen secondary-signal requirements."
            residual = "Medium-High"
            owner = "Fraud Strategy with Independent Validation"
        fairness_action_rows.append(
            {
                "dimension": dimension,
                "review_trigger_pp": float(flagged.loc[flagged["dimension"].eq(dimension), "max_dimension_gap_pp"].max()),
                "root_cause_driver": driver,
                "business_justification": justification,
                "mitigation": mitigation,
                "residual_risk": residual,
                "owner": owner,
                "target_date": "2026-08-31",
                "status": "OPEN_MONITORING_ACTION",
            }
        )
    fairness_actions = add_metadata(
        pd.DataFrame(
            fairness_action_rows,
            columns=["dimension", "review_trigger_pp", "root_cause_driver", "business_justification", "mitigation", "residual_risk", "owner", "target_date", "status"],
        ),
        "Synthetic",
        "Derived",
        "Operational segment disparity review",
        "Operational diagnostic action; no legal/demographic fairness conclusion",
    )
    write_csv(fairness_actions, "validation/operational_segment_fairness_actions.csv")
    fairness_body = "## Result\n\n"
    if flagged.empty:
        fairness_body += "No material disparity was identified within the tested operational segments.\n\n"
    else:
        fairness_body += f"**{flagged['dimension'].nunique()} operational dimensions breached the 10 percentage-point review trigger.** A breach is a review flag, not proof of unlawful or demographic unfairness.\n\n"
        fairness_body += dataframe_to_markdown(flagged.drop_duplicates()) + "\n\n"
        fairness_body += "## Root cause and action\n\n" + dataframe_to_markdown(fairness_actions[["dimension", "root_cause_driver", "business_justification", "mitigation", "residual_risk", "owner", "status"]]) + "\n\n"
    fairness_body += "## Governance interpretation\n\nResults are synthetic operational diagnostics. Each flagged dimension is decomposed into prevalence, feature-design and threshold effects, with business justification, mitigation, residual risk and accountable owner. Groups with fewer than 1,000 transactions or 20 fraud events are marked insufficient for fraud-capture comparison. A trigger does not establish legal or demographic unfairness."
    write_markdown("reports/operational_segment_fairness_note.md", "Operational Segment Disparity Diagnostic", fairness_body)

    control_table = controls[["rule_id", "rule_name", "precision", "fraud_recall", "fraud_amount_captured", "net_benefit", "control_status", "recommendation"]].sort_values("net_benefit", ascending=False)
    write_markdown(
        "reports/control_effectiveness_report.md",
        "Control Effectiveness Report",
        f"""## Senior conclusion

Controls are evaluated on fraud capture, amount capture, false positives, net benefit, customer friction, capacity and failure risk. High capture alone is not sufficient: controls with weak precision, excessive friction or no unique contribution require tuning or retirement.

{dataframe_to_markdown(control_table)}

All results are synthetic controls-testing evidence. Production effectiveness would require actual alert outcomes, control exposure, change history and independent validation.""",
    )

    incident_table = loss_summary[["incident_type", "root_cause_category", "incident_count", "gross_loss", "recovery", "net_loss", "open_actions"]]
    write_markdown(
        "reports/incident_management_report.md",
        "Incident Management Report",
        f"""Synthetic incident exposure totals **{incidents['gross_loss'].sum():,.2f} gross**, **{incidents['recovery'].sum():,.2f} recovery** and **{incidents['net_loss'].sum():,.2f} net loss cost units**. Critical incidents require immediate containment; every open material event has an owner, due date, corrective action and residual-risk status.

{dataframe_to_markdown(incident_table)}
""",
    )

    write_markdown(
        "reports/operational_risk_committee_memo.md",
        "Operational Risk Committee Memo",
        f"""## Executive decision

The synthetic incident portfolio contains **{len(incidents)} events**, including **{high_incidents} High/Critical events**, with net loss exposure of **{net_loss:,.2f} cost units**. The dominant concerns are score-scale failure, rule configuration, vendor dependency, override governance and alert capacity.

## Required actions

1. Enforce release blocking for invalid score scale and missing reason codes.
2. Test rules-only, conservative step-up and queue-outage fallbacks every release.
3. Protect Critical/High alert capacity and escalate backlog before SLA failure.
4. Require dual approval and immutable evidence for high-risk overrides.
5. Close open High/Critical remediation with independent validation evidence.

## Scenario exposure

The largest tail scenario is third-party compromise at **400,000 gross / 320,000 net cost units**. These are educational scenario estimates, not regulatory capital calculations.""",
    )
    log.info("Operational risk outputs generated: incidents=%s fairness_flags=%s", len(incidents), flagged["dimension"].nunique())
    print(f"Operational risk PASS | incidents={len(incidents)} | fairness dimensions flagged={flagged['dimension'].nunique()}")


if __name__ == "__main__":
    main()
