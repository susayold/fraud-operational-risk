from __future__ import annotations

import hashlib

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


CAPACITY_PER_DAY = 250


def stable_sample_flag(value: str, percentage: int) -> bool:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100 < percentage


def schedule_queue(alerts: pd.DataFrame) -> pd.DataFrame:
    working = alerts.copy()
    working["arrival_day"] = pd.to_datetime(working["transaction_time"]).dt.day
    processed_day = pd.Series(index=working.index, dtype="float64")
    backlog: list[int] = []
    day = int(working["arrival_day"].min())
    last_arrival = int(working["arrival_day"].max())
    while day <= last_arrival or backlog:
        incoming = working.index[working["arrival_day"].eq(day)].tolist() if day <= last_arrival else []
        backlog.extend(incoming)
        backlog.sort(
            key=lambda idx: (
                -float(working.at[idx, "alert_priority_score"]),
                pd.Timestamp(working.at[idx, "transaction_time"]),
            )
        )
        processed = backlog[:CAPACITY_PER_DAY]
        backlog = backlog[CAPACITY_PER_DAY:]
        processed_day.loc[processed] = day
        day += 1
    working["processed_day"] = processed_day.astype(int)
    working["queue_age_hours"] = ((working["processed_day"] - working["arrival_day"]).clip(lower=0) * 24).astype(float)
    working["capacity_status"] = np.where(working["processed_day"].le(last_arrival), "Within simulation window", "Backlog cleared after window")
    return working


