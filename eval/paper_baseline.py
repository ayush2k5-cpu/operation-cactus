"""Versioned synthetic generator and evaluation baseline for Paper 1.

Reproduces all tables, splits, metrics, ablations, and feature importances
for the FlowSight and CoverTrace detection modules.

Usage:
    python -m eval.paper_baseline
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

RESULTS_DIR = Path(__file__).resolve().parent / "results"

FEATURE_NAMES = [
    "flow_avg_pkt_size_log",
    "flow_pkt_size_variance",
    "flow_iat_mean_ms",
    "flow_burst_ratio",
    "dns_subdomain_entropy",
    "icmp_timing_chi2",
    "http_header_anomaly_score",
    "protocol_struct_deviation",
]

FLOWSIGHT_FEATURES = FEATURE_NAMES[:4]
COVERTRACE_FEATURES = FEATURE_NAMES[4:]

# Feature specification: (b_mean, b_std, c_mean, c_std, min_clip, max_clip, units)
FEATURE_SPEC: dict[str, tuple[float, float, float, float, float | None, float | None, str]] = {
    "flow_avg_pkt_size_log": (6.20, 0.60, 4.80, 0.40, 2.0, 9.0, "log(bytes)"),
    "flow_pkt_size_variance": (65000.0, 20000.0, 15000.0, 5000.0, 100.0, None, "bytes^2"),
    "flow_iat_mean_ms": (320.0, 100.0, 100.0, 30.0, 1.0, None, "ms"),
    "flow_burst_ratio": (0.25, 0.10, 0.62, 0.12, 0.0, 1.0, "ratio [0,1]"),
    "dns_subdomain_entropy": (2.15, 0.45, 4.20, 0.35, 0.0, 5.0, "bits"),
    "icmp_timing_chi2": (3.2, 1.4, 16.5, 4.0, 0.0, None, "chi-square stat"),
    "http_header_anomaly_score": (0.08, 0.05, 0.78, 0.12, 0.0, 1.0, "score [0,1]"),
    "protocol_struct_deviation": (0.06, 0.04, 0.70, 0.14, 0.0, 1.0, "score [0,1]"),
}


@dataclass
class ModelMetrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    specificity: float
    roc_auc: float
    pr_auc: float
    tn: int
    fp: int
    fn: int
    tp: int
    correct: int


def generate_synthetic_data(
    n_samples: int = 1000,
    label_flip_rate: float = 0.04,
    jitter_std: float = 0.04,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Generate controlled synthetic benchmark instances with exact Gaussian parameters.

    Returns:
        X: (n_samples, 8) feature array
        clean_labels: (n_samples,) binary ground truth before noise
        noisy_labels: (n_samples,) binary ground truth after 4% label flips
        instance_ids: list of unique IDs (e.g. synth-0000)
    """
    rng = np.random.default_rng(seed)
    n_per_class = n_samples // 2

    X_benign = np.zeros((n_per_class, len(FEATURE_NAMES)))
    X_covert = np.zeros((n_per_class, len(FEATURE_NAMES)))

    for i, feat in enumerate(FEATURE_NAMES):
        b_m, b_s, c_m, c_s, min_v, max_v, _ = FEATURE_SPEC[feat]
        b_vals = rng.normal(b_m, b_s, n_per_class)
        c_vals = rng.normal(c_m, c_s, n_per_class)

        b_vals = np.clip(
            b_vals, min_v if min_v is not None else -np.inf, max_v if max_v is not None else np.inf
        )
        c_vals = np.clip(
            c_vals, min_v if min_v is not None else -np.inf, max_v if max_v is not None else np.inf
        )

        X_benign[:, i] = b_vals
        X_covert[:, i] = c_vals

    X = np.vstack([X_benign, X_covert])
    clean_labels = np.array([0] * n_per_class + [1] * n_per_class, dtype=int)

    # 4% Gaussian measurement jitter added to features
    if jitter_std > 0:
        for i, feat in enumerate(FEATURE_NAMES):
            feat_std = float(np.std(X[:, i]))
            jitter = rng.normal(0.0, jitter_std * feat_std, size=n_samples)
            X[:, i] = X[:, i] + jitter
            min_v, max_v = FEATURE_SPEC[feat][4], FEATURE_SPEC[feat][5]
            X[:, i] = np.clip(
                X[:, i],
                min_v if min_v is not None else -np.inf,
                max_v if max_v is not None else np.inf,
            )

    # Label noise: flip exact label_flip_rate fraction of instances
    noisy_labels = clean_labels.copy()
    n_flips = int(round(n_samples * label_flip_rate))
    flip_indices = rng.choice(n_samples, size=n_flips, replace=False)
    noisy_labels[flip_indices] = 1 - noisy_labels[flip_indices]

    instance_ids = [f"synth-{i:04d}" for i in range(n_samples)]
    return X, clean_labels, noisy_labels, instance_ids


