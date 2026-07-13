from __future__ import annotations

import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


ROOT = Path(__file__).resolve().parents[1]
SEED = 20260711
DISCLAIMER = (
    "This project is an educational fraud and operational-risk framework. "
    "It combines an observed PCA-transformed fraud benchmark with a separately "
    "labelled synthetic controls-testing environment. It is not a production "
    "fraud platform, live payment control, AML system or regulatory model."
)


def ensure_directories() -> None:
    for name in (
        "data_contract",
        "data/observed",
        "data/synthetic",
        "data/synthetic/internal",
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
        "reports/assets",
        "excel",
        "scripts",
        "logs",
    ):
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    ensure_directories()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(ROOT / "logs/project5_pipeline.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        logger.addHandler(handler)
    return logger


def metadata(layer: str, status: str, source: str, boundary: str) -> dict[str, str]:
    return {
        "data_layer": layer,
        "data_status": status,
        "source_type": source,
        "claim_boundary": boundary,
    }


def add_metadata(
    frame: pd.DataFrame,
    layer: str,
    status: str,
    source: str,
    boundary: str,
) -> pd.DataFrame:
    result = frame.copy()
    for key, value in metadata(layer, status, source, boundary).items():
        result[key] = value
    return result


def write_csv(frame: pd.DataFrame, relative_path: str, **kwargs) -> Path:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, **kwargs)
    return path


