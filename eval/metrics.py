"""Evaluation metric functions for GKMKB.

Pure functions over per-Entity outcomes. Each ratio function returns a MetricRatio
holding the ratio value together with its raw numerator and denominator.
No frameworks, no file or network access.
"""

from typing import NamedTuple


class MetricRatio(NamedTuple):
    ratio: float | None
    numerator: int
    denominator: int


def hits(y_true: list[bool | int], y_pred: list[bool | int]) -> int:
    """Count true positives (tunnel entity flagged)."""
    return sum(1 for yt, yp in zip(y_true, y_pred, strict=False) if yt and yp)


def misses(y_true: list[bool | int], y_pred: list[bool | int]) -> int:
    """Count false negatives (tunnel entity missed)."""
    return sum(1 for yt, yp in zip(y_true, y_pred, strict=False) if yt and not yp)


def false_alarms(y_true: list[bool | int], y_pred: list[bool | int]) -> int:
    """Count false positives (benign entity flagged)."""
    return sum(1 for yt, yp in zip(y_true, y_pred, strict=False) if not yt and yp)


def true_negatives(y_true: list[bool | int], y_pred: list[bool | int]) -> int:
    """Count true negatives (benign entity not flagged)."""
    return sum(1 for yt, yp in zip(y_true, y_pred, strict=False) if not yt and not yp)


def precision(y_true: list[bool | int], y_pred: list[bool | int]) -> MetricRatio:
    """Precision: hits / (hits + false alarms)."""
    tp = hits(y_true, y_pred)
    fp = false_alarms(y_true, y_pred)
    den = tp + fp
    ratio = tp / den if den > 0 else None
    return MetricRatio(ratio, tp, den)


def recall(y_true: list[bool | int], y_pred: list[bool | int]) -> MetricRatio:
    """Recall: hits / (hits + misses)."""
    tp = hits(y_true, y_pred)
    fn = misses(y_true, y_pred)
    den = tp + fn
    ratio = tp / den if den > 0 else None
    return MetricRatio(ratio, tp, den)


def f1(y_true: list[bool | int], y_pred: list[bool | int]) -> MetricRatio:
    """F1 score: 2 * TP / (2 * TP + FP + FN)."""
    tp = hits(y_true, y_pred)
    fp = false_alarms(y_true, y_pred)
    fn = misses(y_true, y_pred)
    num = 2 * tp
    den = 2 * tp + fp + fn
    ratio = num / den if den > 0 else None
    return MetricRatio(ratio, num, den)


def false_alarm_rate(y_true: list[bool | int], y_pred: list[bool | int]) -> MetricRatio:
    """False-alarm rate (FPR): false alarms / (false alarms + true negatives)."""
    fp = false_alarms(y_true, y_pred)
    tn = true_negatives(y_true, y_pred)
    den = fp + tn
    ratio = fp / den if den > 0 else None
    return MetricRatio(ratio, fp, den)


def roc_points(y_true: list[bool | int], scores: list[float]) -> list[tuple[float, float]]:
    """Compute (FPR, TPR) points by sweeping decision threshold.

    Returns empty list if y_true is empty or contains only one class.
    """
    if not y_true or not scores or len(y_true) != len(scores):
        return []
    pos = sum(1 for y in y_true if y)
    neg = sum(1 for y in y_true if not y)
    if pos == 0 or neg == 0:
        return []

    # Sort thresholds descending by score
    sorted_pairs = sorted(zip(scores, y_true, strict=False), key=lambda x: x[0], reverse=True)
    distinct_scores = sorted({score for score, _ in sorted_pairs}, reverse=True)

    points: list[tuple[float, float]] = [(0.0, 0.0)]
    for thr in distinct_scores:
        y_pred = [1 if s >= thr else 0 for s, _ in sorted_pairs]
        tp = sum(1 for (_, yt), yp in zip(sorted_pairs, y_pred, strict=False) if yt and yp)
        fp = sum(1 for (_, yt), yp in zip(sorted_pairs, y_pred, strict=False) if not yt and yp)
        points.append((fp / neg, tp / pos))

    if points[-1] != (1.0, 1.0):
        points.append((1.0, 1.0))

    # Keep points sorted by FPR then TPR
    points.sort(key=lambda p: (p[0], p[1]))
    return points


def auc(y_true: list[bool | int], scores: list[float]) -> float | None:
    """Compute Area Under ROC Curve via the trapezoidal rule.

    Returns None (undefined, not zero) if empty or only one class is present.
    """
    pts = roc_points(y_true, scores)
    if not pts:
        return None

    area = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:], strict=False):
        area += (x2 - x1) * (y1 + y2) / 2.0
    return area