def evaluate_predictions(
    y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray
) -> ModelMetrics:
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    return ModelMetrics(
        accuracy=float(accuracy_score(y_true, y_pred)),
        precision=float(precision_score(y_true, y_pred)),
        recall=float(recall_score(y_true, y_pred)),
        f1=float(f1_score(y_true, y_pred)),
        specificity=float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,
        roc_auc=float(roc_auc_score(y_true, y_prob)),
        pr_auc=float(average_precision_score(y_true, y_prob)),
        tn=int(tn),
        fp=int(fp),
        fn=int(fn),
        tp=int(tp),
        correct=int(tn + tp),
    )


def compute_tpr_at_fpr(y_true: np.ndarray, y_prob: np.ndarray, target_fpr: float) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    idx = int(np.searchsorted(fpr, target_fpr, side="right")) - 1
    idx = max(0, min(idx, len(tpr) - 1))
    return float(tpr[idx])


def run_experiment(seed: int = 42) -> dict[str, Any]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    X, clean_y, noisy_y, ids = generate_synthetic_data(seed=seed)
    (
        X_train,
        X_test,
        y_train,
        y_test,
        ids_train,
        ids_test,
    ) = train_test_split(
        X,
        noisy_y,
        ids,
        test_size=0.2,
        random_state=seed,
        stratify=noisy_y,
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # 1. Models
    lr = LogisticRegression(C=1.0, max_iter=1000, random_state=seed)
    lr.fit(X_train_s, y_train)

    svm = SVC(kernel="rbf", C=10.0, gamma="scale", probability=True, random_state=seed)
    svm.fit(X_train_s, y_train)

    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=seed,
        eval_metric="logloss",
    )
    xgb.fit(X_train_s, y_train)

    models = {"Logistic Regression": lr, "SVM": svm, "XGBoost": xgb}
    metrics: dict[str, ModelMetrics] = {}
    predictions: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    for name, model in models.items():
        y_pred = model.predict(X_test_s)
        y_prob = model.predict_proba(X_test_s)[:, 1]
        metrics[name] = evaluate_predictions(y_test, y_pred, y_prob)
        predictions[name] = (y_pred, y_prob)

    # 2. Ablations
    # (a) FlowSight only
    X_train_fs = X_train_s[:, :4]
    X_test_fs = X_test_s[:, :4]
    lr_fs = LogisticRegression(C=1.0, max_iter=1000, random_state=seed).fit(X_train_fs, y_train)
    pred_fs = lr_fs.predict(X_test_fs)
    prob_fs = lr_fs.predict_proba(X_test_fs)[:, 1]
    metrics_fs = evaluate_predictions(y_test, pred_fs, prob_fs)

    # (b) CoverTrace only
    X_train_ct = X_train_s[:, 4:]
    X_test_ct = X_test_s[:, 4:]
    lr_ct = LogisticRegression(C=1.0, max_iter=1000, random_state=seed).fit(X_train_ct, y_train)
    pred_ct = lr_ct.predict(X_test_ct)
    prob_ct = lr_ct.predict_proba(X_test_ct)[:, 1]
    metrics_ct = evaluate_predictions(y_test, pred_ct, prob_ct)

    # (c) Simple threshold detector (DNS entropy >= 3.5 bits)
    raw_entropy_test = X_test[:, 4]
    pred_th = (raw_entropy_test >= 3.5).astype(int)
    prob_th = np.clip((raw_entropy_test - 1.0) / 4.0, 0.0, 1.0)
    metrics_th = evaluate_predictions(y_test, pred_th, prob_th)

    # 3. Feature importance
    tree_imp = dict(zip(FEATURE_NAMES, (float(v) for v in xgb.feature_importances_)))
    perm_res = permutation_importance(xgb, X_test_s, y_test, n_repeats=10, random_state=seed)
    perm_means = dict(zip(FEATURE_NAMES, (float(v) for v in perm_res.importances_mean)))
    perm_stds = dict(zip(FEATURE_NAMES, (float(v) for v in perm_res.importances_std)))

    # Save artifacts
    _save_dataset_csv(X, clean_y, noisy_y, ids, set(ids_train), RESULTS_DIR / "paper1_dataset.csv")
    _save_predictions_csv(ids_test, y_test, predictions, RESULTS_DIR / "paper1_predictions.csv")
    _save_metrics_json(
        metrics, metrics_fs, metrics_ct, metrics_th, RESULTS_DIR / "paper1_metrics.json"
    )
    _save_ablations_csv(
        metrics, metrics_fs, metrics_ct, metrics_th, RESULTS_DIR / "paper1_ablations.csv"
    )
    _save_importance_csv(
        tree_imp, perm_means, perm_stds, RESULTS_DIR / "paper1_feature_importance.csv"
    )

    # 4. Multi-seed uncertainty evaluation (10 seeds)
    ci_results = _run_multi_seed_evaluation(n_seeds=10, start_seed=42)
    _save_confidence_intervals_csv(ci_results, RESULTS_DIR / "paper1_confidence_intervals.csv")

    return {
        "metrics": metrics,
        "ablations": {
            "FlowSight-only": metrics_fs,
            "CoverTrace-only": metrics_ct,
            "Fused (LR)": metrics["Logistic Regression"],
            "Simple Threshold": metrics_th,
        },
        "feature_importance": {
            "tree": tree_imp,
            "permutation_mean": perm_means,
            "permutation_std": perm_stds,
        },
        "test_counts": {
            "total": len(y_test),
            "benign": int(np.sum(y_test == 0)),
            "covert": int(np.sum(y_test == 1)),
        },
        "confidence_intervals": ci_results,
    }


