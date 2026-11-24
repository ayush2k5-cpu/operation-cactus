"""Generate updated high-resolution figures for Paper 1 revision."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import auc, confusion_matrix, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

from eval.paper_baseline import generate_synthetic_data

OUT_DIR = Path(__file__).resolve().parent.parent / "eval" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Generate baseline data
X, clean_y, noisy_y, ids = generate_synthetic_data(seed=42)
X_train, X_test, y_train, y_test = train_test_split(
    X, noisy_y, test_size=0.2, random_state=42, stratify=noisy_y
)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42).fit(X_train_s, y_train)
svm = SVC(kernel="rbf", C=10.0, gamma="scale", probability=True, random_state=42).fit(
    X_train_s, y_train
)
xgb = XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42,
    eval_metric="logloss",
).fit(X_train_s, y_train)

models = [("Logistic Regression", lr), ("SVM (RBF)", svm), ("XGBoost", xgb)]

# Fig 1: Confusion Matrices
fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), dpi=300)
for ax, (name, clf) in zip(axes, models):
    pred = clf.predict(X_test_s)
    cm = confusion_matrix(y_test, pred)
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.set_title(f"{name}\n(Total Acc: {np.trace(cm)}/200)", fontsize=11, fontweight="bold")
    tick_marks = np.arange(2)
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(["Benign (0)", "Covert (1)"], fontsize=9)
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(["Benign (0)", "Covert (1)"], fontsize=9)
    ax.set_xlabel("Predicted Label", fontsize=10)
    ax.set_ylabel("True Label", fontsize=10)

    thresh = cm.max() / 2.0
    for i in range(2):
        for j in range(2):
            val = cm[i, j]
            label = f"{val}\n({'TN' if (i == 0 and j == 0) else 'FP' if (i == 0 and j == 1) else 'FN' if (i == 1 and j == 0) else 'TP'})"
            ax.text(
                j,
                i,
                label,
                ha="center",
                va="center",
                color="white" if val > thresh else "black",
                fontsize=10,
                fontweight="bold",
            )

plt.tight_layout()
fig1_path = OUT_DIR / "fig1_confusion_matrices.png"
plt.savefig(fig1_path, bbox_inches="tight")
plt.close()
print("Saved:", fig1_path)

# Fig 2: ROC Curves
fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
colors = {"Logistic Regression": "#1f77b4", "SVM (RBF)": "#2ca02c", "XGBoost": "#d62728"}
styles = {"Logistic Regression": "-", "SVM (RBF)": "--", "XGBoost": "-."}

for name, clf in models:
    prob = clf.predict_proba(X_test_s)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, prob)
    roc_auc = auc(fpr, tpr)
    ax.plot(
        fpr,
        tpr,
        label=f"{name} (AUC = {roc_auc:.4f})",
        color=colors[name],
        linestyle=styles[name],
        linewidth=2,
    )

ax.plot([0, 1], [0, 1], "k--", alpha=0.6, label="Random Chance (AUC = 0.5000)")
ax.set_xlim([-0.02, 1.02])
ax.set_ylim([-0.02, 1.02])
ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
ax.set_ylabel("True Positive Rate (Recall / Sensitivity)", fontsize=11)
ax.set_title("ROC Curve Comparison on Held-Out Test Set", fontsize=12, fontweight="bold")
ax.legend(loc="lower right", fontsize=9)
ax.grid(True, linestyle=":", alpha=0.6)

plt.tight_layout()
fig2_path = OUT_DIR / "fig2_roc_curves.png"
plt.savefig(fig2_path, bbox_inches="tight")
plt.close()
print("Saved:", fig2_path)

# Fig 3: Metrics Comparison Bar Chart
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=300)
metric_names = ["Accuracy", "Precision", "Recall", "F1-Score", "Specificity", "ROC-AUC"]
bar_width = 0.25
x_pos = np.arange(len(metric_names))

for idx, (name, clf) in enumerate(models):
    pred = clf.predict(X_test_s)
    prob = clf.predict_proba(X_test_s)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    vals = [
        (tp + tn) / 200,
        tp / (tp + fp),
        tp / (tp + fn),
        2 * tp / (2 * tp + fp + fn),
        tn / (tn + fp),
        auc(*roc_curve(y_test, prob)[:2]),
    ]
    ax.bar(
        x_pos + idx * bar_width,
        [v * 100 for v in vals],
        bar_width,
        label=name,
        color=colors[name],
        alpha=0.9,
    )

ax.set_xticks(x_pos + bar_width)
ax.set_xticklabels(metric_names, fontsize=10)
ax.set_ylabel("Score (%)", fontsize=11)
ax.set_ylim([85, 100])
ax.set_title(
    "Performance Metric Comparison on Held-Out Test Partition", fontsize=12, fontweight="bold"
)
ax.legend(loc="lower left", fontsize=9)
ax.grid(axis="y", linestyle=":", alpha=0.6)

plt.tight_layout()
fig3_path = OUT_DIR / "fig3_metrics_comparison.png"
plt.savefig(fig3_path, bbox_inches="tight")
plt.close()
print("Saved:", fig3_path)
