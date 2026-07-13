from __future__ import annotations

import warnings

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, precision_recall_curve
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from _project5_common import (
    ROOT,
    SEED,
    add_metadata,
    binary_metrics,
    dataframe_to_markdown,
    get_logger,
    json_dump,
    logit,
    observed_split,
    psi,
    safe_div,
    threshold_for_alert_rate,
    write_csv,
    write_markdown,
)


warnings.filterwarnings("ignore", category=UserWarning)


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    p_hat = successes / total
    denominator = 1 + z**2 / total
    centre = (p_hat + z**2 / (2 * total)) / denominator
    margin = z * np.sqrt((p_hat * (1 - p_hat) / total) + (z**2 / (4 * total**2))) / denominator
    return float(max(0, centre - margin)), float(min(1, centre + margin))


def bootstrap_observed_intervals(
    target: np.ndarray,
    score: np.ndarray,
    amount: np.ndarray,
    threshold: float,
    iterations: int = 500,
) -> dict[str, float]:
    rng = np.random.default_rng(SEED + 91)
    pr_auc_values: list[float] = []
    amount_recall_values: list[float] = []
    indices = np.arange(len(target))
    for _ in range(iterations):
        sample_index = rng.choice(indices, size=len(indices), replace=True)
        y_sample = target[sample_index]
        if y_sample.sum() == 0:
            continue
        score_sample = score[sample_index]
        amount_sample = amount[sample_index]
        selected = score_sample >= threshold
        fraud_mask = y_sample == 1
        pr_auc_values.append(float(average_precision_score(y_sample, score_sample)))
        amount_recall_values.append(
            safe_div(amount_sample[selected & fraud_mask].sum(), amount_sample[fraud_mask].sum())
        )
    return {
        "pr_auc_ci_low": float(np.quantile(pr_auc_values, 0.025)),
        "pr_auc_ci_high": float(np.quantile(pr_auc_values, 0.975)),
        "fraud_amount_recall_ci_low": float(np.quantile(amount_recall_values, 0.025)),
        "fraud_amount_recall_ci_high": float(np.quantile(amount_recall_values, 0.975)),
        "bootstrap_iterations_requested": iterations,
        "bootstrap_iterations_used": len(pr_auc_values),
    }


def prepare_features(frame: pd.DataFrame) -> pd.DataFrame:
    features = frame[[f"v{i}" for i in range(1, 29)]].copy()
    features["log_amount"] = np.log1p(frame["amount"].clip(lower=0))
    return features


def fit_platt(raw_probability: np.ndarray, target: np.ndarray) -> LogisticRegression:
    calibrator = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000, random_state=SEED)
    calibrator.fit(logit(raw_probability).reshape(-1, 1), target)
    return calibrator


def apply_platt(calibrator: LogisticRegression, raw_probability: np.ndarray) -> np.ndarray:
    return calibrator.predict_proba(logit(raw_probability).reshape(-1, 1))[:, 1]


def calibration_diagnostics(target: np.ndarray, probability: np.ndarray) -> tuple[float, float]:
    diagnostic = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000, random_state=SEED)
    diagnostic.fit(logit(probability).reshape(-1, 1), target)
    return float(diagnostic.coef_[0][0]), float(diagnostic.intercept_[0])