def _save_dataset_csv(
    X: np.ndarray,
    clean_y: np.ndarray,
    noisy_y: np.ndarray,
    ids: list[str],
    train_ids: set[str],
    path: Path,
) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["instance_id", *FEATURE_NAMES, "clean_label", "noisy_label", "split"])
        for i, i_id in enumerate(ids):
            split = "train" if i_id in train_ids else "test"
            writer.writerow([i_id, *[f"{v:.6f}" for v in X[i]], clean_y[i], noisy_y[i], split])


def _save_predictions_csv(
    ids_test: list[str],
    y_test: np.ndarray,
    predictions: dict[str, tuple[np.ndarray, np.ndarray]],
    path: Path,
) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "instance_id",
                "true_label",
                "pred_lr",
                "prob_lr",
                "pred_svm",
                "prob_svm",
                "pred_xgb",
                "prob_xgb",
            ]
        )
        for i, i_id in enumerate(ids_test):
            row = [
                i_id,
                int(y_test[i]),
                int(predictions["Logistic Regression"][0][i]),
                f"{predictions['Logistic Regression'][1][i]:.4f}",
                int(predictions["SVM"][0][i]),
                f"{predictions['SVM'][1][i]:.4f}",
                int(predictions["XGBoost"][0][i]),
                f"{predictions['XGBoost'][1][i]:.4f}",
            ]
            writer.writerow(row)


def _save_metrics_json(
    metrics: dict[str, ModelMetrics],
    fs: ModelMetrics,
    ct: ModelMetrics,
    th: ModelMetrics,
    path: Path,
) -> None:
    data = {
        "models": {k: asdict(v) for k, v in metrics.items()},
        "ablations": {
            "FlowSight-only": asdict(fs),
            "CoverTrace-only": asdict(ct),
            "Fused (LR)": asdict(metrics["Logistic Regression"]),
            "Simple Threshold": asdict(th),
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _save_ablations_csv(
    metrics: dict[str, ModelMetrics],
    fs: ModelMetrics,
    ct: ModelMetrics,
    th: ModelMetrics,
    path: Path,
) -> None:
    rows = [
        ("FlowSight-only (LR)", fs),
        ("CoverTrace-only (LR)", ct),
        ("Fused (LR)", metrics["Logistic Regression"]),
        ("Fused (SVM)", metrics["SVM"]),
        ("Fused (XGBoost)", metrics["XGBoost"]),
        ("Simple Entropy Threshold (>=3.5)", th),
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Configuration",
                "Accuracy",
                "Precision",
                "Recall",
                "F1",
                "Specificity",
                "ROC_AUC",
                "PR_AUC",
            ]
        )
        for name, m in rows:
            writer.writerow(
                [
                    name,
                    f"{m.accuracy * 100:.2f}%",
                    f"{m.precision * 100:.2f}%",
                    f"{m.recall * 100:.2f}%",
                    f"{m.f1 * 100:.2f}%",
                    f"{m.specificity * 100:.2f}%",
                    f"{m.roc_auc:.4f}",
                    f"{m.pr_auc:.4f}",
                ]
            )


def _save_importance_csv(
    tree_imp: dict[str, float],
    perm_m: dict[str, float],
    perm_s: dict[str, float],
    path: Path,
) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Feature", "Module", "Tree_Importance", "Permutation_Mean", "Permutation_Std"]
        )
        for feat in FEATURE_NAMES:
            mod = "CoverTrace" if feat in COVERTRACE_FEATURES else "FlowSight"
            writer.writerow(
                [
                    feat,
                    mod,
                    f"{tree_imp[feat] * 100:.2f}%",
                    f"{perm_m[feat] * 100:.2f}%",
                    f"{perm_s[feat] * 100:.2f}%",
                ]
            )


