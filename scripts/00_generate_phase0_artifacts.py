from __future__ import annotations

import csv
import os
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_CORE_ENV = os.getenv("FINANCIAL_RISK_DATA_CORE")
DATA_CORE = Path(DATA_CORE_ENV) if DATA_CORE_ENV else PROJECT_ROOT.parent / "_data_core_placeholder"

RAW_OBSERVED = DATA_CORE / "data" / "raw" / "openml_creditcard_fraud_284807.csv.gz"
SILVER_OBSERVED = DATA_CORE / "data" / "silver" / "silver_fraud_transactions.csv.gz"
GOLD_KRI = DATA_CORE / "data" / "gold" / "gold_fraud_kri.csv"

OBSERVED_TARGET = PROJECT_ROOT / "data" / "observed" / "fraud_pca_input.csv.gz"
OBSERVED_SAMPLE = PROJECT_ROOT / "data" / "observed" / "fraud_pca_sample.csv"
REFERENCE_KRI = PROJECT_ROOT / "data" / "reference" / "project0_gold_fraud_kri.csv"

RUN_TS = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dirs() -> None:
    dirs = [
        "data_contract",
        "data/observed",
        "data/synthetic",
        "data/reference",
        "methodology",
        "models",
        "rules",
        "outputs",
        "operational_risk",
        "governance",
        "testing",
        "validation",
        "reports",
        "excel",
        "scripts",
        "logs",
    ]
    for d in dirs:
        (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)


