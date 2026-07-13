from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT.parent / "_final_deliverables"
FULL_NAME = "Project5_FraudOperationalRisk_Gold_v1_0_1_PUBLIC_REMEDIATED_FINAL.zip"
LIGHT_NAME = "Project5_FraudOperationalRisk_Gold_v1_0_1_PUBLIC_REMEDIATED_AI_REVIEW_LIGHT.zip"


def project_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix.lower() != ".pyc"
    )


def light_eligible(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    if relative.startswith("data/review_samples/"):
        return True
    if relative in {
        "data/observed/fraud_pca_sample.csv",
        "data/synthetic/synthetic_transactions_sample.csv",
        "excel/Project5_FraudOperationalRisk_Model.xlsx",
    }:
        return True
    excluded_prefixes = (
        "data/synthetic/internal/",
        "data/observed/fraud_pca_input.csv.gz",
        "data/observed/observed_split_index.csv.gz",
        "data/synthetic/synthetic_transactions.csv.gz",
        "data/synthetic/synthetic_customers.csv",
        "data/synthetic/synthetic_devices.csv",
        "data/synthetic/synthetic_beneficiaries.csv",
        "data/synthetic/synthetic_disputes.csv",
        "data/reference/p3_customer_risk_context.csv",
        "outputs/observed_model_predictions.csv.gz",
        "outputs/synthetic_transaction_scores.csv.gz",
        "outputs/synthetic_rule_hits.csv.gz",
        "outputs/hybrid_decision_output.csv.gz",
        "outputs/alert_queue.csv.gz",
        "models/observed_champion_model.joblib",
        "models/observed_champion_platt_calibrator.joblib",
        "models/observed_anomaly_model.joblib",
        "models/synthetic_controls_model.joblib",
        "models/synthetic_controls_platt_calibrator.joblib",
        "models/synthetic_controls_anomaly.joblib",
    )
    return not relative.startswith(excluded_prefixes)


def write_zip(destination: Path, files: list[Path]) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            arcname = (Path(ROOT.name) / path.relative_to(ROOT)).as_posix()
            archive.write(path, arcname)


def main() -> None:
    DELIVERABLES.mkdir(parents=True, exist_ok=True)
    files = project_files()
    full = DELIVERABLES / FULL_NAME
    light = DELIVERABLES / LIGHT_NAME
    write_zip(full, files)
    write_zip(light, [path for path in files if light_eligible(path)])
    print(f"FULL: {full} ({full.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"LIGHT: {light} ({light.stat().st_size / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