def write_markdown(relative_path: str, title: str, body: str, disclaimer: bool = True) -> Path:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"# {title}\n\n"
    if disclaimer:
        text += f"> {DISCLAIMER}\n\n"
    text += body.rstrip() + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def file_sha256(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def sigmoid(values: np.ndarray | pd.Series) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    values = np.clip(values, -35, 35)
    return 1.0 / (1.0 + np.exp(-values))


def logit(values: np.ndarray | pd.Series) -> np.ndarray:
    values = np.clip(np.asarray(values, dtype=float), 1e-7, 1 - 1e-7)
    return np.log(values / (1 - values))


def observed_split(period: pd.Series) -> pd.Series:
    return pd.Series(
        np.select(
            [period <= 17, period <= 23],
            ["train", "validation"],
            default="test",
        ),
        index=period.index,
    )


def binary_metrics(
    y_true: Iterable[int],
    score: Iterable[float],
    threshold: float,
    amount: Iterable[float] | None = None,
) -> dict[str, float]:
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(score, dtype=float)
    pred = (s >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    amount_array = np.ones(len(y), dtype=float) if amount is None else np.asarray(amount, dtype=float)
    fraud_amount = float(amount_array[y == 1].sum())
    captured_amount = float(amount_array[(y == 1) & (pred == 1)].sum())
    return {
        "rows": int(len(y)),
        "fraud_count": int(y.sum()),
        "fraud_rate": float(y.mean()),
        "pr_auc": float(average_precision_score(y, s)),
        "roc_auc": float(roc_auc_score(y, s)),
        "threshold": float(threshold),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "alert_rate": float(pred.mean()),
        "alerts_per_1000": float(pred.mean() * 1000),
        "false_positive_rate": safe_div(fp, fp + tn),
        "fraud_amount_recall": safe_div(captured_amount, fraud_amount),
        "fraud_amount_captured": captured_amount,
        "true_positive": int(tp),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_negative": int(tn),
        "brier_score": float(brier_score_loss(y, np.clip(s, 0, 1))),
    }


def threshold_for_alert_rate(score: Iterable[float], alert_rate: float) -> float:
    values = np.asarray(score, dtype=float)
    return float(np.quantile(values, 1 - alert_rate))


def psi(expected: Iterable[float], actual: Iterable[float], bins: int = 10) -> float:
    expected_values = np.asarray(expected, dtype=float)
    actual_values = np.asarray(actual, dtype=float)
    edges = np.unique(np.quantile(expected_values, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf
    expected_hist = np.histogram(expected_values, bins=edges)[0] / len(expected_values)
    actual_hist = np.histogram(actual_values, bins=edges)[0] / len(actual_values)
    expected_hist = np.clip(expected_hist, 1e-6, None)
    actual_hist = np.clip(actual_hist, 1e-6, None)
    return float(np.sum((actual_hist - expected_hist) * np.log(actual_hist / expected_hist)))


def dataframe_to_markdown(frame: pd.DataFrame, decimals: int = 4) -> str:
    printable = frame.copy()
    for column in printable.select_dtypes(include=["number"]).columns:
        printable[column] = printable[column].map(
            lambda value: "" if pd.isna(value) else f"{value:.{decimals}f}"
        )
    headers = [str(column) for column in printable.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in printable.astype(str).itertuples(index=False, name=None):
        lines.append("| " + " | ".join(value.replace("|", "/") for value in row) + " |")
    return "\n".join(lines)


def json_dump(relative_path: str, payload: dict) -> Path:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def decision_for_record(record: dict) -> tuple[str, str]:
    """Reference decision function shared by engine and executable UAT tests."""
    score = record.get("synthetic_model_score")
    amount = record.get("amount")
    transaction_id = record.get("transaction_id")
    customer_id = record.get("customer_id")
    device_id = record.get("device_id")
    beneficiary_id = record.get("beneficiary_id")
    timestamp = record.get("transaction_time")
    if (
        transaction_id in (None, "")
        or customer_id in (None, "")
        or device_id in (None, "")
        or beneficiary_id in (None, "")
        or timestamp in (None, "")
    ):
        return "DATA_EXCEPTION", "RC_MISSING_DATA"
    try:
        pd.to_datetime(timestamp, errors="raise")
    except (ValueError, TypeError):
        return "DATA_EXCEPTION", "RC_MISSING_DATA"
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return "DATA_EXCEPTION", "RC_MISSING_SCORE"
    if not 0 <= float(score) <= 1:
        return "DATA_EXCEPTION", "RC_INVALID_SCORE"
    if amount is None or float(amount) < 0:
        return "DATA_EXCEPTION", "RC_INVALID_AMOUNT"
    if int(record.get("blacklist_hit", 0)) == 1:
        return "BLOCK_ACCOUNT", "RC_BLACKLIST"
    if int(record.get("privileged_override_flag", 0)) == 1 and float(amount) >= 2000:
        return "BLOCK_ACCOUNT", "RC_OVERRIDE_MISUSE"
    if int(record.get("duplicate_transaction_flag", 0)) == 1:
        return "HOLD", "RC_DUPLICATE_TXN"
    if int(record.get("account_takeover_signal", 0)) == 1 and int(record.get("failed_otp_count", 0)) >= 5:
        return "HOLD", "RC_ATO_CRITICAL"
    critical_hits = int(record.get("critical_rule_hits", 0))
    high_hits = int(record.get("high_rule_hits", 0))
    anomaly = float(record.get("synthetic_anomaly_score", 0.0))
    step_up_threshold = float(record.get("model_step_up_threshold", 0.030594))
    review_threshold = float(record.get("model_review_threshold", 0.119124))
    decline_threshold = float(record.get("model_decline_threshold", 0.135282))
    anomaly_threshold = float(record.get("anomaly_review_threshold", 0.995206))
    quality_rule_overlay = int(record.get("quality_rule_overlay", 0))
    if critical_hits >= 1:
        return "HOLD", "RC_CRITICAL_RULE"
    if float(score) >= decline_threshold and float(amount) >= 1000:
        return "DECLINE", "RC_MODEL_HIGH_AMOUNT"
    if float(score) >= review_threshold:
        return "MANUAL_REVIEW", "RC_MODEL_HIGH"
    if quality_rule_overlay == 1 and float(score) >= 0.05:
        return "MANUAL_REVIEW", "RC_COMBINED_RISK"
    if high_hits >= 2 and float(score) >= step_up_threshold:
        return "MANUAL_REVIEW", "RC_COMBINED_RISK"
    if anomaly >= anomaly_threshold:
        return "MANUAL_REVIEW", "RC_ANOMALY_HIGH"
    if high_hits >= 1 or float(score) >= step_up_threshold:
        return "STEP_UP", "RC_STEP_UP_RISK"
    return "ALLOW", "RC_LOW_RISK"