def write_text(rel_path: str, text: str) -> None:
    path = PROJECT_ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_csv(rel_path: str, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path = PROJECT_ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def observed_stats() -> dict[str, object]:
    df = pd.read_csv(
        SILVER_OBSERVED,
        usecols=["transaction_id", "amount", "fraud_flag", "monitoring_period"],
    )
    fraud = df[df["fraud_flag"] == 1]
    return {
        "rows": int(len(df)),
        "fraud_cases": int(df["fraud_flag"].sum()),
        "non_fraud_cases": int((df["fraud_flag"] == 0).sum()),
        "fraud_rate": float(df["fraud_flag"].mean()),
        "transaction_amount": float(df["amount"].sum()),
        "fraud_amount": float(fraud["amount"].sum()),
        "min_amount": float(df["amount"].min()),
        "max_amount": float(df["amount"].max()),
        "min_monitoring_period": int(df["monitoring_period"].min()),
        "max_monitoring_period": int(df["monitoring_period"].max()),
        "duplicate_transaction_id": int(df["transaction_id"].duplicated().sum()),
    }


def prepare_data_files() -> dict[str, object]:
    if not SILVER_OBSERVED.exists():
        raise FileNotFoundError(f"Missing observed fraud source: {SILVER_OBSERVED}")
    if not OBSERVED_TARGET.exists():
        shutil.copy2(SILVER_OBSERVED, OBSERVED_TARGET)
    if GOLD_KRI.exists() and not REFERENCE_KRI.exists():
        shutil.copy2(GOLD_KRI, REFERENCE_KRI)

    sample_df = pd.read_csv(SILVER_OBSERVED, nrows=5000)
    sample_df.to_csv(OBSERVED_SAMPLE, index=False)

    return observed_stats()


def build_observed_contract() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    common = {
        "data_layer": "Layer A - Observed PCA Fraud Benchmark",
        "data_status": "Observed",
        "source_type": "Project 0 silver fraud data derived from public OpenML credit card fraud data",
        "claim_boundary": "Observed predictive benchmark only; no business reason-code claim from PCA variables",
    }

    def add(field, required, source_col, dtype, purpose, status, notes):
        rows.append(
            {
                "field": field,
                "required_status": required,
                "source_column": source_col,
                "expected_type": dtype,
                "business_purpose": purpose,
                "availability_status": status,
                "phase0_decision": "LOCKED",
                "notes": notes,
                **common,
            }
        )

    add("transaction_id", "Required", "transaction_id", "integer", "Unique transaction key for reconciliation and duplicate checks", "Available", "Generated in Project 0 silver layer; duplicate count must be zero.")
    for i in range(1, 29):
        add(f"v{i}", "Required", f"v{i}", "numeric", "PCA feature for observed fraud benchmark modelling", "Available", "May be used for predictive modelling; must not be translated into business reason codes.")
    add("amount", "Required", "amount", "numeric", "Transaction exposure and fraud amount capture economics", "Available", "Cost unit is used unless dataset currency is formally confirmed.")
    add("fraud_flag", "Required", "fraud_flag", "binary 0/1", "Observed fraud label for benchmark model validation", "Available", "Mapped from public dataset Class field.")
    add("amount_band", "Optional", "amount_band", "categorical", "Monitoring and segmentation", "Available", "Derived in Project 0.")
    add("pca_abs_signal", "Optional", "pca_abs_signal", "numeric", "PCA signal monitoring and KRI support", "Available", "Derived in Project 0; not a customer-facing reason code.")
    add("pca_signal_band", "Optional", "pca_signal_band", "categorical", "KRI segmentation", "Available", "Derived in Project 0.")
    add("monitoring_period", "Required for stability", "monitoring_period", "integer", "Time-order proxy for stability and monitoring", "Available", "Derived in Project 0 because current raw copy does not expose original Time.")
    add("source_dataset", "Required", "source_dataset", "string", "Lineage and source manifest", "Available", "Identifies the Project 0 source dataset.")
    add("Time", "Unavailable / not used in MVP", "not_available_in_current_project0_copy", "numeric", "Would support original time-order split if present", "Unavailable", "The current Project 0 raw copy does not contain Time; use monitoring_period as a controlled proxy and disclose limitation.")
    return rows


def build_synthetic_contract() -> list[dict[str, object]]:
    fields = [
        ("transaction_id", "Required", "Unique synthetic transaction key"),
        ("customer_id", "Required", "Customer key for tenure, frequency and repeat behaviour"),
        ("transaction_datetime", "Required", "Event timestamp for velocity and SLA logic"),
        ("amount", "Required", "Transaction exposure and alert economics"),
        ("channel", "Required", "Channel segmentation such as card_not_present, POS, wallet or transfer"),
        ("merchant_category", "Required", "Merchant and control segmentation"),
        ("country_pair_type", "Required", "Domestic versus cross-border diagnostic group"),
        ("device_id", "Required", "Device linkage"),
        ("device_trust_status", "Required", "Trusted versus new device diagnostic group"),
        ("beneficiary_id", "Required", "Beneficiary risk and velocity testing"),
        ("beneficiary_age_days", "Required", "New beneficiary rule support"),
        ("customer_tenure_days", "Required", "New versus established customer group"),
        ("velocity_1h", "Required", "Velocity rule feature"),
        ("velocity_24h", "Required", "Velocity rule feature"),
        ("transaction_frequency_band", "Required", "Low versus high transaction-frequency diagnostic group"),
        ("project3_risk_segment_synthetic", "Optional contextual", "Synthetic customer-context feature only; non-causal"),
        ("latent_fraud_archetype", "Required hidden", "Hidden data-generation driver; must not be used directly by detection rules"),
        ("synthetic_fraud_label", "Required output", "Synthetic transaction-fraud label generated from latent risk and stochastic outcomes"),
        ("rule_trigger_flags", "Required derived", "Rule-testing output, not a label source"),
        ("data_layer", "Required", "Mandatory output separation field"),
        ("data_status", "Required", "Mandatory output separation field"),
        ("source_type", "Required", "Mandatory output separation field"),
        ("claim_boundary", "Required", "Mandatory output separation field"),
        ("dispute_id", "Required only for friendly-fraud claim layer", "Separate dispute/claim key"),
        ("friendly_fraud_label", "Required only for friendly-fraud claim layer", "Post-transaction claim outcome; not real-time transaction fraud"),
    ]
    rows = []
    for field, required, purpose in fields:
        rows.append(
            {
                "field": field,
                "required_status": required,
                "expected_type": "string/numeric/date/binary as applicable",
                "data_layer": "Layer B - Synthetic Controls-Testing Environment",
                "data_status": "Synthetic",
                "source_type": "Generated from documented synthetic methodology",
                "claim_boundary": "Controls-testing, rule governance, alert operations and UAT/SIT only; not observed fraud performance",
                "business_purpose": purpose,
                "phase0_decision": "LOCKED",
                "notes": "Must remain interpretable and must not be mixed with observed PCA performance claims.",
            }
        )
    return rows


def build_assumptions() -> list[dict[str, object]]:
    return [
        {
            "assumption_id": "A001",
            "assumption_name": "investigation_cost_per_alert",
            "base_value": "5.00",
            "unit": "cost units per alert",
            "status": "LOCKED",
            "owner": "Risk Analytics",
            "used_in": "threshold economics, alert capacity, net benefit",
            "sensitivity_required": "Yes",
            "claim_boundary": "Illustrative educational assumption, not a market benchmark",
            "change_control": "Change request required before model review",
        },
        {
            "assumption_id": "A002",
            "assumption_name": "preventable_loss_rate",
            "base_value": "70%",
            "unit": "percent of captured fraud amount",
            "status": "LOCKED",
            "owner": "Fraud Risk",
            "used_in": "prevented loss and net benefit",
            "sensitivity_required": "Yes",
            "claim_boundary": "Illustrative educational assumption",
            "change_control": "Change request required before model review",
        },
        {
            "assumption_id": "A003",
            "assumption_name": "alert_capacity_per_day",
            "base_value": "250",
            "unit": "alerts per day",
            "status": "LOCKED",
            "owner": "Fraud Operations",
            "used_in": "threshold feasibility and backlog risk",
            "sensitivity_required": "Yes",
            "claim_boundary": "Portfolio capacity proxy",
            "change_control": "Capacity change must show threshold impact",
        },
        {
            "assumption_id": "A004",
            "assumption_name": "false_positive_friction_cost",
            "base_value": "2.00",
            "unit": "cost units per false positive action",
            "status": "LOCKED",
            "owner": "Customer Risk",
            "used_in": "net benefit and customer friction trade-off",
            "sensitivity_required": "Yes",
            "claim_boundary": "Illustrative educational assumption",
            "change_control": "Change request required before model review",
        },
        {
            "assumption_id": "A005",
            "assumption_name": "candidate_alert_rate_grid",
            "base_value": "0.05%, 0.10%, 0.20%, 0.50%, 1.00%, 2.00%, 5.00%",
            "unit": "share of transactions alerted",
            "status": "LOCKED",
            "owner": "Model Risk",
            "used_in": "threshold search grid",
            "sensitivity_required": "No",
            "claim_boundary": "Threshold grid frozen before model review",
            "change_control": "Grid change requires documented approval",
        },
        {
            "assumption_id": "A006",
            "assumption_name": "probability_calibration_method",
            "base_value": "Platt/sigmoid default; isotonic only if calibration fraud count >= 200 or CV evidence supports it",
            "unit": "method rule",
            "status": "LOCKED",
            "owner": "Model Risk",
            "used_in": "economic probability usage",
            "sensitivity_required": "Conditional",
            "claim_boundary": "Calibration fitted outside final test set",
            "change_control": "Calibration method change requires validation note",
        },
        {
            "assumption_id": "A007",
            "assumption_name": "fairness_gap_review_trigger",
            "base_value": ">10pp absolute gap",
            "unit": "percentage points",
            "status": "LOCKED",
            "owner": "Operational Risk",
            "used_in": "operational segment fairness diagnostics",
            "sensitivity_required": "No",
            "claim_boundary": "Operational segment diagnostic only; no legal fairness claim",
            "change_control": "Trigger change requires governance approval",
        },
        {
            "assumption_id": "A008",
            "assumption_name": "fairness_minimum_sample_rule",
            "base_value": ">=1,000 transactions per group and >=20 fraud events for fraud-capture comparisons",
            "unit": "count rule",
            "status": "LOCKED",
            "owner": "Operational Risk",
            "used_in": "diagnostic reliability",
            "sensitivity_required": "No",
            "claim_boundary": "Suppress or caveat insufficient evidence groups",
            "change_control": "Change requires validation sign-off",
        },
        {
            "assumption_id": "A009",
            "assumption_name": "friendly_fraud_timing",
            "base_value": "post-transaction dispute/claim layer",
            "unit": "method rule",
            "status": "LOCKED",
            "owner": "Fraud Risk",
            "used_in": "synthetic disputes design",
            "sensitivity_required": "No",
            "claim_boundary": "Not treated as real-time transaction fraud",
            "change_control": "Unsupported friendly-fraud placeholders must be removed",
        },
        {
            "assumption_id": "A010",
            "assumption_name": "project3_credit_segment_usage",
            "base_value": "synthetic contextual feature only",
            "unit": "claim rule",
            "status": "LOCKED",
            "owner": "Portfolio Governance",
            "used_in": "synthetic customer-context enrichment",
            "sensitivity_required": "No",
            "claim_boundary": "No credit-fraud causality claim",
            "change_control": "Any causal wording must be removed",
        },
        {
            "assumption_id": "A011",
            "assumption_name": "observed_time_field",
            "base_value": "monitoring_period proxy; original Time unavailable in current Project 0 copy",
            "unit": "data availability rule",
            "status": "LOCKED",
            "owner": "Data Governance",
            "used_in": "split/stability design",
            "sensitivity_required": "No",
            "claim_boundary": "Use proxy disclosure in all observed benchmark reporting",
            "change_control": "If Time is recovered, update contract and reconciliation",
        },
    ]


def docs(stats: dict[str, object]) -> dict[str, str]:
    fraud_rate_pct = float(stats["fraud_rate"]) * 100
    docs_out: dict[str, str] = {}
    docs_out["01_project5_scope.md"] = f"""
# Project 5 Scope - Fraud Detection, Transaction Risk Controls and Operational Risk Governance

Status: Phase 0 locked for build.
Generated: {RUN_TS}

## Executive Objective

Project 5 demonstrates how a Risk function detects suspicious transactions, prioritises alerts, balances fraud loss against customer friction, manages operational incidents and proves that controls work.

The project is not just a model. It is an end-to-end fraud-risk operating framework:

Transaction data -> risk indicators -> observed benchmark models -> deterministic rules -> hybrid decision engine -> alert queue -> investigation outcome -> fraud loss/prevented loss -> incident and control failure -> KRI monitoring -> management action.

## Two-Layer Design

Layer A: Observed PCA Fraud Benchmark.
- Source: Project 0 observed public fraud dataset.
- Current available population: {stats["rows"]:,} transactions, {stats["fraud_cases"]:,} fraud cases, fraud rate {fraud_rate_pct:.4f}%.
- Purpose: predictive benchmark, PR-AUC, precision/recall, fraud amount capture, threshold economics, calibration review.
- Boundary: PCA variables cannot support business reason codes such as device-risk or beneficiary-risk rules.

Layer B: Synthetic Controls-Testing Environment.
- Source: documented synthetic generation methodology.
- Purpose: interpretable fraud rules, reason codes, alert operations, incidents, KRIs, UAT/SIT and governance.
- Boundary: synthetic controls testing only, not observed fraud performance.

## Non-Claim

This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Phase 0 Build Lock

No model training is allowed before data, label, anti-circularity, threshold economics, probability calibration, friendly-fraud timing and fairness diagnostics are locked.
"""

    docs_out["04_p5_data_availability_check.md"] = f"""
# Project 5 Data Availability Check

Generated: {RUN_TS}

## Available Project 0 Sources

| Layer | Path | Status | Use |
|---|---|---|---|
| Raw observed | Project 0 canonical source | Available when `FINANCIAL_RISK_DATA_CORE` is configured | Source lineage; current copy has PCA fields, Amount and Class but not Time |
| Silver observed | Project 0 canonical silver fraud source | Available when `FINANCIAL_RISK_DATA_CORE` is configured | Primary Project 5 observed benchmark input |
| Gold KRI | Project 0 canonical gold KRI source | Available when `FINANCIAL_RISK_DATA_CORE` is configured | Reference KRI aggregation from Project 0 |

## Observed Data Profile

| Metric | Value |
|---|---:|
| Rows | {stats["rows"]:,} |
| Fraud cases | {stats["fraud_cases"]:,} |
| Non-fraud cases | {stats["non_fraud_cases"]:,} |
| Fraud rate | {fraud_rate_pct:.4f}% |
| Transaction amount | {stats["transaction_amount"]:,.2f} cost units |
| Fraud amount | {stats["fraud_amount"]:,.2f} cost units |
| Minimum amount | {stats["min_amount"]:,.2f} |
| Maximum amount | {stats["max_amount"]:,.2f} |
| Monitoring period range | {stats["min_monitoring_period"]} to {stats["max_monitoring_period"]} |
| Duplicate transaction IDs | {stats["duplicate_transaction_id"]:,} |

## Availability Decision

The observed fraud benchmark is available and sufficient for Phase 1 modelling. The dataset has extreme class imbalance, which is appropriate for PR-AUC, recall/precision, fraud amount capture and threshold economics.

The current Project 0 raw copy does not expose original `Time`. Project 5 will use `monitoring_period` as a documented time-order/stability proxy unless the original Time field is recovered later.

## Data Claim Boundary

Observed PCA data supports predictive benchmarking only. It does not support reason-code or rule explanations such as device trust, cross-border risk, beneficiary age, OTP failure or account takeover. Those concepts belong only to the synthetic controls-testing layer.
"""

    docs_out["05_observed_vs_synthetic_data_design.md"] = """
# Observed vs Synthetic Data Design

## Core Principle

Project 5 uses two data layers because one public observed fraud dataset cannot answer every fraud-management question.

| Layer | Data status | Main use | Permitted claim | Prohibited claim |
|---|---|---|---|---|
| Layer A | Observed | Predictive benchmark and class-imbalance modelling | Observed fraud classification performance, PR-AUC, fraud amount capture | Device rule, beneficiary rule, OTP failure, account takeover reason code |
| Layer B | Synthetic | Controls testing and operational governance | Rule logic, alert workflow, UAT/SIT, KRI, incident process | Real-world fraud model performance |

## Mandatory Output Fields

Every downstream output must include:

- `data_layer`
- `data_status`
- `source_type`
- `claim_boundary`

Allowed values include Observed, Derived, Proxy, Synthetic and Unavailable.

## Senior Risk Rationale

The split prevents two common portfolio errors:

1. Using PCA variables to invent business explanations that the data cannot support.
2. Presenting synthetic rule performance as if it were observed real-world fraud performance.

Project 5 can still tell one coherent story: observed data proves modelling discipline; synthetic data proves risk-system and operational-control thinking.
"""

    docs_out["06_fraud_label_definition.md"] = """
# Fraud Label Definition

## Layer A - Observed PCA Benchmark

Observed fraud label:

`fraud_flag = 1` means the transaction is labelled fraud in the public observed dataset.

`fraud_flag = 0` means the transaction is labelled non-fraud in the public observed dataset.

This label is suitable for model benchmarking, PR-AUC, recall, precision and fraud amount capture. It is not suitable for explaining fraud reason codes because the explanatory features are PCA-transformed.

## Layer B - Synthetic Transaction Fraud

Synthetic fraud labels must be generated from latent fraud mechanisms and stochastic outcomes, not copied from detection rules.

Allowed hidden drivers:

- account takeover propensity;
- unusual beneficiary risk;
- abnormal device behaviour;
- cross-border transaction stress;
- velocity spike;
- merchant/category exposure;
- customer-history risk.

Observable rule features must be generated separately from the hidden fraud label. A rule can help detect fraud, but it must not define fraud by itself.

## Anti-Circularity Standard

The following must be true after synthetic generation:

- rule precision is less than 100%;
- rule recall is less than 100%;
- legitimate transactions can trigger controls;
- fraud transactions can avoid obvious rules;
- model or anomaly score can add value beyond deterministic rules;
- deterministic rules can add governance value beyond model score.

## Friendly Fraud / Dispute Abuse

Friendly fraud is not a real-time transaction fraud label. It is a post-transaction dispute or claim-risk outcome. It must be generated and evaluated in a separate dispute dataset.
"""

    docs_out["07_synthetic_fraud_generation_methodology.md"] = """
# Synthetic Fraud Generation Methodology

## Objective

Create an interpretable controls-testing environment that supports deterministic rules, reason codes, alert queues, incident simulation, KRIs and UAT/SIT.

## Entity Design

Synthetic layer will contain:

- customers;
- devices;
- beneficiaries;
- merchants/categories;
- transactions;
- dispute/claim records for friendly fraud;
- incidents and control failures.

## Generation Flow

1. Generate customers with tenure, transaction frequency and synthetic risk segment.
2. Generate devices with trusted/new status and relationship to customers.
3. Generate beneficiaries with age, history and risk flags.
4. Generate transactions with amount, channel, geography, merchant category and timestamp.
5. Generate hidden latent fraud archetype and latent fraud probability.
6. Generate observable features separately from the hidden label.
7. Generate synthetic fraud label using stochastic outcome logic.
8. Generate deterministic rule triggers from observable fields only.
9. Generate alert decision and investigation outcome.
10. Generate incidents and control failures after transactions.

## Required Fraud Archetypes

- account takeover style transaction risk;
- new beneficiary / mule-risk style transaction risk;
- high-velocity transaction risk;
- cross-border unusual activity risk;
- merchant/category exposure risk.

Friendly fraud is handled separately as post-transaction dispute/claim risk.

## Anti-Circularity Controls

The label generation code must keep hidden drivers separate from rule conditions. Detection rules cannot read hidden fraud archetype or latent fraud probability directly.

Validation must prove that rules do not perfectly recreate the label.
"""

    docs_out["09_threshold_economics_decision.md"] = """
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
2. Realised net benefit > 0.
3. Fraud transaction recall >= 80%.
4. Precision >= 10%.
5. Fraud amount recall:
   - PASS if >=80%.
   - AMBER exception if 60%-80%.

Selection uses PASS candidates first. If no PASS candidate exists, eligible AMBER candidates may be used. Within the selected pool, maximise validation realised net benefit and use fraud-amount recall and precision as tie breakers. The final test set must not influence selection.

Formalised during v1.0.1 public remediation. Underlying code and selected threshold unchanged; not backdated as the original Phase 0 lock.

Any post-lock change requires a versioned change request, owner, approval, reason, before/after threshold impact and updated change log.
"""

    docs_out["10_probability_calibration_decision.md"] = """
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
"""

    docs_out["11_friendly_fraud_claim_methodology.md"] = """
# Friendly Fraud Claim Methodology

## Decision

Friendly fraud / dispute abuse is a post-transaction claim problem. It must not be generated like real-time account takeover, velocity fraud or beneficiary-risk transaction fraud.

## Required Dataset

`data/synthetic/synthetic_disputes.csv`

Required fields:

- `dispute_id`
- `transaction_id`
- `claim_date`
- `days_to_claim`
- `claim_reason`
- `prior_dispute_count`
- `merchant_category`
- `delivery_confirmation_proxy`
- `claim_amount`
- `friendly_fraud_label`
- `claim_outcome`

## Control Objective

Friendly-fraud controls support claim review, merchant review and repeat-dispute monitoring. They do not support real-time transaction blocking in this MVP unless a separate governance decision is made.

## Implementation Status

Phase 0 locks the separate post-transaction claim design. After Phase 3, implementation status must be updated to reference `data/synthetic/synthetic_disputes.csv` and `outputs/friendly_fraud_claim_risk_summary.csv`; transaction fraud and friendly-fraud claim labels must remain separate.
"""

    docs_out["12_project3_project6_linkage_note.md"] = """
# Project 3 and Project 6 Linkage Note

## Project 3 Linkage

Project 5 may use Project 3-derived risk segment or PD band as a synthetic customer-context feature only.

Permitted wording:

Project 3-derived credit-risk segments were used as a synthetic customer-context feature in the controls-testing environment. Any relationship with fraud vulnerability is simulated and is not evidence of real-world credit-fraud causality.

Prohibited wording:

- credit risk causes fraud;
- PD predicts transaction fraud in the observed dataset;
- Project 3 scorecard is a fraud model.

## Project 6 Linkage

Project 6 contributes governance design, not fraud labels:

- rule priority;
- UAT/SIT structure;
- fallback behaviour;
- release controls;
- exception handling;
- RCA discipline.

Project 5 can reuse these governance patterns when building rule inventory, rule priority matrix, test evidence and incident management.
"""

    docs_out["13_operational_segment_fairness_spec.md"] = """
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
"""

    docs_out["14_phase0_validation_gate.md"] = """
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
"""
    return docs_out


def validation_rows(stats: dict[str, object]) -> list[dict[str, object]]:
    checks = [
        ("Files", "Project folder structure exists", "PASS", "All official folders created."),
        ("Observed data", "Project 0 silver fraud file exists", "PASS" if SILVER_OBSERVED.exists() else "FAIL", str(SILVER_OBSERVED)),
        ("Observed data", "Observed input copied to Project 5", "PASS" if OBSERVED_TARGET.exists() else "FAIL", str(OBSERVED_TARGET)),
        ("Observed data", "Observed row count >= 100,000", "PASS" if int(stats["rows"]) >= 100000 else "FAIL", f"{stats['rows']:,} rows"),
        ("Observed data", "Observed fraud label has both classes", "PASS" if int(stats["fraud_cases"]) > 0 and int(stats["non_fraud_cases"]) > 0 else "FAIL", f"{stats['fraud_cases']:,} fraud and {stats['non_fraud_cases']:,} non-fraud"),
        ("Observed data", "Duplicate transaction_id count is zero", "PASS" if int(stats["duplicate_transaction_id"]) == 0 else "FAIL", f"{stats['duplicate_transaction_id']:,} duplicates"),
        ("Claim boundary", "PCA variables not used as business reason codes", "PASS", "Locked in observed contract and design note."),
        ("Synthetic data", "Synthetic input contract created before generation", "PASS", "Generation not performed in Phase 0."),
        ("Label methodology", "Synthetic label anti-circularity rules documented", "PASS", "Hidden drivers separated from observable rule features."),
        ("Threshold economics", "Investigation cost 5.00 recorded", "PASS", "governance/assumption_register.csv"),
        ("Threshold economics", "Preventable loss rate 70% recorded", "PASS", "governance/assumption_register.csv"),
        ("Threshold economics", "Alert capacity 250/day recorded", "PASS", "governance/assumption_register.csv"),
        ("Threshold economics", "False-positive friction cost 2.00 recorded", "PASS", "governance/assumption_register.csv"),
        ("Threshold economics", "Candidate threshold grid frozen", "PASS", "0.05%, 0.10%, 0.20%, 0.50%, 1.00%, 2.00%, 5.00%."),
        ("Calibration", "Calibration method and triggers frozen", "PASS", "Platt default; isotonic only under minimum evidence rule."),
        ("Friendly fraud", "Friendly fraud treated as post-transaction claim risk", "PASS", "Separate synthetic_disputes.csv design."),
        ("Fairness", "Operational segment groups documented", "PASS", "new/established, domestic/cross-border, trusted/new device, frequency, synthetic segment."),
        ("Fairness", "10pp review trigger documented", "PASS", "No legal fairness claim."),
        ("Cross-project linkage", "P3/P6 linkage boundary documented", "PASS", "Contextual and governance only; no causality claim."),
        ("Model training", "No model training performed in Phase 0", "PASS", "Phase 1 begins only after this gate."),
    ]
    return [
        {
            "check_group": group,
            "check_name": name,
            "status": status,
            "evidence": evidence,
            "severity": "Critical" if status == "FAIL" else "Info",
            "owner": "Risk Analytics",
            "action_required": "Resolve before Phase 1" if status == "FAIL" else "None",
        }
        for group, name, status, evidence in checks
    ]


def main() -> None:
    ensure_dirs()
    stats = prepare_data_files()

    observed_contract = build_observed_contract()
    synthetic_contract = build_synthetic_contract()
    assumptions = build_assumptions()

    observed_fields = list(observed_contract[0].keys())
    synthetic_fields = list(synthetic_contract[0].keys())
    assumption_fields = list(assumptions[0].keys())

    write_csv("02_p5_observed_input_contract.csv", observed_contract, observed_fields)
    write_csv("data_contract/p5_observed_input_contract.csv", observed_contract, observed_fields)
    write_csv("03_p5_synthetic_input_contract.csv", synthetic_contract, synthetic_fields)
    write_csv("data_contract/p5_synthetic_input_contract.csv", synthetic_contract, synthetic_fields)
    write_csv("08_assumption_register.csv", assumptions, assumption_fields)
    write_csv("governance/assumption_register.csv", assumptions, assumption_fields)

    doc_map = docs(stats)
    for rel_path, text in doc_map.items():
        write_text(rel_path, text)

    structured_map = {
        "04_p5_data_availability_check.md": "data_contract/p5_data_availability_check.md",
        "05_observed_vs_synthetic_data_design.md": "data_contract/observed_vs_synthetic_design.md",
        "06_fraud_label_definition.md": "methodology/fraud_label_definition.md",
        "07_synthetic_fraud_generation_methodology.md": "methodology/synthetic_fraud_generation_methodology.md",
        "09_threshold_economics_decision.md": "methodology/threshold_economics_decision.md",
        "10_probability_calibration_decision.md": "methodology/probability_calibration_decision.md",
        "11_friendly_fraud_claim_methodology.md": "methodology/friendly_fraud_claim_methodology.md",
        "12_project3_project6_linkage_note.md": "reports/project3_project6_linkage_note.md",
        "13_operational_segment_fairness_spec.md": "methodology/operational_segment_fairness_spec.md",
        "14_phase0_validation_gate.md": "validation/phase0_validation_gate.md",
    }
    for src, dst in structured_map.items():
        write_text(dst, (PROJECT_ROOT / src).read_text(encoding="utf-8"))

    write_text(
        "README.md",
        f"""
# Project 5 - Fraud Detection, Transaction Risk Controls and Operational Risk Governance

Status: Phase 0 locked. Model training has not started.

## What This Project Proves

This project shows how a Risk Analyst can connect fraud modelling, transaction rules, alert operations, operational risk incidents, KRIs, UAT/SIT and management reporting into one controlled fraud-risk framework.

## Current Phase

Phase 0 has locked:

- scope;
- observed and synthetic input contracts;
- observed/synthetic claim separation;
- fraud label methodology;
- synthetic generation methodology;
- threshold economics assumptions;
- probability calibration decision;
- friendly-fraud claim methodology;
- Project 3 / Project 6 linkage boundaries;
- operational segment fairness diagnostics;
- validation gate.

## Data Summary

Observed Project 0 fraud data:

- Rows: {stats["rows"]:,}
- Fraud cases: {stats["fraud_cases"]:,}
- Fraud rate: {float(stats["fraud_rate"]) * 100:.4f}%
- Fraud amount: {float(stats["fraud_amount"]):,.2f} cost units
- Duplicate transaction IDs: {stats["duplicate_transaction_id"]:,}

## Important Boundary

Layer A observed PCA data is used for predictive fraud benchmark only. Layer B synthetic data is used for interpretable controls testing only. These claims must not be mixed.

## Next Phase

Phase 1 may build the observed benchmark: EDA, train/validation/test split, logistic baseline, tree/tree-based challenger, anomaly benchmark, PR-AUC, recall/precision and fraud amount capture.
""",
    )
    write_text(
        "business_question.md",
        """
# Business Question

How can transaction-level risk indicators, predictive models, deterministic controls and operational governance be combined to reduce fraud loss without creating unacceptable customer friction or alert workload?

Supporting questions:

1. What is the observed fraud rate and fraud amount?
2. Which model best identifies fraud under extreme imbalance?
3. How much fraud amount can be captured at different alert rates?
4. What threshold maximises net benefit under analyst-capacity constraints?
5. Which deterministic controls are needed in addition to the model?
6. Which transactions require allow, step-up, hold, review or decline?
7. How should alerts be prioritised?
8. How much investigation capacity is required?
9. What causes false positives?
10. Which fraud controls can fail operationally?
11. What KRIs should be monitored?
12. What should management do when fraud loss or backlog breaches appetite?
""",
    )
    write_text(
        "recruiter_summary.md",
        """
# Recruiter Summary

Project 5 is a fraud-risk and operational-risk portfolio project. It combines an observed PCA fraud benchmark with a separately labelled synthetic controls-testing environment.

The observed layer will prove modelling discipline under extreme class imbalance using PR-AUC, fraud amount capture, calibration and threshold economics.

The synthetic layer will prove practical risk-system thinking: deterministic rules, reason codes, alert queues, investigation capacity, incidents, KRI monitoring, UAT/SIT and governance.

The value to an employer is not just "I can train a fraud model." The value is: I can translate model output and fraud indicators into controlled business decisions, test evidence, operational workload, risk appetite and management action.
""",
    )
    write_text(
        "limitation_note.md",
        """
# Limitation Note

This project is educational and portfolio-oriented.

Limitations:

- It is not a production fraud platform.
- It is not a live payment switch.
- It is not an AML system.
- It is not a cyber-security product.
- It is not a regulatory operational-risk capital model.
- Observed PCA variables do not support business reason codes.
- Synthetic controls-testing outputs do not prove observed fraud performance.
- Cost-unit assumptions are illustrative and must not be presented as market benchmarks.
- The current Project 0 observed fraud raw copy does not expose original `Time`; Project 5 uses `monitoring_period` as a disclosed proxy.
""",
    )
    write_text(
        "change_log.md",
        f"""
# Change Log

| Version | Date | Change | Owner |
|---|---|---|---|
| v0.1-phase0 | {RUN_TS[:10]} | Created Project 5 folder, Phase 0 methodology locks, input contracts and validation gate | Risk Analytics |
""",
    )
    write_text(
        "requirements.txt",
        """
pandas
numpy
scikit-learn
openpyxl
matplotlib
""",
    )
    write_text(
        "data_contract/source_manifest.md",
        f"""
# Source Manifest

| Source | Path | Used as | Claim boundary |
|---|---|---|---|
| Project 0 raw observed fraud | Project 0 canonical source | Lineage reference | Public observed PCA benchmark source; current copy has no Time field |
| Project 0 silver observed fraud | Project 0 canonical silver fraud source | Primary Project 5 observed input | Observed predictive benchmark only |
| Project 0 gold fraud KRI | Project 0 canonical gold KRI source | Reference KRI aggregation | Monitoring reference only |

Project-local observed input:

`data/observed/fraud_pca_input.csv.gz`

Project-local sample:

`data/observed/fraud_pca_sample.csv`
""",
    )

    population_rows = [
        {
            "population": "Layer A observed PCA benchmark",
            "rows": stats["rows"],
            "fraud_cases": stats["fraud_cases"],
            "fraud_rate": f"{float(stats['fraud_rate']):.8f}",
            "amount": f"{float(stats['transaction_amount']):.2f}",
            "fraud_amount": f"{float(stats['fraud_amount']):.2f}",
            "data_status": "Observed",
            "source_type": "Project 0 silver fraud data",
            "claim_boundary": "Observed predictive benchmark only",
        },
        {
            "population": "Layer B synthetic controls testing",
            "rows": "Not generated in Phase 0",
            "fraud_cases": "Not generated in Phase 0",
            "fraud_rate": "Not generated in Phase 0",
            "amount": "Not generated in Phase 0",
            "fraud_amount": "Not generated in Phase 0",
            "data_status": "Synthetic",
            "source_type": "Future synthetic generator",
            "claim_boundary": "Controls testing only",
        },
    ]
    write_csv(
        "data_contract/population_reconciliation.csv",
        population_rows,
        list(population_rows[0].keys()),
    )

    checks = validation_rows(stats)
    validation_fields = list(checks[0].keys())
    write_csv("validation/phase0_validation_gate.csv", checks, validation_fields)
    write_csv("validation/validation_checks.csv", checks, validation_fields)
    unresolved_fail = [r for r in checks if r["status"] == "FAIL" and r["severity"] == "Critical"]
    write_text(
        "validation/phase0_validation_report.md",
        f"""
# Phase 0 Validation Report

Generated: {RUN_TS}

## Result

{"PASS" if not unresolved_fail else "FAIL"}

Critical FAIL count: {len(unresolved_fail)}

## Senior Risk Conclusion

Phase 0 is locked. The project may proceed to Phase 1 observed benchmark only if no new data, label, threshold, calibration, friendly-fraud or fairness design change is introduced without change control.

The key governance control is claim separation:

- observed PCA data supports predictive benchmark claims;
- synthetic data supports controls-testing and operational governance claims.

No model training has been performed in Phase 0.
""",
    )
    write_text("validation/validation_report.md", (PROJECT_ROOT / "validation" / "phase0_validation_report.md").read_text(encoding="utf-8"))
    write_text(
        "logs/project5_pipeline.log",
        f"[{RUN_TS}] Phase 0 artifacts generated. Observed rows={stats['rows']}, fraud_cases={stats['fraud_cases']}, validation={'PASS' if not unresolved_fail else 'FAIL'}.\n",
    )

    print("Project 5 Phase 0 generated")
    print(f"Observed rows: {stats['rows']:,}")
    print(f"Fraud cases: {stats['fraud_cases']:,}")
    print(f"Fraud rate: {float(stats['fraud_rate']) * 100:.4f}%")
    print(f"Validation: {'PASS' if not unresolved_fail else 'FAIL'}")


if __name__ == "__main__":
    main()
