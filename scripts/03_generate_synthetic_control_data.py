from __future__ import annotations

import numpy as np
import pandas as pd

from _project5_common import (
    ROOT,
    SEED,
    add_metadata,
    get_logger,
    sigmoid,
    write_csv,
    write_markdown,
)


CUSTOMER_COUNT = 50_000
DEVICE_COUNT = 65_000
BENEFICIARY_COUNT = 90_000
TRANSACTION_COUNT = 250_000
DAY_COUNT = 30


def main() -> None:
    log = get_logger("phase3.synthetic_entities")
    rng = np.random.default_rng(SEED)

    countries = np.array(["VN", "SG", "TH", "MY", "ID", "PH"])
    country_probability = np.array([0.45, 0.13, 0.11, 0.11, 0.12, 0.08])
    segments = np.array(["Mass", "Affluent", "SME", "Digital_Native"])
    segment_probability = np.array([0.56, 0.12, 0.14, 0.18])
    channels = np.array(["MOBILE", "WEB", "CARD", "API"])
    channel_probability = np.array([0.50, 0.18, 0.27, 0.05])

    customer_id = np.array([f"C{i:07d}" for i in range(1, CUSTOMER_COUNT + 1)])
    customer_segment = rng.choice(segments, size=CUSTOMER_COUNT, p=segment_probability)
    home_country = rng.choice(countries, size=CUSTOMER_COUNT, p=country_probability)
    account_age_days = np.maximum(1, rng.gamma(3.0, 330.0, size=CUSTOMER_COUNT).astype(int))
    usual_amount = np.exp(rng.normal(4.3, 0.85, size=CUSTOMER_COUNT)).clip(5, 5000)
    usual_hour = np.clip(rng.normal(14, 4.2, size=CUSTOMER_COUNT), 0, 23).astype(int)
    p3_grade = rng.choice(np.array(["A", "B", "C", "D", "E", "F_G"]), size=CUSTOMER_COUNT, p=[0.20, 0.29, 0.25, 0.15, 0.07, 0.04])
    p3_pd_map = {"A": 0.10, "B": 0.16, "C": 0.22, "D": 0.29, "E": 0.36, "F_G": 0.44}
    p3_pd_context = np.array([p3_pd_map[value] for value in p3_grade])
    vulnerability = sigmoid(
        -2.0
        + 0.75 * (account_age_days < 90)
        + 0.35 * (customer_segment == "Digital_Native")
        + 0.20 * ((p3_pd_context - p3_pd_context.mean()) / p3_pd_context.std())
        + rng.normal(0, 0.65, CUSTOMER_COUNT)
    )
    customers = pd.DataFrame(
        {
            "customer_id": customer_id,
            "account_age_days": account_age_days,
            "customer_segment": customer_segment,
            "home_country": home_country,
            "usual_channel": rng.choice(channels, size=CUSTOMER_COUNT, p=channel_probability),
            "usual_transaction_amount": usual_amount.round(2),
            "usual_transaction_hour": usual_hour,
            "historical_fraud_vulnerability": vulnerability.round(6),
            "customer_vulnerability_score": (vulnerability * 100).round(2),
            "p3_synthetic_risk_grade_context": p3_grade,
            "p3_synthetic_pd_context": p3_pd_context,
            "p3_context_noncausal_flag": 1,
        }
    )
    customers = add_metadata(
        customers,
        "Synthetic",
        "Synthetic",
        "Seeded customer generator with frozen P3 distribution context",
        "Controls testing only; P3 context is synthetic and non-causal",
    )
    write_csv(customers, "data/synthetic/synthetic_customers.csv")

    p3_context = customers[
        ["customer_id", "p3_synthetic_risk_grade_context", "p3_synthetic_pd_context", "p3_context_noncausal_flag"]
    ].copy()
    p3_context = add_metadata(
        p3_context,
        "Synthetic",
        "Proxy",
        "Frozen Project 3 grade distribution mapped to synthetic customers",
        "No observed credit-fraud causal claim",
    )
    write_csv(p3_context, "data/reference/p3_customer_risk_context.csv")
    p3_distribution = (
        p3_context.groupby("p3_synthetic_risk_grade_context", as_index=False)
        .agg(customers=("customer_id", "size"), mean_pd_context=("p3_synthetic_pd_context", "mean"))
    )
    p3_distribution["population_share"] = p3_distribution["customers"] / p3_distribution["customers"].sum()
    p3_distribution = add_metadata(
        p3_distribution,
        "Synthetic",
        "Derived",
        "Frozen P3 contextual distribution",
        "Portable regeneration reference; no observed credit-fraud relationship",
    )
    write_csv(p3_distribution, "data/reference/p3_risk_distribution.csv")

    device_id = np.array([f"D{i:07d}" for i in range(1, DEVICE_COUNT + 1)])
    device_country = rng.choice(countries, size=DEVICE_COUNT, p=country_probability)
    devices = pd.DataFrame(
        {
            "device_id": device_id,
            "device_age_days": np.maximum(0, rng.gamma(2.5, 170.0, DEVICE_COUNT).astype(int)),
            "device_trust_score": np.clip(rng.beta(6, 2, DEVICE_COUNT) * 100, 0, 100).round(2),
            "device_country": device_country,
            "device_change_count": rng.poisson(0.8, DEVICE_COUNT),
            "emulator_flag": rng.binomial(1, 0.006, DEVICE_COUNT),
            "rooted_device_flag": rng.binomial(1, 0.012, DEVICE_COUNT),
        }
    )
    devices = add_metadata(
        devices,
        "Synthetic",
        "Synthetic",
        "Seeded device generator",
        "Controls testing; not vendor device intelligence",
    )
    write_csv(devices, "data/synthetic/synthetic_devices.csv")

    beneficiary_id = np.array([f"B{i:07d}" for i in range(1, BENEFICIARY_COUNT + 1)])
    beneficiary_country = rng.choice(countries, size=BENEFICIARY_COUNT, p=country_probability)
    beneficiaries = pd.DataFrame(
        {
            "beneficiary_id": beneficiary_id,
            "beneficiary_age_hours": np.maximum(0, rng.gamma(2.4, 950.0, BENEFICIARY_COUNT).astype(int)),
            "beneficiary_risk_score": np.clip(rng.beta(1.3, 7.0, BENEFICIARY_COUNT) * 100, 0, 100).round(2),
            "new_beneficiary_flag": rng.binomial(1, 0.08, BENEFICIARY_COUNT),
            "beneficiary_country": beneficiary_country,
            "beneficiary_blacklist_flag": rng.binomial(1, 0.0008, BENEFICIARY_COUNT),
        }
    )
    beneficiaries = add_metadata(
        beneficiaries,
        "Synthetic",
        "Synthetic",
        "Seeded beneficiary generator",
        "Controls testing; blacklist is simulated",
    )
    write_csv(beneficiaries, "data/synthetic/synthetic_beneficiaries.csv")

    customer_index = rng.integers(0, CUSTOMER_COUNT, TRANSACTION_COUNT)
    device_index = rng.integers(0, DEVICE_COUNT, TRANSACTION_COUNT)
    beneficiary_index = rng.integers(0, BENEFICIARY_COUNT, TRANSACTION_COUNT)
    day = rng.integers(1, DAY_COUNT + 1, TRANSACTION_COUNT)
    hour = np.clip(
        usual_hour[customer_index] + rng.normal(0, 3.2, TRANSACTION_COUNT), 0, 23
    ).astype(int)
    minute = rng.integers(0, 60, TRANSACTION_COUNT)
    transaction_time = pd.Timestamp("2026-01-01") + pd.to_timedelta(day - 1, unit="D") + pd.to_timedelta(hour, unit="h") + pd.to_timedelta(minute, unit="m")
    base_amount = usual_amount[customer_index] * np.exp(rng.normal(0, 0.8, TRANSACTION_COUNT))
    amount = np.clip(base_amount, 0.5, 25_000)
    transaction_country = np.where(
        rng.random(TRANSACTION_COUNT) < 0.91,
        home_country[customer_index],
        rng.choice(countries, size=TRANSACTION_COUNT, p=country_probability),
    )
    transaction_channel = np.where(
        rng.random(TRANSACTION_COUNT) < 0.82,
        customers["usual_channel"].to_numpy()[customer_index],
        rng.choice(channels, size=TRANSACTION_COUNT, p=channel_probability),
    )
    merchant_category = rng.choice(
        np.array(["GROCERY", "TRAVEL", "ELECTRONICS", "GAMING", "CRYPTO", "UTILITIES", "RETAIL", "TRANSFER"]),
        TRANSACTION_COUNT,
        p=[0.18, 0.09, 0.12, 0.10, 0.025, 0.14, 0.20, 0.145],
    )

    hidden_ato = np.clip(
        0.50 * vulnerability[customer_index]
        + 0.25 * (devices["device_trust_score"].to_numpy()[device_index] < 35)
        + rng.beta(1.0, 12.0, TRANSACTION_COUNT),
        0,
        1.8,
    )
    hidden_mule = np.clip(
        0.45 * (beneficiaries["beneficiary_risk_score"].to_numpy()[beneficiary_index] / 100)
        + 0.25 * (beneficiaries["beneficiary_age_hours"].to_numpy()[beneficiary_index] < 24)
        + rng.beta(0.8, 14.0, TRANSACTION_COUNT),
        0,
        1.8,
    )
    hidden_social = np.clip(
        0.35 * vulnerability[customer_index]
        + 0.25 * (transaction_channel == "MOBILE")
        + rng.beta(0.8, 15.0, TRANSACTION_COUNT),
        0,
        1.8,
    )
    hidden_card_testing = np.clip(
        0.35 * (amount < 15)
        + 0.20 * (transaction_channel == "CARD")
        + rng.beta(0.7, 18.0, TRANSACTION_COUNT),
        0,
        1.6,
    )
    hidden_merchant = np.clip(
        0.35 * np.isin(merchant_category, ["CRYPTO", "GAMING", "ELECTRONICS"])
        + rng.beta(0.7, 16.0, TRANSACTION_COUNT),
        0,
        1.6,
    )
    hidden_internal = np.clip(rng.beta(0.35, 45.0, TRANSACTION_COUNT) + 0.12 * (transaction_channel == "API"), 0, 1.4)

    latent = pd.DataFrame(
        {
            "transaction_id": [f"T{i:09d}" for i in range(1, TRANSACTION_COUNT + 1)],
            "transaction_time": transaction_time,
            "customer_id": customer_id[customer_index],
            "device_id": device_id[device_index],
            "beneficiary_id": beneficiary_id[beneficiary_index],
            "amount": amount.round(2),
            "channel": transaction_channel,
            "merchant_category": merchant_category,
            "country": transaction_country,
            "home_country": home_country[customer_index],
            "account_age_days": account_age_days[customer_index],
            "customer_segment": customer_segment[customer_index],
            "customer_vulnerability_score": (vulnerability[customer_index] * 100).round(2),
            "usual_transaction_amount": usual_amount[customer_index].round(2),
            "usual_transaction_hour": usual_hour[customer_index],
            "p3_synthetic_risk_grade_context": p3_grade[customer_index],
            "p3_synthetic_pd_context": p3_pd_context[customer_index],
            "device_age_days": devices["device_age_days"].to_numpy()[device_index],
            "device_trust_score": devices["device_trust_score"].to_numpy()[device_index],
            "device_country": device_country[device_index],
            "emulator_flag": devices["emulator_flag"].to_numpy()[device_index],
            "rooted_device_flag": devices["rooted_device_flag"].to_numpy()[device_index],
            "beneficiary_age_hours": beneficiaries["beneficiary_age_hours"].to_numpy()[beneficiary_index],
            "beneficiary_risk_score": beneficiaries["beneficiary_risk_score"].to_numpy()[beneficiary_index],
            "beneficiary_country": beneficiary_country[beneficiary_index],
            "beneficiary_blacklist_flag": beneficiaries["beneficiary_blacklist_flag"].to_numpy()[beneficiary_index],
            "hidden_account_takeover_risk": hidden_ato,
            "hidden_mule_network_risk": hidden_mule,
            "hidden_social_engineering_risk": hidden_social,
            "hidden_card_testing_risk": hidden_card_testing,
            "hidden_merchant_compromise_risk": hidden_merchant,
            "hidden_internal_process_risk": hidden_internal,
            "random_label_noise": rng.normal(0, 0.75, TRANSACTION_COUNT),
        }
    )
    latent = add_metadata(
        latent,
        "Synthetic",
        "Synthetic",
        "Seeded latent fraud mechanism generator",
        "Audit-only label-generation layer; hidden fields are excluded from controls and models",
    )
    write_csv(latent, "data/synthetic/internal/synthetic_transactions_latent.csv.gz", compression="gzip")

    entity_summary = pd.DataFrame(
        [
            ["customers", CUSTOMER_COUNT],
            ["devices", DEVICE_COUNT],
            ["beneficiaries", BENEFICIARY_COUNT],
            ["transactions", TRANSACTION_COUNT],
            ["operational_days", DAY_COUNT],
        ],
        columns=["entity", "row_count"],
    )
    entity_summary = add_metadata(
        entity_summary,
        "Synthetic",
        "Derived",
        "Synthetic entity generator",
        "Controls-testing population only",
    )
    write_csv(entity_summary, "data_contract/synthetic_population_reconciliation.csv")

    write_markdown(
        "reports/synthetic_entity_generation_report.md",
        "Synthetic Entity Generation Report",
        f"""Generated **{CUSTOMER_COUNT:,} customers**, **{DEVICE_COUNT:,} devices**, **{BENEFICIARY_COUNT:,} beneficiaries** and **{TRANSACTION_COUNT:,} latent transaction rows** across **{DAY_COUNT} simulated days** using seed `{SEED}`.

Hidden fraud mechanisms are retained only in the audit layer. They are excluded from observable detection models, deterministic rules and investigator reason codes. Project 3 credit-risk context is mapped at low weight to synthetic customer vulnerability and is explicitly non-causal. The next phase converts latent risks into noisy observable symptoms and stochastic labels.""",
    )
    log.info("Synthetic entities generated: transactions=%s", TRANSACTION_COUNT)
    print(f"Synthetic entities PASS | transactions={TRANSACTION_COUNT:,}")


if __name__ == "__main__":
    main()
