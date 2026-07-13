from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "01_load_validate_observed_data.py",
    "02_build_observed_fraud_benchmark.py",
    "03_generate_synthetic_control_data.py",
    "04_build_synthetic_features_and_labels.py",
    "05_build_fraud_rules.py",
    "06_build_hybrid_decision_engine.py",
    "07_build_alert_operations.py",
    "08_build_operational_risk_outputs.py",
    "09_generate_excel_and_reports.py",
    "10_validate_final_outputs.py",
]


def main() -> None:
    for script in SCRIPTS:
        print(f"\n[Project 5] Running {script}", flush=True)
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)
    print("\nProject 5 full pipeline PASS", flush=True)


if __name__ == "__main__":
    main()
