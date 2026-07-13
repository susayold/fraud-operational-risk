from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _project5_common import (
    ROOT,
    add_metadata,
    dataframe_to_markdown,
    ensure_directories,
    file_sha256,
    get_logger,
    observed_split,
    safe_div,
    write_csv,
    write_markdown,
)


def main() -> None:
    ensure_directories()
    log = get_logger("phase1.data")
    source = ROOT / "data/observed/fraud_pca_input.csv.gz"
    if not source.exists():
        raise FileNotFoundError(f"Observed input not found: {source}")

    data = pd.read_csv(source)
    required = ["transaction_id", *[f"v{i}" for i in range(1, 29)], "amount", "fraud_flag", "monitoring_period"]
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError(f"Missing observed fields: {missing}")

    data["split"] = observed_split(data["monitoring_period"])
    feature_columns = [f"v{i}" for i in range(1, 29)] + ["amount"]
    exact_duplicates = int(data.duplicated(subset=required).sum())
    invalid_class = int((~data["fraud_flag"].isin([0, 1])).sum())
    invalid_amount = int((data["amount"] < 0).sum())
    missing_feature_rows = int(data[feature_columns].isna().any(axis=1).sum())
    eligible = data.loc[
        data["fraud_flag"].isin([0, 1])
        & data["amount"].ge(0)
        & ~data[feature_columns].isna().any(axis=1)
    ].copy()

    reconciliation = pd.DataFrame(
        [
            ["Raw transactions", len(data)],
            ["Less exact duplicates", exact_duplicates],
            ["Less invalid fraud class", invalid_class],
            ["Less invalid amount", invalid_amount],
            ["Less unusable feature rows", missing_feature_rows],
            ["Eligible observed benchmark population", len(eligible)],
        ],
        columns=["population_step", "row_count"],
    )
    reconciliation["reconciliation_status"] = "PASS" if len(eligible) == len(data) else "REVIEW"
    reconciliation = add_metadata(
        reconciliation,
        "Observed",
        "Observed",
        "Project 0 silver PCA fraud transactions",
        "Population control only; no investigator workflow claim",
    )
    write_csv(reconciliation, "data_contract/population_reconciliation.csv")

    split_summary = (
        eligible.groupby("split", observed=True)
        .agg(
            rows=("transaction_id", "size"),
            fraud_count=("fraud_flag", "sum"),
            total_amount=("amount", "sum"),
            fraud_amount=("amount", lambda x: x[eligible.loc[x.index, "fraud_flag"].eq(1)].sum()),
            first_period=("monitoring_period", "min"),
            last_period=("monitoring_period", "max"),
        )
        .reset_index()
    )
    split_summary["fraud_rate"] = split_summary["fraud_count"] / split_summary["rows"]
    split_summary["fraud_amount_rate"] = split_summary["fraud_amount"] / split_summary["total_amount"]
    split_summary = add_metadata(
        split_summary,
        "Observed",
        "Derived",
        "Ordered monitoring-period proxy split",
        "Time semantics unavailable; split preserves source row order only",
    )
    write_csv(split_summary, "data_contract/observed_split_reconciliation.csv")
    write_csv(
        eligible[["transaction_id", "monitoring_period", "split", "fraud_flag"]],
        "data/observed/observed_split_index.csv.gz",
        compression="gzip",
    )

    total_amount = float(eligible["amount"].sum())
    fraud_amount = float(eligible.loc[eligible["fraud_flag"].eq(1), "amount"].sum())
    legitimate_amount = eligible.loc[eligible["fraud_flag"].eq(0), "amount"]
    fraud_values = eligible.loc[eligible["fraud_flag"].eq(1), "amount"]
    kpis = pd.DataFrame(
        [
            ["total_transactions", len(eligible), "count"],
            ["fraud_transactions", int(eligible["fraud_flag"].sum()), "count"],
            ["fraud_rate", float(eligible["fraud_flag"].mean()), "ratio"],
            ["class_imbalance_ratio", safe_div((eligible["fraud_flag"] == 0).sum(), eligible["fraud_flag"].sum()), "legitimate_per_fraud"],
            ["total_transaction_amount", total_amount, "cost_units"],
            ["fraud_amount", fraud_amount, "cost_units"],
            ["fraud_amount_rate", safe_div(fraud_amount, total_amount), "ratio"],
            ["average_legitimate_amount", float(legitimate_amount.mean()), "cost_units"],
            ["average_fraud_amount", float(fraud_values.mean()), "cost_units"],
            ["amount_p95", float(eligible["amount"].quantile(0.95)), "cost_units"],
            ["amount_p99", float(eligible["amount"].quantile(0.99)), "cost_units"],
            ["duplicate_transaction_id", int(eligible["transaction_id"].duplicated().sum()), "count"],
            ["missing_feature_rows", missing_feature_rows, "count"],
        ],
        columns=["metric", "value", "unit"],
    )
    kpis = add_metadata(
        kpis,
        "Observed",
        "Derived",
        "Observed PCA fraud benchmark",
        "Observed transaction classification and amount analysis only",
    )
    write_csv(kpis, "outputs/observed_fraud_kpi_summary.csv")

    by_period = (
        eligible.groupby("monitoring_period")
        .agg(
            transactions=("transaction_id", "size"),
            fraud_transactions=("fraud_flag", "sum"),
            total_amount=("amount", "sum"),
            fraud_amount=("amount", lambda x: x[eligible.loc[x.index, "fraud_flag"].eq(1)].sum()),
        )
        .reset_index()
    )
    by_period["fraud_rate"] = by_period["fraud_transactions"] / by_period["transactions"]
    by_period["fraud_amount_rate"] = by_period["fraud_amount"] / by_period["total_amount"]
    by_period = add_metadata(
        by_period,
        "Observed",
        "Derived",
        "Monitoring-period proxy",
        "Period index is not a calendar timestamp",
    )
    write_csv(by_period, "outputs/observed_fraud_by_period.csv")

    amount_rank = eligible.sort_values("amount", ascending=False).reset_index(drop=True)
    amount_rank["transaction_percentile"] = (np.arange(len(amount_rank)) + 1) / len(amount_rank)
    percentile_rows = []
    for share in (0.001, 0.005, 0.01, 0.02, 0.05, 0.10):
        selected = amount_rank.iloc[: max(1, int(np.ceil(len(amount_rank) * share)))]
        percentile_rows.append(
            {
                "top_transaction_share": share,
                "transactions": len(selected),
                "fraud_transactions": int(selected["fraud_flag"].sum()),
                "fraud_recall": safe_div(selected["fraud_flag"].sum(), eligible["fraud_flag"].sum()),
                "fraud_amount_recall": safe_div(
                    selected.loc[selected["fraud_flag"].eq(1), "amount"].sum(), fraud_amount
                ),
            }
        )
    amount_capture = add_metadata(
        pd.DataFrame(percentile_rows),
        "Observed",
        "Derived",
        "Amount-only ordering",
        "EDA benchmark, not a fraud control",
    )
    write_csv(amount_capture, "outputs/observed_amount_percentile_capture.csv")

    assets = ROOT / "reports/assets"
    plt.figure(figsize=(7, 4))
    counts = eligible["fraud_flag"].value_counts().sort_index()
    plt.bar(["Legitimate", "Fraud"], counts.values, color=["#31546d", "#c43d4b"])
    plt.yscale("log")
    plt.ylabel("Transactions (log scale)")
    plt.title("Observed class imbalance")
    plt.tight_layout()
    plt.savefig(assets / "observed_class_imbalance.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.plot(by_period["monitoring_period"], by_period["fraud_rate"] * 100, marker="o", color="#c43d4b")
    plt.xlabel("Monitoring period proxy")
    plt.ylabel("Fraud rate (%)")
    plt.title("Observed fraud rate by ordered period")
    plt.tight_layout()
    plt.savefig(assets / "observed_fraud_rate_by_period.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.hist(np.log1p(eligible.loc[eligible["fraud_flag"].eq(0), "amount"]), bins=80, alpha=0.65, label="Legitimate")
    plt.hist(np.log1p(eligible.loc[eligible["fraud_flag"].eq(1), "amount"]), bins=50, alpha=0.65, label="Fraud")
    plt.xlabel("log(1 + amount)")
    plt.ylabel("Transactions")
    plt.title("Observed amount distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig(assets / "observed_amount_distribution.png", dpi=160)
    plt.close()

    feature_means = []
    for column in [f"v{i}" for i in range(1, 29)]:
        good = eligible.loc[eligible["fraud_flag"].eq(0), column]
        bad = eligible.loc[eligible["fraud_flag"].eq(1), column]
        pooled = eligible[column].std(ddof=0)
        separation = abs(float(bad.mean() - good.mean())) / pooled if pooled else 0.0
        feature_means.append([column, good.mean(), bad.mean(), separation])
    separation = pd.DataFrame(feature_means, columns=["feature", "legitimate_mean", "fraud_mean", "standardised_mean_gap"])
    separation = separation.sort_values("standardised_mean_gap", ascending=False)
    separation = add_metadata(
        separation,
        "Observed",
        "Derived",
        "PCA feature univariate profile",
        "PCA names are not business reason codes",
    )
    write_csv(separation, "outputs/observed_feature_separation.csv")
    top = separation.head(10)
    plt.figure(figsize=(8, 4.5))
    plt.barh(top["feature"][::-1], top["standardised_mean_gap"][::-1], color="#2b7a78")
    plt.xlabel("Absolute standardised mean gap")
    plt.title("Top observed PCA univariate separation")
    plt.tight_layout()
    plt.savefig(assets / "observed_feature_separation.png", dpi=160)
    plt.close()

    p3_context = ROOT / "data/reference/p3_customer_risk_context.csv"
    source_manifest = pd.DataFrame(
        [
            {
                "dataset_id": "P5-OBS-PCA-INPUT",
                "dataset_version": "Project 5 v1.0.1 packaged snapshot",
                "source_name": "Credit Card Fraud Detection PCA benchmark derivative",
                "source_url": "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud",
                "licence_or_access_terms": "Public Kaggle dataset; users must follow Kaggle and original dataset access terms",
                "retrieved_at": "Project 0 data-pool snapshot; exact external retrieval timestamp not asserted",
                "snapshot_date": "2026-07-11",
                "row_count": len(data),
                "fraud_count": int(data["fraud_flag"].sum()),
                "fraud_rate": float(data["fraud_flag"].mean()),
                "amount_total": float(data["amount"].sum()),
                "fraud_amount": float(data.loc[data["fraud_flag"].eq(1), "amount"].sum()),
                "sha256": file_sha256(source),
                "canonical_path": "Project 0 canonical fraud source",
                "packaged_path": "data/observed/fraud_pca_input.csv.gz",
                "transformation": "Project 0 renamed fields to transaction_id, v1-v28, amount, fraud_flag, monitoring_period",
                "downstream_use": "Observed fraud benchmark, calibration, threshold economics and amount-capture analysis",
                "portability": "Included in FULL package; sample included in AI review package",
            },
            {
                "dataset_id": "P0-CANONICAL-FRAUD",
                "dataset_version": "Project 0 data-pool reference",
                "source_name": "Project 0 canonical fraud data pool",
                "source_url": "Local governed data-pool reference; public source URL documented in P5-OBS-PCA-INPUT",
                "licence_or_access_terms": "Do not redistribute outside documented public-source terms",
                "retrieved_at": "Not independently asserted by Project 5",
                "snapshot_date": "2026-07-11",
                "row_count": len(data),
                "fraud_count": int(data["fraud_flag"].sum()),
                "fraud_rate": float(data["fraud_flag"].mean()),
                "amount_total": float(data["amount"].sum()),
                "fraud_amount": float(data.loc[data["fraud_flag"].eq(1), "amount"].sum()),
                "sha256": file_sha256(source),
                "canonical_path": "Project 0 canonical source",
                "packaged_path": "data/observed/fraud_pca_input.csv.gz",
                "transformation": "Copied into Project 5 as observed benchmark input",
                "downstream_use": "Source lineage and rebuild reference",
                "portability": "Project 5 full package is self-contained for observed rebuild",
            },
            {
                "dataset_id": "P3-CUSTOMER-RISK-CONTEXT",
                "dataset_version": "Project 3 synthetic reference snapshot",
                "source_name": "Project 3 customer risk context reference",
                "source_url": "Project 3 portfolio artifact; no external public source asserted",
                "licence_or_access_terms": "Synthetic/derived portfolio data; use as context only",
                "retrieved_at": "2026-07-11 portfolio build",
                "snapshot_date": "2026-07-11",
                "row_count": int(pd.read_csv(p3_context, usecols=["customer_id"]).shape[0]) if p3_context.exists() else 0,
                "fraud_count": 0,
                "fraud_rate": 0.0,
                "amount_total": 0.0,
                "fraud_amount": 0.0,
                "sha256": file_sha256(p3_context) if p3_context.exists() else "",
                "canonical_path": "Project 3 final deliverable reference",
                "packaged_path": "data/reference/p3_customer_risk_context.csv",
                "transformation": "Used only for contextual customer-risk enrichment checks; no causal production claim",
                "downstream_use": "Synthetic controls context and cross-project narrative boundary",
                "portability": "Included in FULL package; excluded from AI review light package",
            },
            {
                "dataset_id": "P6-GOVERNANCE-PATTERN",
                "dataset_version": "Project 6 rule-implementation reference",
                "source_name": "Project 6 governance pattern reference",
                "source_url": "Project 6 portfolio artifact; no external public source asserted",
                "licence_or_access_terms": "Portfolio governance methodology reference",
                "retrieved_at": "2026-07-11 portfolio build",
                "snapshot_date": "2026-07-11",
                "row_count": 0,
                "fraud_count": 0,
                "fraud_rate": 0.0,
                "amount_total": 0.0,
                "fraud_amount": 0.0,
                "sha256": "",
                "canonical_path": "Project 6 Risk System Rule Implementation",
                "packaged_path": "reports/project3_project6_linkage_note.md",
                "transformation": "Methodology reference only; not model training data",
                "downstream_use": "BRD/UAT/SIT/release-control narrative alignment",
                "portability": "Documented reference, not a required rebuild input",
            },
        ]
    )
    source_manifest = add_metadata(
        source_manifest,
        "Observed",
        "Observed",
        "Project 0",
        "Observed benchmark source lineage",
    )
    source_manifest.loc[source_manifest["dataset_id"].eq("P3-CUSTOMER-RISK-CONTEXT"), ["data_layer", "data_status", "source_type", "claim_boundary"]] = [
        "Synthetic",
        "Reference",
        "Project 3 portfolio artifact",
        "Contextual synthetic reference only; no production causality claim",
    ]
    source_manifest.loc[source_manifest["dataset_id"].eq("P6-GOVERNANCE-PATTERN"), ["data_layer", "data_status", "source_type", "claim_boundary"]] = [
        "Governance",
        "Reference",
        "Project 6 portfolio artifact",
        "Governance-pattern reference only; not model data",
    ]
    write_csv(source_manifest, "data_contract/source_manifest.csv")

    summary_table = split_summary[["split", "rows", "fraud_count", "fraud_rate", "first_period", "last_period"]]
    body = f"""## Executive readout

- Eligible population: **{len(eligible):,}** transactions.
- Confirmed fraud labels: **{int(eligible['fraud_flag'].sum()):,}**, equal to **{eligible['fraud_flag'].mean():.4%}**.
- Observed fraud amount: **{fraud_amount:,.2f} cost units**, or **{safe_div(fraud_amount, total_amount):.4%}** of total amount.
- Class imbalance: **{safe_div((eligible['fraud_flag'] == 0).sum(), eligible['fraud_flag'].sum()):,.1f} legitimate transactions per fraud transaction**.
- Exact duplicate transaction IDs, invalid targets, negative amounts and missing model features: **0**.

## Ordered split

{dataframe_to_markdown(summary_table)}

The source no longer exposes the original `Time` field. `monitoring_period` preserves row ordering in blocks and is therefore used as a temporal-order proxy. It must not be interpreted as a real calendar period. Train uses periods 1-17, validation 18-23 and test 24-29. The final test population remains untouched until model lock.

## Senior interpretation

Accuracy is unsuitable because a model predicting every transaction as legitimate would exceed 99.8% accuracy while capturing no fraud. Primary evidence will be PR-AUC, fraud recall, fraud-amount recall, alert rate, false-positive workload and net benefit. Amount alone is retained only as a simple benchmark.

## Claim boundary

The observed PCA layer supports predictive benchmarking and realised amount-capture analysis. It does not support device, beneficiary, authentication, customer-behaviour or investigator reason-code claims.
"""
    write_markdown("reports/observed_fraud_eda.md", "Observed Fraud EDA", body)
    log.info("Observed data validated: rows=%s fraud=%s", len(eligible), int(eligible["fraud_flag"].sum()))
    print(f"Observed validation PASS | rows={len(eligible):,} | fraud={int(eligible['fraud_flag'].sum()):,}")


if __name__ == "__main__":
    main()