def main() -> None:
    log = get_logger("phase5.alert_operations")
    rng = np.random.default_rng(SEED + 2)
    decisions = pd.read_csv(ROOT / "outputs/hybrid_decision_output.csv.gz")

    queue_required = (
        decisions["decision"].isin(["HOLD", "MANUAL_REVIEW", "DATA_EXCEPTION"])
        | (
            decisions["decision"].isin(["DECLINE", "BLOCK_ACCOUNT"])
            & decisions["transaction_id"].map(lambda value: stable_sample_flag(value, 20))
        )
        | (
            decisions["decision"].eq("STEP_UP")
            & decisions["synthetic_model_score"].ge(0.20)
        )
    )
    alerts = decisions.loc[queue_required].copy()
    alerts.insert(0, "alert_id", [f"AL{i:09d}" for i in range(1, len(alerts) + 1)])
    severity_weight = alerts["review_priority"].map({"CRITICAL": 2.0, "HIGH": 1.5, "MEDIUM": 1.0, "LOW": 0.7}).fillna(0.5)
    detection_confidence = np.clip(
        0.35
        + 0.12 * alerts["rule_hit_count"].clip(upper=3)
        + 0.25 * alerts["synthetic_model_score"]
        + 0.15 * alerts["synthetic_anomaly_score"],
        0.30,
        1.0,
    )
    vulnerability_weight = 1 + alerts["customer_vulnerability_score"] / 200
    potential_loss = alerts["amount"] * alerts["synthetic_model_score"].clip(lower=0.01)
    alerts["detection_confidence"] = detection_confidence.round(4)
    alerts["potential_loss_proxy"] = potential_loss.round(4)
    alerts["alert_priority_score"] = (
        potential_loss * detection_confidence * vulnerability_weight * severity_weight
    ).round(4)
    alerts["assigned_team"] = np.select(
        [
            alerts["primary_reason_code"].isin(["RC_ATO_CRITICAL", "RC_BLACKLIST", "RC_OVERRIDE_MISUSE"]),
            alerts["primary_reason_code"].isin(["RC_MULE_NETWORK", "RC_NEW_BENEFICIARY"]),
            alerts["decision"].eq("DATA_EXCEPTION"),
        ],
        ["ATO & Account Security", "Payments Fraud", "Data Exception Queue"],
        default="Fraud Operations",
    )
    alerts = schedule_queue(alerts)
    handling_time = alerts["review_priority"].map({"CRITICAL": 25, "HIGH": 18, "MEDIUM": 12, "LOW": 8}).fillna(10)
    handling_time = handling_time + rng.integers(-2, 4, len(alerts))
    alerts["handling_minutes"] = np.maximum(5, handling_time)
    alerts["sla_breach_flag"] = (alerts["queue_age_hours"] > alerts["sla_hours"]).astype(int)

    fraud = alerts["transaction_fraud_label"].eq(1).to_numpy()
    fraud_draw = rng.random(len(alerts))
    legitimate_draw = rng.random(len(alerts))
    outcome = np.where(
        fraud,
        np.select(
            [fraud_draw < 0.88, fraud_draw < 0.96],
            ["CONFIRMED_FRAUD", "SUSPECTED_FRAUD"],
            default="PENDING",
        ),
        np.select(
            [legitimate_draw < 0.82, legitimate_draw < 0.90, legitimate_draw < 0.95, legitimate_draw < 0.98],
            ["LEGITIMATE", "CUSTOMER_AUTHORISED", "DUPLICATE", "SYSTEM_ERROR"],
            default="PENDING",
        ),
    )
    alerts["investigation_status"] = np.where(alerts["processed_day"].notna(), "CLOSED", "OPEN")
    alerts["outcome"] = outcome
    alerts["analyst_action"] = pd.Series(outcome).map(
        {
            "CONFIRMED_FRAUD": "Block instrument and initiate recovery",
            "SUSPECTED_FRAUD": "Escalate enhanced investigation",
            "LEGITIMATE": "Release transaction/control",
            "CUSTOMER_AUTHORISED": "Release and record customer confirmation",
            "DUPLICATE": "Reverse duplicate and close",
            "SYSTEM_ERROR": "Route technology incident",
            "PENDING": "Maintain monitoring",
        }
    ).to_numpy()
    prevention_factor = alerts["decision"].map(
        {"BLOCK_ACCOUNT": 0.85, "DECLINE": 0.80, "HOLD": 0.70, "MANUAL_REVIEW": 0.45, "STEP_UP": 0.35, "DATA_EXCEPTION": 0.20}
    ).fillna(0.0)
    alerts["prevented_loss_proxy"] = np.where(
        alerts["outcome"].isin(["CONFIRMED_FRAUD", "SUSPECTED_FRAUD"]),
        alerts["amount"] * prevention_factor,
        0.0,
    ).round(2)
    alerts["recovery_proxy"] = np.where(
        alerts["outcome"].eq("CONFIRMED_FRAUD"), alerts["amount"] * 0.15, 0.0
    ).round(2)
    alerts["data_layer"] = "Synthetic"
    alerts["data_status"] = "Derived"
    alerts["source_type"] = "Synthetic hybrid decisions and simulated investigations"
    alerts["claim_boundary"] = "Controls-testing workload and outcomes; not observed operations"
    write_csv(alerts, "outputs/alert_queue.csv.gz", compression="gzip")

    daily = (
        alerts.groupby("arrival_day", as_index=False)
        .agg(
            incoming_alerts=("alert_id", "size"),
            critical_alerts=("review_priority", lambda values: values.eq("CRITICAL").sum()),
            total_handling_hours=("handling_minutes", lambda values: values.sum() / 60),
            sla_breaches=("sla_breach_flag", "sum"),
            fraud_amount_waiting=("amount", lambda values: values[alerts.loc[values.index, "transaction_fraud_label"].eq(1)].sum()),
        )
    )
    daily["capacity"] = CAPACITY_PER_DAY
    daily["daily_surplus_deficit"] = daily["capacity"] - daily["incoming_alerts"]
    daily["capacity_utilisation"] = daily["incoming_alerts"] / daily["capacity"]
    running_backlog = []
    backlog = 0
    for incoming in daily["incoming_alerts"]:
        backlog = max(0, backlog + int(incoming) - CAPACITY_PER_DAY)
        running_backlog.append(backlog)
    daily["end_of_day_backlog"] = running_backlog
    daily["required_analysts_7_5h"] = np.ceil(daily["total_handling_hours"] / 7.5).astype(int)
    daily = add_metadata(
        daily,
        "Synthetic",
        "Derived",
        "Synthetic alert arrivals and locked 250/day capacity",
        "Workload proxy; no real staffing benchmark",
    )
    write_csv(daily, "outputs/alert_capacity_daily.csv")

    summary = (
        alerts.groupby(["review_priority", "outcome"], as_index=False)
        .agg(
            alerts=("alert_id", "size"),
            amount=("amount", "sum"),
            average_handling_minutes=("handling_minutes", "mean"),
            sla_breaches=("sla_breach_flag", "sum"),
            prevented_loss_proxy=("prevented_loss_proxy", "sum"),
            recovery_proxy=("recovery_proxy", "sum"),
        )
    )
    summary["sla_breach_rate"] = summary["sla_breaches"] / summary["alerts"]
    summary = add_metadata(
        summary,
        "Synthetic",
        "Derived",
        "Synthetic alert investigation outcomes",
        "Simulated operational evidence only",
    )
    write_csv(summary, "outputs/alert_outcome_summary.csv")

    base_daily_alerts = len(alerts) / decisions["simulation_day"].nunique()
    base_handling = float(alerts["handling_minutes"].mean())
    scenarios = [
        ("Base", 1.00, 1.00, 1.00),
        ("Alert volume +25%", 1.25, 1.00, 1.00),
        ("Alert volume +50%", 1.50, 1.00, 1.00),
        ("Handling time +20%", 1.00, 1.20, 1.00),
        ("Analyst absence 20%", 1.00, 1.00, 0.80),
        ("Threshold tightened", 1.35, 1.05, 1.00),
        ("Critical incident spike", 1.60, 1.25, 0.90),
    ]
    sensitivity_rows = []
    for name, volume_factor, handling_factor, capacity_factor in scenarios:
        daily_alerts = base_daily_alerts * volume_factor
        capacity = CAPACITY_PER_DAY * capacity_factor
        daily_backlog = max(0.0, daily_alerts - capacity)
        handling_hours = daily_alerts * base_handling * handling_factor / 60
        sensitivity_rows.append(
            {
                "scenario": name,
                "alerts_per_day": daily_alerts,
                "capacity_per_day": capacity,
                "capacity_utilisation": safe_div(daily_alerts, capacity),
                "daily_backlog_addition": daily_backlog,
                "required_analysts_7_5h": np.ceil(handling_hours / 7.5),
                "estimated_handling_hours": handling_hours,
                "status": "PASS" if daily_alerts <= capacity else "BREACH",
            }
        )
    sensitivity = add_metadata(
        pd.DataFrame(sensitivity_rows),
        "Synthetic",
        "Proxy",
        "Pre-specified workload sensitivity",
        "Illustrative operations capacity only",
    )
    write_csv(sensitivity, "outputs/operations_capacity_sensitivity.csv")

    total_alerts = len(alerts)
    confirmed = int(alerts["outcome"].eq("CONFIRMED_FRAUD").sum())
    false_positive = int(alerts["transaction_fraud_label"].eq(0).sum())
    max_backlog = int(daily["end_of_day_backlog"].max())
    priority_efficiency = (
        alerts.groupby("review_priority", as_index=False)
        .agg(
            alerts=("alert_id", "size"),
            fraud_labels=("transaction_fraud_label", "sum"),
            legitimate_outcomes=("outcome", lambda values: values.eq("LEGITIMATE").sum()),
            non_fraud_alerts=("transaction_fraud_label", lambda values: values.eq(0).sum()),
        )
    )
    priority_efficiency["fraud_precision"] = priority_efficiency["fraud_labels"] / priority_efficiency["alerts"]
    priority_efficiency = priority_efficiency.set_index("review_priority").reindex(["CRITICAL", "HIGH", "MEDIUM"]).reset_index()
    priority_efficiency = add_metadata(
        priority_efficiency,
        "Synthetic",
        "Derived",
        "Synthetic alert queue and investigation outcomes",
        "Priority-efficiency diagnostic; not observed operations",
    )
    write_csv(priority_efficiency, "outputs/priority_queue_efficiency.csv")
    critical_alerts = alerts.loc[alerts["review_priority"].eq("CRITICAL")]
    critical_reasons = critical_alerts["primary_reason_code"].value_counts().to_dict()
    critical_reason_text = ", ".join(f"{reason}: {count}" for reason, count in critical_reasons.items())
    write_markdown(
        "methodology/alert_prioritisation_methodology.md",
        "Alert Prioritisation Methodology",
        """Alert priority combines calibrated synthetic fraud probability, potential loss, detection confidence, customer vulnerability and rule severity. Critical and high-priority cases are processed before lower priority cases. `DECLINE` and `BLOCK_ACCOUNT` actions enter a 20% quality-assurance sample; automated `STEP_UP` enters human review only when score is at least 0.20. This separates automated control actions from investigator workload.

The locked capacity is 250 alerts per simulated day. Handling-time assumptions are 25, 18, 12 and 8 minutes for critical, high, medium and low alerts, with seeded variation. These are educational staffing proxies, not market benchmarks.""",
    )
    report_table = sensitivity[["scenario", "alerts_per_day", "capacity_per_day", "capacity_utilisation", "daily_backlog_addition", "required_analysts_7_5h", "status"]]
    priority_display = priority_efficiency[["review_priority", "alerts", "fraud_labels", "fraud_precision", "legitimate_outcomes", "non_fraud_alerts"]].copy()
    priority_display["fraud_precision"] = priority_display["fraud_precision"].map(lambda value: f"{value:.2%}")
    write_markdown(
        "reports/alert_operations_report.md",
        "Alert Operations and Capacity Report",
        f"""## Base outcome

- Investigation queue: **{total_alerts:,} alerts** across 30 simulated arrival days.
- Average incoming volume: **{base_daily_alerts:,.1f} alerts/day** versus locked capacity of **{CAPACITY_PER_DAY}**.
- Maximum end-of-day backlog: **{max_backlog:,} alerts**.
- Confirmed synthetic fraud investigations: **{confirmed:,}**.
- Legitimate transactions in queue (false-positive workload proxy): **{false_positive:,}**.
- SLA breach rate: **{alerts['sla_breach_flag'].mean():.2%}**.

## Capacity sensitivity

{dataframe_to_markdown(report_table)}

## Priority queue efficiency

{dataframe_to_markdown(priority_display)}

## Critical-queue efficiency

Priority is severity-based rather than probability-ranked. The CRITICAL queue is dominated by simulated blacklist and privileged-override controls: {critical_reason_text}. Only **{int(critical_alerts['transaction_fraud_label'].sum())}** of the **{len(critical_alerts)}** alerts carry the synthetic fraud label.

The **{critical_alerts['outcome'].eq('LEGITIMATE').mean():.2%}** LEGITIMATE outcome share is one investigation disposition, not the complete false-positive rate; **{int(critical_alerts['transaction_fraud_label'].eq(0).sum())}** of **{len(critical_alerts)}** CRITICAL alerts are non-fraud in the synthetic label. This is a material control-efficiency weakness. The rules should retain severity protection, but require blacklist-data validation, quality assurance, precision monitoring and tuning. High priority must not be interpreted as high predictive precision.

Management action: Owner = Fraud Strategy / Data Owner. Validate blacklist-generation quality, separate confirmed-list hits from proxy hits, monitor precision and require dual approval before rule tuning.

## Management interpretation

The queue is governed separately from automated step-up/decline actions. A capacity breach requires threshold/rule tuning, temporary staffing, priority protection for critical alerts and explicit backlog risk acceptance. The project does not claim that simulated handling times or outcomes represent a bank's actual fraud operation.
""",
    )
    log.info("Alert operations built: alerts=%s base_daily=%.2f max_backlog=%s", total_alerts, base_daily_alerts, max_backlog)
    print(f"Alert operations PASS | alerts={total_alerts:,} | avg/day={base_daily_alerts:.1f} | max backlog={max_backlog:,}")


if __name__ == "__main__":
    main()