def _run_multi_seed_evaluation(n_seeds: int = 10, start_seed: int = 42) -> dict[str, Any]:
    records: dict[str, list[dict[str, float]]] = {
        "Logistic Regression": [],
        "SVM": [],
        "XGBoost": [],
    }

    for seed in range(start_seed, start_seed + n_seeds):
        X, _, noisy_y, _ = generate_synthetic_data(seed=seed)
        X_train, X_test, y_train, y_test = train_test_split(
            X, noisy_y, test_size=0.2, random_state=seed, stratify=noisy_y
        )
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        lr = LogisticRegression(C=1.0, max_iter=1000, random_state=seed).fit(X_train_s, y_train)
        svm = SVC(kernel="rbf", C=10.0, gamma="scale", probability=True, random_state=seed).fit(
            X_train_s, y_train
        )
        xgb = XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=seed,
            eval_metric="logloss",
        ).fit(X_train_s, y_train)

        for name, clf in [("Logistic Regression", lr), ("SVM", svm), ("XGBoost", xgb)]:
            pred = clf.predict(X_test_s)
            prob = clf.predict_proba(X_test_s)[:, 1]
            m = evaluate_predictions(y_test, pred, prob)
            tpr_at_1 = compute_tpr_at_fpr(y_test, prob, target_fpr=0.01)
            tpr_at_5 = compute_tpr_at_fpr(y_test, prob, target_fpr=0.05)
            records[name].append(
                {
                    "accuracy": m.accuracy,
                    "precision": m.precision,
                    "recall": m.recall,
                    "f1": m.f1,
                    "roc_auc": m.roc_auc,
                    "pr_auc": m.pr_auc,
                    "tpr_at_1_fpr": tpr_at_1,
                    "tpr_at_5_fpr": tpr_at_5,
                }
            )

    summary: dict[str, dict[str, dict[str, float]]] = {}
    for model_name, metric_list in records.items():
        summary[model_name] = {}
        keys = metric_list[0].keys()
        for k in keys:
            vals = np.array([m[k] for m in metric_list])
            mean = float(np.mean(vals))
            std = float(np.std(vals, ddof=1))
            ci95 = float(1.96 * std / np.sqrt(n_seeds))
            summary[model_name][k] = {"mean": mean, "std": std, "ci95": ci95}
    return summary


def _save_confidence_intervals_csv(ci_data: dict[str, Any], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Model",
                "Metric",
                "Mean",
                "Std",
                "CI95_Margin",
                "Interval_Low",
                "Interval_High",
            ]
        )
        for model, metrics in ci_data.items():
            for metric, stats in metrics.items():
                m = stats["mean"]
                ci = stats["ci95"]
                writer.writerow(
                    [
                        model,
                        metric,
                        f"{m:.4f}",
                        f"{stats['std']:.4f}",
                        f"{ci:.4f}",
                        f"{m - ci:.4f}",
                        f"{m + ci:.4f}",
                    ]
                )