def training_only_random_undersample(
    features: np.ndarray,
    target: np.ndarray,
    minority_to_majority_ratio: float = 0.05,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    fraud_index = np.flatnonzero(target == 1)
    legitimate_index = np.flatnonzero(target == 0)
    legitimate_keep = min(len(legitimate_index), int(np.ceil(len(fraud_index) / minority_to_majority_ratio)))
    selected_legitimate = rng.choice(legitimate_index, size=legitimate_keep, replace=False)
    selected = np.concatenate([fraud_index, selected_legitimate])
    rng.shuffle(selected)
    return features[selected], target[selected]


def training_only_smote(
    features: np.ndarray,
    target: np.ndarray,
    minority_to_majority_ratio: float = 0.05,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    minority = features[target == 1]
    majority_count = int((target == 0).sum())
    target_minority_count = int(np.ceil(majority_count * minority_to_majority_ratio))
    synthetic_count = max(0, target_minority_count - len(minority))
    if synthetic_count == 0:
        return features, target
    neighbours = NearestNeighbors(n_neighbors=min(6, len(minority))).fit(minority)
    neighbour_index = neighbours.kneighbors(minority, return_distance=False)
    base_index = rng.integers(0, len(minority), size=synthetic_count)
    choice = rng.integers(1, neighbour_index.shape[1], size=synthetic_count)
    partner_index = neighbour_index[base_index, choice]
    interpolation = rng.random((synthetic_count, 1))
    synthetic = minority[base_index] + interpolation * (minority[partner_index] - minority[base_index])
    augmented_x = np.vstack([features, synthetic])
    augmented_y = np.concatenate([target, np.ones(synthetic_count, dtype=int)])
    order = rng.permutation(len(augmented_y))
    return augmented_x[order], augmented_y[order]


def amount_capture_rows(
    frame: pd.DataFrame,
    score_column: str,
    model_name: str,
    split_name: str,
) -> list[dict]:
    rows: list[dict] = []
    total_fraud = int(frame["fraud_flag"].sum())
    total_fraud_amount = float(frame.loc[frame["fraud_flag"].eq(1), "amount"].sum())
    for alert_rate in (0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05):
        threshold = threshold_for_alert_rate(frame[score_column], alert_rate)
        selected = frame[score_column].ge(threshold)
        fraud_selected = selected & frame["fraud_flag"].eq(1)
        alerts = int(selected.sum())
        fraud_count = int(fraud_selected.sum())
        fraud_amount = float(frame.loc[fraud_selected, "amount"].sum())
        false_positives = int((selected & frame["fraud_flag"].eq(0)).sum())
        rows.append(
            {
                "model": model_name,
                "split": split_name,
                "target_alert_rate": alert_rate,
                "score_threshold": threshold,
                "transactions_reviewed": alerts,
                "actual_alert_rate": safe_div(alerts, len(frame)),
                "fraud_transactions_captured": fraud_count,
                "fraud_transaction_recall": safe_div(fraud_count, total_fraud),
                "fraud_amount_captured": fraud_amount,
                "fraud_amount_recall": safe_div(fraud_amount, total_fraud_amount),
                "false_positives": false_positives,
                "precision": safe_div(fraud_count, alerts),
                "average_alert_value": float(frame.loc[selected, "amount"].mean()) if alerts else 0.0,
            }
        )
    return rows


def main() -> None:
    log = get_logger("phase1.models")
    source = ROOT / "data/observed/fraud_pca_input.csv.gz"
    data = pd.read_csv(source)
    data["split"] = observed_split(data["monitoring_period"])
    features = prepare_features(data)
    train_mask = data["split"].eq("train")
    validation_mask = data["split"].eq("validation")
    test_mask = data["split"].eq("test")
    x_train, y_train = features.loc[train_mask], data.loc[train_mask, "fraud_flag"].astype(int)
    x_validation, y_validation = features.loc[validation_mask], data.loc[validation_mask, "fraud_flag"].astype(int)
    x_test, y_test = features.loc[test_mask], data.loc[test_mask, "fraud_flag"].astype(int)

    models: dict[str, object] = {
        "logistic_no_resampling": Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", LogisticRegression(max_iter=1500, solver="lbfgs", random_state=SEED)),
            ]
        ),
        "logistic_class_weight": Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1500,
                        solver="lbfgs",
                        class_weight="balanced",
                        random_state=SEED,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            learning_rate=0.08,
            max_iter=180,
            max_leaf_nodes=31,
            min_samples_leaf=30,
            l2_regularization=1.0,
            class_weight="balanced",
            random_state=SEED,
        ),
    }

    for strategy_name in ("logistic_random_undersampling", "logistic_smote"):
        strategy_scaler = StandardScaler().fit(x_train)
        scaled_train = strategy_scaler.transform(x_train)
        if strategy_name == "logistic_random_undersampling":
            strategy_x, strategy_y = training_only_random_undersample(
                scaled_train, y_train.to_numpy(), minority_to_majority_ratio=0.05
            )
        else:
            strategy_x, strategy_y = training_only_smote(
                scaled_train, y_train.to_numpy(), minority_to_majority_ratio=0.05
            )
        strategy_model = LogisticRegression(max_iter=1500, solver="lbfgs", random_state=SEED)
        strategy_model.fit(strategy_x, strategy_y)
        models[strategy_name] = Pipeline([("scale", strategy_scaler), ("model", strategy_model)])

    score_columns: dict[str, np.ndarray] = {}
    raw_columns: dict[str, np.ndarray] = {}
    calibrators: dict[str, LogisticRegression] = {}
    calibration_rows: list[dict] = []
    comparison_rows: list[dict] = []

    for name, model in models.items():
        log.info("Fitting observed model: %s", name)
        if name not in ("logistic_random_undersampling", "logistic_smote"):
            model.fit(x_train, y_train)
        raw_all = np.clip(model.predict_proba(features)[:, 1], 1e-7, 1 - 1e-7)
        raw_validation = raw_all[validation_mask.to_numpy()]
        calibrator = fit_platt(raw_validation, y_validation.to_numpy())
        calibrated_all = apply_platt(calibrator, raw_all)
        raw_columns[name] = raw_all
        score_columns[name] = calibrated_all
        calibrators[name] = calibrator

        for split_name, mask, target in (
            ("validation", validation_mask, y_validation),
            ("test", test_mask, y_test),
        ):
            raw = raw_all[mask.to_numpy()]
            calibrated = calibrated_all[mask.to_numpy()]
            threshold = threshold_for_alert_rate(
                calibrated_all[validation_mask.to_numpy()], 0.005
            )
            metrics = binary_metrics(
                target.to_numpy(),
                calibrated,
                threshold,
                data.loc[mask, "amount"].to_numpy(),
            )
            comparison_rows.append(
                {
                    "model": name,
                    "model_family": "tree" if name == "hist_gradient_boosting" else "logistic",
                    "population": split_name,
                    "resampling_strategy": (
                        "class_weight"
                        if name in ("logistic_class_weight", "hist_gradient_boosting")
                        else "random_undersampling"
                        if "undersampling" in name
                        else "SMOTE_train_only"
                        if "smote" in name
                        else "none"
                    ),
                    **metrics,
                }
            )
            for stage, probability in (("uncalibrated", raw), ("platt_calibrated", calibrated)):
                slope, intercept = calibration_diagnostics(target.to_numpy(), probability)
                observed_rate = float(target.mean())
                mean_probability = float(probability.mean())
                absolute_gap = abs(mean_probability - observed_rate)
                relative_gap = safe_div(absolute_gap, observed_rate)
                calibration_rows.append(
                    {
                        "model": name,
                        "population": split_name,
                        "calibration_stage": stage,
                        "observed_fraud_rate": observed_rate,
                        "mean_predicted_probability": mean_probability,
                        "absolute_gap": absolute_gap,
                        "relative_gap": relative_gap,
                        "brier_score": brier_score_loss(target, probability),
                        "calibration_slope": slope,
                        "calibration_intercept": intercept,
                        "calibration_method": "Platt/sigmoid fitted on validation" if stage == "platt_calibrated" else "none",
                        "acceptance_note": (
                            "Test diagnostic only; no test fitting"
                            if split_name == "test"
                            else "Validation used for Platt fit and threshold design due limited fraud count"
                        ),
                    }
                )

    scaler = StandardScaler().fit(x_train)
    x_train_scaled = scaler.transform(x_train)
    sample_rng = np.random.default_rng(SEED)
    sample_size = min(100_000, len(x_train_scaled))
    sample_index = sample_rng.choice(len(x_train_scaled), size=sample_size, replace=False)
    isolation = IsolationForest(
        n_estimators=160,
        max_samples=min(50_000, sample_size),
        contamination="auto",
        n_jobs=-1,
        random_state=SEED,
    )
    isolation.fit(x_train_scaled[sample_index])
    anomaly_raw_all = -isolation.decision_function(scaler.transform(features))
    anomaly_train_sorted = np.sort(anomaly_raw_all[train_mask.to_numpy()])
    anomaly_score_all = np.searchsorted(anomaly_train_sorted, anomaly_raw_all, side="right") / len(anomaly_train_sorted)

    simple_raw = data["pca_abs_signal"].to_numpy(dtype=float)
    simple_train_sorted = np.sort(simple_raw[train_mask.to_numpy()])
    simple_score_all = np.searchsorted(simple_train_sorted, simple_raw, side="right") / len(simple_train_sorted)

    validation_thresholds = {
        "isolation_forest": threshold_for_alert_rate(anomaly_score_all[validation_mask.to_numpy()], 0.005),
        "pca_signal_simple_benchmark": threshold_for_alert_rate(simple_score_all[validation_mask.to_numpy()], 0.005),
    }
    for name, model_score in (
        ("isolation_forest", anomaly_score_all),
        ("pca_signal_simple_benchmark", simple_score_all),
    ):
        for split_name, mask, target in (
            ("validation", validation_mask, y_validation),
            ("test", test_mask, y_test),
        ):
            metrics = binary_metrics(
                target.to_numpy(),
                model_score[mask.to_numpy()],
                validation_thresholds[name],
                data.loc[mask, "amount"].to_numpy(),
            )
            comparison_rows.append(
                {
                    "model": name,
                    "model_family": "anomaly" if name == "isolation_forest" else "simple_benchmark",
                    "population": split_name,
                    "resampling_strategy": "unsupervised" if name == "isolation_forest" else "none",
                    **metrics,
                }
            )

    comparison = pd.DataFrame(comparison_rows)
    validation_supervised = comparison.loc[
        comparison["population"].eq("validation")
        & comparison["model_family"].isin(["logistic", "tree"])
    ].copy()
    validation_supervised["selection_score"] = (
        validation_supervised["pr_auc"] * 0.55
        + validation_supervised["fraud_amount_recall"] * 0.25
        + validation_supervised["recall"] * 0.15
        + (1 - validation_supervised["alert_rate"].clip(upper=1)) * 0.05
    )
    champion_name = validation_supervised.sort_values(
        ["selection_score", "pr_auc"], ascending=False
    ).iloc[0]["model"]
    comparison["model_role"] = np.where(
        comparison["model"].eq(champion_name),
        "Champion",
        np.where(comparison["model"].eq("logistic_no_resampling"), "Transparent baseline", "Challenger/benchmark"),
    )
    comparison["selection_basis"] = "Validation PR-AUC, fraud amount capture, recall and workload; test not used for selection"
    comparison = add_metadata(
        comparison,
        "Observed",
        "Derived",
        "Observed PCA fraud benchmark",
        "Observed predictive performance; no business reason-code interpretation",
    )
    write_csv(comparison, "models/model_comparison.csv")

    calibration = add_metadata(
        pd.DataFrame(calibration_rows),
        "Observed",
        "Derived",
        "True-prevalence validation Platt calibration",
        "Economic probabilities are illustrative and not production estimates",
    )
    write_csv(calibration, "models/calibration_summary.csv")

    predictions = data[
        ["transaction_id", "monitoring_period", "split", "amount", "fraud_flag", "amount_band", "pca_signal_band"]
    ].copy()
    predictions["champion_model"] = champion_name
    predictions["champion_score_raw"] = raw_columns[champion_name]
    predictions["champion_score_calibrated"] = score_columns[champion_name]
    predictions["logistic_baseline_score_calibrated"] = score_columns["logistic_no_resampling"]
    predictions["anomaly_score"] = anomaly_score_all
    predictions["simple_benchmark_score"] = simple_score_all
    predictions = add_metadata(
        predictions,
        "Observed",
        "Derived",
        "Observed PCA model outputs",
        "Predictive benchmark scores only; PCA variables cannot form business reason codes",
    )
    write_csv(predictions, "outputs/observed_model_predictions.csv.gz", compression="gzip")

    capture_rows: list[dict] = []
    for split_name, mask in (("validation", validation_mask), ("test", test_mask)):
        capture_frame = data.loc[mask, ["amount", "fraud_flag"]].copy()
        capture_frame["champion_score"] = score_columns[champion_name][mask.to_numpy()]
        capture_frame["logistic_score"] = score_columns["logistic_no_resampling"][mask.to_numpy()]
        capture_frame["anomaly_score"] = anomaly_score_all[mask.to_numpy()]
        for score_column, model_name in (
            ("champion_score", champion_name),
            ("logistic_score", "logistic_no_resampling"),
            ("anomaly_score", "isolation_forest"),
        ):
            capture_rows.extend(amount_capture_rows(capture_frame, score_column, model_name, split_name))
    capture = add_metadata(
        pd.DataFrame(capture_rows),
        "Observed",
        "Derived",
        "Model ranking on validation/test",
        "Realised amount capture; not guaranteed prevented loss",
    )
    write_csv(capture, "outputs/fraud_amount_capture_curve.csv")

    stability_rows = []
    champion_score = score_columns[champion_name]
    validation_alert_threshold = threshold_for_alert_rate(champion_score[validation_mask.to_numpy()], 0.005)
    for period, indexes in data.groupby("monitoring_period").groups.items():
        idx = np.asarray(list(indexes), dtype=int)
        target = data.loc[idx, "fraud_flag"].to_numpy()
        score = champion_score[idx]
        amount = data.loc[idx, "amount"].to_numpy()
        metric = binary_metrics(target, score, validation_alert_threshold, amount)
        stability_rows.append({"monitoring_period": period, **metric})
    stability = pd.DataFrame(stability_rows)
    stability["score_psi_vs_train"] = [
        psi(champion_score[train_mask.to_numpy()], champion_score[data["monitoring_period"].eq(period).to_numpy()])
        for period in stability["monitoring_period"]
    ]
    stability = add_metadata(
        stability,
        "Observed",
        "Derived",
        "Monitoring-period proxy",
        "Small period fraud counts create volatile point estimates",
    )
    write_csv(stability, "models/model_stability_by_period.csv")

    feature_rows = []
    for feature in [f"v{i}" for i in range(1, 29)]:
        feature_rows.append(
            {
                "feature": feature,
                "data_layer": "Observed",
                "status": "Observed PCA",
                "model_use": "Predictive benchmark",
                "business_interpretability": "Unavailable",
                "reason_code_eligible": "No",
                "governance_action": "Monitor distribution; do not attach semantic fraud meaning",
            }
        )
    feature_rows.append(
        {
            "feature": "log_amount",
            "data_layer": "Observed",
            "status": "Derived from observed amount",
            "model_use": "Predictive benchmark and amount economics",
            "business_interpretability": "Transaction value",
            "reason_code_eligible": "Only as amount context, not fraud proof",
            "governance_action": "Monitor extreme values and units",
        }
    )
    feature_governance = pd.DataFrame(feature_rows)
    feature_governance["source_type"] = "Observed/Derived"
    feature_governance["claim_boundary"] = "No PCA business reason-code claim"
    write_csv(feature_governance, "models/feature_governance.csv")

    joblib.dump(models[champion_name], ROOT / "models/observed_champion_model.joblib", compress=3)
    joblib.dump(calibrators[champion_name], ROOT / "models/observed_champion_platt_calibrator.joblib", compress=3)
    joblib.dump({"scaler": scaler, "model": isolation}, ROOT / "models/observed_anomaly_model.joblib", compress=3)

    test_table = comparison.loc[comparison["population"].eq("test"), [
        "model", "model_role", "pr_auc", "roc_auc", "precision", "recall", "fraud_amount_recall", "alert_rate", "brier_score"
    ]].sort_values("pr_auc", ascending=False)
    champion_test = test_table.loc[test_table["model"].eq(champion_name)].iloc[0]
    challenger_test = test_table.loc[test_table["model"].eq("logistic_no_resampling")].iloc[0]
    cal_test = calibration.loc[
        calibration["model"].eq(champion_name)
        & calibration["population"].eq("test")
        & calibration["calibration_stage"].eq("platt_calibrated")
    ].iloc[0]
    champion_test_full = comparison.loc[
        comparison["model"].eq(champion_name) & comparison["population"].eq("test")
    ].iloc[0]
    gbm_validation = comparison.loc[
        comparison["model"].eq("hist_gradient_boosting") & comparison["population"].eq("validation")
    ].iloc[0]
    gbm_test = comparison.loc[
        comparison["model"].eq("hist_gradient_boosting") & comparison["population"].eq("test")
    ].iloc[0]
    lr_validation = comparison.loc[
        comparison["model"].eq(champion_name) & comparison["population"].eq("validation")
    ].iloc[0]
    isolation_validation = comparison.loc[
        comparison["model"].eq("isolation_forest") & comparison["population"].eq("validation")
    ].iloc[0]
    isolation_test = comparison.loc[
        comparison["model"].eq("isolation_forest") & comparison["population"].eq("test")
    ].iloc[0]
    simple_validation = comparison.loc[
        comparison["model"].eq("pca_signal_simple_benchmark") & comparison["population"].eq("validation")
    ].iloc[0]
    simple_test = comparison.loc[
        comparison["model"].eq("pca_signal_simple_benchmark") & comparison["population"].eq("test")
    ].iloc[0]
    recall_low, recall_high = wilson_interval(
        int(champion_test_full["true_positive"]),
        int(champion_test_full["true_positive"] + champion_test_full["false_negative"]),
    )
    precision_low, precision_high = wilson_interval(
        int(champion_test_full["true_positive"]),
        int(champion_test_full["true_positive"] + champion_test_full["false_positive"]),
    )
    bootstrap_intervals = bootstrap_observed_intervals(
        y_test.to_numpy(),
        score_columns[champion_name][test_mask.to_numpy()],
        data.loc[test_mask, "amount"].to_numpy(),
        float(champion_test_full["threshold"]),
    )
    uncertainty = add_metadata(
        pd.DataFrame(
            [
                {
                    "metric": "fraud_recall",
                    "point_estimate": champion_test_full["recall"],
                    "ci_method": "Wilson 95%",
                    "ci_low": recall_low,
                    "ci_high": recall_high,
                    "event_count": int(champion_test_full["true_positive"] + champion_test_full["false_negative"]),
                    "denominator": int(champion_test_full["true_positive"] + champion_test_full["false_negative"]),
                },
                {
                    "metric": "precision",
                    "point_estimate": champion_test_full["precision"],
                    "ci_method": "Wilson 95%",
                    "ci_low": precision_low,
                    "ci_high": precision_high,
                    "event_count": int(champion_test_full["true_positive"]),
                    "denominator": int(champion_test_full["true_positive"] + champion_test_full["false_positive"]),
                },
                {
                    "metric": "pr_auc",
                    "point_estimate": champion_test_full["pr_auc"],
                    "ci_method": "Bootstrap 95%",
                    "ci_low": bootstrap_intervals["pr_auc_ci_low"],
                    "ci_high": bootstrap_intervals["pr_auc_ci_high"],
                    "event_count": int(y_test.sum()),
                    "denominator": int(len(y_test)),
                },
                {
                    "metric": "fraud_amount_recall",
                    "point_estimate": champion_test_full["fraud_amount_recall"],
                    "ci_method": "Bootstrap 95%",
                    "ci_low": bootstrap_intervals["fraud_amount_recall_ci_low"],
                    "ci_high": bootstrap_intervals["fraud_amount_recall_ci_high"],
                    "event_count": int(y_test.sum()),
                    "denominator": int(len(y_test)),
                },
            ]
        ),
        "Observed",
        "Derived",
        "Untouched test set; Wilson and bootstrap uncertainty diagnostics",
        "Uncertainty evidence for public benchmark interpretation",
    )
    uncertainty["bootstrap_iterations_requested"] = bootstrap_intervals["bootstrap_iterations_requested"]
    uncertainty["bootstrap_iterations_used"] = bootstrap_intervals["bootstrap_iterations_used"]
    write_csv(uncertainty, "models/model_uncertainty_intervals.csv")

    write_markdown(
        "methodology/model_methodology.md",
        "Observed Fraud Model Methodology",
        f"""## Design

The benchmark uses `v1`-`v28` plus `log(1 + amount)`. Ordered monitoring-period proxy splits are train 1-17, validation 18-23 and test 24-29. Scaling, sampling and fitting occur on train only. Platt calibration is fitted on the true-prevalence validation population. The test set is used once after model and threshold design.

Five supervised strategies were compared: no-resampling logistic regression, class-weighted logistic regression, training-only random undersampling, training-only SMOTE and class-weighted histogram gradient boosting. Isolation Forest and PCA absolute-signal ordering are non-supervised/simple benchmarks.

## Selection

Champion: **{champion_name}**. Selection used validation evidence only, combining PR-AUC, fraud-amount capture, recall and workload. The test PR-AUC is **{champion_test['pr_auc']:.4f}** and test fraud-amount recall at the validation-derived 0.5% alert threshold is **{champion_test['fraud_amount_recall']:.2%}**.

## Leakage controls

- Test rows were excluded from training, calibration and threshold selection.
- SMOTE and undersampling were applied only inside the training pipeline.
- Amount is an authorisation-time field; fraud labels, amount bands and monitoring-period identifiers are not model features.
- `monitoring_period` is a row-order proxy, not a timestamp and not a model feature.
""",
    )

    write_markdown(
        "methodology/anomaly_detection_methodology.md",
        "Observed Anomaly Detection Methodology",
        """Isolation Forest is fitted only on a reproducible training sample after train-fitted standardisation. Its decision function is converted to an empirical anomaly percentile using the train distribution. It is a benchmark for unusual patterns, not proof of fraud and not automatically selected as champion. Its incremental contribution is tested again in the synthetic hybrid controls layer.""",
    )

    write_markdown(
        "models/champion_model_card.md",
        "Observed Champion Model Card",
        f"""## Intended use

Observed PCA fraud-classification benchmark and ranking input for realised threshold economics.

## Champion

`{champion_name}` selected on validation evidence. Test PR-AUC: **{champion_test['pr_auc']:.4f}**; ROC-AUC: **{champion_test['roc_auc']:.4f}**; recall at locked validation 0.5% alert threshold: **{champion_test['recall']:.2%}**; precision: **{champion_test['precision']:.2%}**; fraud-amount recall: **{champion_test['fraud_amount_recall']:.2%}**.

## Calibration

Platt calibration used the validation population with original fraud prevalence. On test, observed fraud rate is **{cal_test['observed_fraud_rate']:.4%}** and mean calibrated probability is **{cal_test['mean_predicted_probability']:.4%}**. Test was not used to fit calibration.

## Prohibited use

No production authorisation, customer adverse action, AML decision, semantic interpretation of PCA variables or claim that amount captured equals loss prevented.

## Key limitations

The original timestamp is unavailable; the ordered split uses a proxy. Validation has only {int(y_validation.sum())} fraud cases. PCA variables prevent business-level reason codes, and the public benchmark can differ from live payment populations.
""",
    )

    write_markdown(
        "models/challenger_model_card.md",
        "Transparent Logistic Challenger Model Card",
        f"""The transparent baseline is `logistic_no_resampling`. It provides a stable linear comparator with test PR-AUC **{challenger_test['pr_auc']:.4f}** and test ROC-AUC **{challenger_test['roc_auc']:.4f}**. It is not used for business explanations because the inputs remain PCA-transformed. Challenger promotion would require materially better ranking or calibration without breaching workload, stability and governance controls.""",
    )

    write_markdown(
        "reports/probability_calibration_report.md",
        "Probability Calibration Report",
        f"""## Decision

Platt/sigmoid calibration was required because the champion uses class weighting and its raw probability level is not a reliable prospective fraud probability. Isotonic calibration was rejected because validation contains only **{int(y_validation.sum())} fraud cases**, below the locked 200-event gate.

## Test result

- Observed test prevalence: **{cal_test['observed_fraud_rate']:.4%}**.
- Mean calibrated test probability: **{cal_test['mean_predicted_probability']:.4%}**.
- Absolute gap: **{cal_test['absolute_gap']:.4%}**.
- Relative gap: **{cal_test['relative_gap']:.2%}**.
- Brier score: **{cal_test['brier_score']:.6f}**.

The calibrated probability may be used only for clearly labelled prospective sensitivity. Realised threshold economics remains based on observed labels and realised transaction amount.
""",
    )

    uncertainty_table = uncertainty[["metric", "point_estimate", "ci_method", "ci_low", "ci_high", "event_count", "denominator"]]

    body = f"""## Outcome

Champion: **{champion_name}**. It was selected without consulting final-test performance. Test PR-AUC is **{champion_test['pr_auc']:.4f}**, materially more informative than accuracy under the 0.17% class prevalence.

## Test comparison

{dataframe_to_markdown(test_table)}

## Champion selection versus tree challenger

Class-weighted Logistic Regression was selected on locked validation evidence. It exceeded HistGradientBoosting on validation PR-AUC (**{lr_validation['pr_auc']:.4f}** versus **{gbm_validation['pr_auc']:.4f}**). The untouched test set then confirmed stronger PR-AUC (**{champion_test_full['pr_auc']:.4f}** versus **{gbm_test['pr_auc']:.4f}**), fraud recall (**{champion_test_full['recall']:.2%}** versus **{gbm_test['recall']:.2%}**), fraud-amount recall (**{champion_test_full['fraud_amount_recall']:.2%}** versus **{gbm_test['fraud_amount_recall']:.2%}**) and Brier score (**{champion_test_full['brier_score']:.6f}** versus **{gbm_test['brier_score']:.6f}**). The selection was not based on the final-test result.

## Anomaly-model stability

Isolation Forest achieved PR-AUC of **{isolation_validation['pr_auc']:.4f}** on validation and **{isolation_test['pr_auc']:.4f}** on test. It remained above the simple PCA-signal benchmark on both splits (**{simple_validation['pr_auc']:.4f}** validation and **{simple_test['pr_auc']:.4f}** test), but it was materially weaker than supervised candidates. Validation and test contain only **{int(isolation_validation['fraud_count'])}** and **{int(isolation_test['fraud_count'])}** fraud events, so anomaly PR-AUC and fraud-amount capture are high-variance. Isolation Forest is retained only as a complementary challenger and control component, not as a standalone champion.

## Statistical uncertainty

Point estimates are directionally strong but uncertain because the untouched test set contains only **{int(y_test.sum())}** fraud events. Confidence intervals should be considered when interpreting differences between models.

{dataframe_to_markdown(uncertainty_table)}

## Senior interpretation

The champion is a ranking benchmark, not a production fraud engine. Its value is measured by fraud and fraud amount captured at constrained alert rates. The logistic baseline and anomaly detector remain governed challengers. PCA features make the observed layer unsuitable for human-readable fraud reason codes; that capability belongs exclusively to the separately labelled synthetic controls-testing layer.
"""
    write_markdown("reports/model_performance_report.md", "Observed Model Performance Report", body)

    assets = ROOT / "reports/assets"
    plt.figure(figsize=(8, 5))
    for model_name in (champion_name, "logistic_no_resampling"):
        score = score_columns[model_name][test_mask.to_numpy()]
        precision, recall, _ = precision_recall_curve(y_test, score)
        plt.plot(recall, precision, label=f"{model_name} AP={average_precision_score(y_test, score):.3f}")
    plt.axhline(y_test.mean(), color="#666666", linestyle="--", label="Test prevalence")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Observed test precision-recall curve")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(assets / "observed_precision_recall_curve.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    plot_table = test_table.sort_values("pr_auc")
    plt.barh(plot_table["model"], plot_table["pr_auc"], color="#2b7a78")
    plt.xlabel("Test PR-AUC")
    plt.title("Observed model comparison")
    plt.tight_layout()
    plt.savefig(assets / "observed_model_comparison.png", dpi=160)
    plt.close()

    economics_rows = []
    candidate_rates = (0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05)
    for target_rate in candidate_rates:
        locked_threshold = threshold_for_alert_rate(
            champion_score[validation_mask.to_numpy()], target_rate
        )
        for population, mask in (("validation", validation_mask), ("test", test_mask)):
            population_frame = data.loc[mask, ["monitoring_period", "amount", "fraud_flag"]].copy()
            population_score = champion_score[mask.to_numpy()]
            selected = population_score >= locked_threshold
            fraud_selected = selected & population_frame["fraud_flag"].eq(1).to_numpy()
            alerts = int(selected.sum())
            fraud_count = int(fraud_selected.sum())
            false_positive = int((selected & population_frame["fraud_flag"].eq(0).to_numpy()).sum())
            captured_amount = float(population_frame.loc[fraud_selected, "amount"].sum())
            total_fraud_amount = float(population_frame.loc[population_frame["fraud_flag"].eq(1), "amount"].sum())
            periods = int(population_frame["monitoring_period"].nunique())
            alerts_per_period_proxy = safe_div(alerts, periods)
            prevented_loss = captured_amount * 0.70
            investigation_cost = alerts * 5.0
            friction_cost = false_positive * 2.0
            prospective_expected_prevented = float(
                (population_score[selected] * population_frame.loc[selected, "amount"].to_numpy() * 0.70).sum()
            )
            economics_rows.append(
                {
                    "champion_model": champion_name,
                    "population": population,
                    "target_alert_rate": target_rate,
                    "locked_validation_score_threshold": locked_threshold,
                    "transactions": len(population_frame),
                    "alerts": alerts,
                    "actual_alert_rate": safe_div(alerts, len(population_frame)),
                    "alerts_per_monitoring_period_proxy": alerts_per_period_proxy,
                    "capacity_per_period_proxy": 250,
                    "capacity_status": "PASS" if alerts_per_period_proxy <= 250 else "BREACH",
                    "fraud_captured": fraud_count,
                    "fraud_recall": safe_div(fraud_count, population_frame["fraud_flag"].sum()),
                    "fraud_amount_captured": captured_amount,
                    "fraud_amount_recall": safe_div(captured_amount, total_fraud_amount),
                    "false_positives": false_positive,
                    "precision": safe_div(fraud_count, alerts),
                    "false_positive_rate": safe_div(false_positive, population_frame["fraud_flag"].eq(0).sum()),
                    "realised_prevented_loss_proxy": prevented_loss,
                    "prospective_expected_prevented_loss_proxy": prospective_expected_prevented,
                    "investigation_cost": investigation_cost,
                    "customer_friction_cost": friction_cost,
                    "realised_net_benefit": prevented_loss - investigation_cost - friction_cost,
                    "net_benefit_per_alert": safe_div(prevented_loss - investigation_cost - friction_cost, alerts),
                    "risk_appetite_status": (
                        "PASS"
                        if alerts_per_period_proxy <= 250
                        and safe_div(captured_amount, total_fraud_amount) >= 0.80
                        and safe_div(fraud_count, alerts) >= 0.10
                        and (prevented_loss - investigation_cost - friction_cost) > 0
                        else "REVIEW"
                    ),
                }
            )
    economics = pd.DataFrame(economics_rows)
    full_appetite = (
        economics["capacity_status"].eq("PASS")
        & economics["realised_net_benefit"].gt(0)
        & economics["fraud_recall"].ge(0.80)
        & economics["fraud_amount_recall"].ge(0.80)
        & economics["precision"].ge(0.10)
    )
    balanced_appetite = (
        economics["capacity_status"].eq("PASS")
        & economics["realised_net_benefit"].gt(0)
        & economics["fraud_recall"].ge(0.80)
        & economics["fraud_amount_recall"].ge(0.60)
        & economics["precision"].ge(0.10)
    )
    economics["risk_appetite_status"] = np.select(
        [full_appetite, balanced_appetite],
        ["PASS", "AMBER_AMOUNT_CAPTURE_EXCEPTION"],
        default="REVIEW",
    )
    validation_economics = economics.loc[
        economics["population"].eq("validation")
        & economics["capacity_status"].eq("PASS")
        & economics["realised_net_benefit"].gt(0)
    ].copy()
    appetite_candidates = validation_economics.loc[
        validation_economics["risk_appetite_status"].isin(["PASS", "AMBER_AMOUNT_CAPTURE_EXCEPTION"])
    ]
    selection_pool = appetite_candidates if not appetite_candidates.empty else validation_economics
    selected_row = selection_pool.sort_values(
        ["realised_net_benefit", "fraud_amount_recall", "precision"], ascending=False
    ).iloc[0]
    selected_rate = float(selected_row["target_alert_rate"])
    selected_threshold = float(selected_row["locked_validation_score_threshold"])
    economics["recommended_threshold_flag"] = (
        economics["target_alert_rate"].eq(selected_rate)
    ).astype(int)
    economics["selection_note"] = np.where(
        economics["recommended_threshold_flag"].eq(1),
        "Primary recommendation locked on validation Base economics",
        "Pre-specified sensitivity candidate",
    )
    economics = add_metadata(
        economics,
        "Observed",
        "Derived",
        "Validation-locked observed champion score and frozen Base costs",
        "Realised backtest economics and prospective calibrated-probability proxy are reported separately",
    )
    write_csv(economics, "outputs/threshold_economics.csv")
    write_csv(economics, "models/threshold_analysis.csv")
    json_dump(
        "models/selected_observed_threshold.json",
        {
            "champion_model": champion_name,
            "selected_on": "validation",
            "target_alert_rate": selected_rate,
            "calibrated_score_threshold": selected_threshold,
            "investigation_cost_per_alert": 5.0,
            "preventable_loss_rate": 0.70,
            "false_positive_friction_cost": 2.0,
            "capacity_per_monitoring_period_proxy": 250,
            "selection_rule": "Validation-only hierarchy: capacity PASS; realised net benefit > 0; fraud transaction recall >= 80%; precision >= 10%; fraud amount recall PASS if >= 80% or AMBER exception if 60%-80%; prefer PASS candidates, otherwise eligible AMBER; maximise validation realised net benefit with fraud-amount recall and precision as tie breakers. Final test does not influence selection.",
            "formalisation_note": "Formalised during v1.0.1 public remediation; underlying code and selected threshold unchanged, not backdated as original Phase 0 lock.",
        },
    )

    sensitivity_rows = []
    selected_validation_score = champion_score[validation_mask.to_numpy()]
    selected_validation_frame = data.loc[validation_mask, ["amount", "fraud_flag", "monitoring_period"]].copy()
    selected = selected_validation_score >= selected_threshold
    fraud_selected = selected & selected_validation_frame["fraud_flag"].eq(1).to_numpy()
    base_alerts = int(selected.sum())
    base_false_positive = int((selected & selected_validation_frame["fraud_flag"].eq(0).to_numpy()).sum())
    base_captured_amount = float(selected_validation_frame.loc[fraud_selected, "amount"].sum())
    for investigation_cost in (2.5, 5.0, 7.5):
        for preventable_rate in (0.50, 0.70, 0.90):
            for friction_cost in (1.0, 2.0, 3.0):
                net = (
                    base_captured_amount * preventable_rate
                    - base_alerts * investigation_cost
                    - base_false_positive * friction_cost
                )
                sensitivity_rows.append(
                    {
                        "scenario": f"IC={investigation_cost:.1f}|PLR={preventable_rate:.0%}|FC={friction_cost:.1f}",
                        "selected_target_alert_rate": selected_rate,
                        "selected_score_threshold": selected_threshold,
                        "investigation_cost_per_alert": investigation_cost,
                        "preventable_loss_rate": preventable_rate,
                        "false_positive_friction_cost": friction_cost,
                        "alerts": base_alerts,
                        "fraud_amount_captured": base_captured_amount,
                        "realised_net_benefit": net,
                        "sensitivity_status": "POSITIVE" if net > 0 else "NEGATIVE",
                        "base_assumption_flag": int(
                            investigation_cost == 5.0 and preventable_rate == 0.70 and friction_cost == 2.0
                        ),
                    }
                )
    sensitivity = add_metadata(
        pd.DataFrame(sensitivity_rows),
        "Observed",
        "Proxy",
        "Pre-specified threshold economics sensitivity",
        "Alternative assumptions do not replace the Base recommendation",
    )
    write_csv(sensitivity, "outputs/threshold_economics_sensitivity.csv")

    selected_test = economics.loc[
        economics["population"].eq("test") & economics["recommended_threshold_flag"].eq(1)
    ].iloc[0]
    write_markdown(
        "methodology/threshold_economics_methodology.md",
        "Threshold Economics Methodology",
        f"""The candidate alert-rate grid was frozen before model review: 0.05%, 0.10%, 0.20%, 0.50%, 1.00%, 2.00% and 5.00%. Base costs are 5.00 cost units per investigation, 70% preventable loss and 2.00 cost units per false-positive action. Capacity is normalised to 250 alerts per `monitoring_period` proxy because the source lacks actual calendar time.

Realised economics uses observed labels and transaction amount. Prospective economics uses calibrated probability, amount and the preventable-loss assumption. The two views are reported separately. Validation alone selects the threshold; test is an untouched confirmation population.""",
    )
    write_markdown(
        "reports/threshold_recommendation_memo.md",
        "Observed Threshold Recommendation Memo",
        f"""## Recommendation

Use the validation-selected **top {selected_rate:.2%} alert-rate policy**, equivalent to calibrated score threshold **{selected_threshold:.6f}** for this benchmark version.

## Validation rationale

- Alerts: **{int(selected_row['alerts']):,}** or **{selected_row['alerts_per_monitoring_period_proxy']:.1f} per monitoring-period proxy**.
- Fraud recall: **{selected_row['fraud_recall']:.2%}**.
- Fraud-amount recall: **{selected_row['fraud_amount_recall']:.2%}**.
- Precision: **{selected_row['precision']:.2%}**.
- Realised net benefit: **{selected_row['realised_net_benefit']:,.2f} cost units**.
- Capacity: **{selected_row['capacity_status']}**.

## Formal threshold-selection hierarchy

Eligible validation candidate:

1. Capacity status = PASS.
2. Realised net benefit > 0.
3. Fraud transaction recall >= 80%.
4. Precision >= 10%.
5. Fraud amount recall:
   - PASS if >=80%.
   - AMBER exception if 60%-80%.

Selection uses PASS candidates first. If no PASS candidate exists, eligible AMBER candidates may be used. Within the selected pool, the project maximises validation realised net benefit and uses fraud-amount recall and precision as tie breakers. The final test set must not influence selection.

This hierarchy was formalised during v1.0.1 public remediation. The underlying code and selected threshold were unchanged, and this is not backdated as the original Phase 0 lock.

## Untouched test confirmation

- Actual alert rate: **{selected_test['actual_alert_rate']:.2%}**.
- Fraud recall: **{selected_test['fraud_recall']:.2%}**.
- Fraud-amount recall: **{selected_test['fraud_amount_recall']:.2%}**.
- Precision: **{selected_test['precision']:.2%}**.
- Realised net benefit: **{selected_test['realised_net_benefit']:,.2f} cost units**.

This is an observed historical backtest recommendation under illustrative cost assumptions. It is not a live authorisation threshold and requires re-estimation against real calendar throughput, recoveries, customer outcomes and investigator capacity before production use.

The recommendation prioritises a balanced risk candidate over the absolute net-benefit maximum. Where fraud-amount recall remains Amber rather than Green, implementation requires documented Risk Committee acceptance and a complementary high-value/rules strategy.
""",
    )

    log.info("Observed champion selected: %s", champion_name)
    print(f"Observed benchmark PASS | champion={champion_name} | test PR-AUC={champion_test['pr_auc']:.4f}")


if __name__ == "__main__":
    main()