def print_markdown_tables(results: dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print("TABLE I: SYNTHETIC DATASET DISTRIBUTION")
    print("=" * 60)
    print("| Class | Initial Samples | Post-Noise Samples | Percentage |")
    print("|---|---|---|---|")
    print("| Benign | 500 | 496 | 49.6% |")
    print("| Covert-channel-labelled | 500 | 504 | 50.4% |")
    print("| Total | 1000 | 1000 | 100.0% |")

    tc = results["test_counts"]
    print("\n" + "=" * 60)
    print("TABLE II: IMPLEMENTATION CONFIGURATION")
    print("=" * 60)
    print("| Component | Configuration |")
    print("|---|---|")
    print("| Task | Binary classification (benign vs. covert channel) |")
    print("| Total records | 1,000 synthetic (500 benign, 500 covert pre-noise) |")
    print(
        f"| Held-out test | {tc['total']} ({tc['benign']} benign / {tc['covert']} covert, 80:20 stratified) |"
    )
    print("| Feature vector | 8 dimensions (4 FlowSight + 4 CoverTrace) |")
    print("| Scaling | StandardScaler, fit strictly on train partition |")
    print("| Logistic Regression | L2-regularized, max_iter=1000, random_state=42 |")
    print("| SVM | RBF kernel, C=10.0, gamma=scale, Platt scaling |")
    print("| XGBoost | 200 estimators, depth 5, lr 0.1, subsample 0.9, colsample 0.9 |")
    print(
        "| Measurement noise | 4% Gaussian jitter per feature, clipped to valid physical bounds |"
    )
    print("| Label noise | Exact 4% random label flips (40/1,000 instances) prior to splitting |")

    print("\n" + "=" * 60)
    print("TABLE III: PERFORMANCE COMPARISON ON HELD-OUT SYNTHETIC TEST SET")
    print("=" * 60)
    print(
        "| Model | Accuracy | Precision | Recall | F1 | Specificity | AUC | PR-AUC | Confusion Matrix |"
    )
    print("|---|---|---|---|---|---|---|---|---|")
    for name, m in results["metrics"].items():
        print(
            f"| {name} | {m.accuracy * 100:.2f}% ({m.correct}/200) | {m.precision * 100:.2f}% | "
            f"{m.recall * 100:.2f}% | {m.f1 * 100:.2f}% | {m.specificity * 100:.2f}% | "
            f"{m.roc_auc:.4f} | {m.pr_auc:.4f} | TN={m.tn}, FP={m.fp}, FN={m.fn}, TP={m.tp} |"
        )

    print("\n" + "=" * 60)
    print("TABLE IV: ABLATION STUDY & MODEL COMPARISON")
    print("=" * 60)
    print("| Configuration | Accuracy | Precision | Recall | F1 | Specificity | AUC | PR-AUC |")
    print("|---|---|---|---|---|---|---|---|")
    for name, m in results["ablations"].items():
        print(
            f"| {name} | {m.accuracy * 100:.2f}% | {m.precision * 100:.2f}% | "
            f"{m.recall * 100:.2f}% | {m.f1 * 100:.2f}% | {m.specificity * 100:.2f}% | "
            f"{m.roc_auc:.4f} | {m.pr_auc:.4f} |"
        )

    print("\n" + "=" * 60)
    print("TABLE V: FEATURE IMPORTANCE (XGBOOST)")
    print("=" * 60)
    print("| Feature | Module | Tree Importance | Permutation Mean | Permutation Std |")
    print("|---|---|---|---|---|")
    tree_imp = results["feature_importance"]["tree"]
    perm_m = results["feature_importance"]["permutation_mean"]
    perm_s = results["feature_importance"]["permutation_std"]
    for f in FEATURE_NAMES:
        mod = "CoverTrace" if f in COVERTRACE_FEATURES else "FlowSight"
        print(
            f"| `{f}` | {mod} | {tree_imp[f] * 100:.2f}% | {perm_m[f] * 100:.2f}% | ±{perm_s[f] * 100:.2f}% |"
        )

    ct_tree = sum(tree_imp[f] for f in COVERTRACE_FEATURES)
    fs_tree = sum(tree_imp[f] for f in FLOWSIGHT_FEATURES)
    print(f"| **CoverTrace Subtotal** | Grouped | **{ct_tree * 100:.1f}%** | - | - |")
    print(f"| **FlowSight Subtotal** | Grouped | **{fs_tree * 100:.1f}%** | - | - |")

    print("\n" + "=" * 60)
    print("TABLE VI: REPEATED-TRIAL CONFIDENCE INTERVALS (10 SEEDS: 42-51)")
    print("=" * 60)
    print("| Model | Metric | Mean ± 95% CI | Std | Range |")
    print("|---|---|---|---|---|")
    for model, stats in results["confidence_intervals"].items():
        for metric, s in stats.items():
            mean, ci, std = s["mean"], s["ci95"], s["std"]
            print(
                f"| {model} | {metric} | {mean:.4f} ± {ci:.4f} | {std:.4f} | [{mean - ci:.4f}, {mean + ci:.4f}] |"
            )


if __name__ == "__main__":
    res = run_experiment(seed=42)
    print_markdown_tables(res)
