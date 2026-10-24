"""Tests for eval.metrics pure functions.

Tests on tiny fixed lists with hand-computed expected values and edge cases.
"""

from eval.metrics import (
    MetricRatio,
    auc,
    f1,
    false_alarm_rate,
    false_alarms,
    hits,
    misses,
    precision,
    recall,
    roc_points,
    true_negatives,
)


def test_hand_computed_tiny_list():
    # 4 entities: 2 tunnels (indices 0, 1), 2 benigns (indices 2, 3)
    # predictions: entity 0 flagged (hit), entity 1 missed, entity 2 flagged (false alarm), entity 3 clean
    y_true = [1, 1, 0, 0]
    y_pred = [1, 0, 1, 0]

    assert hits(y_true, y_pred) == 1
    assert misses(y_true, y_pred) == 1
    assert false_alarms(y_true, y_pred) == 1
    assert true_negatives(y_true, y_pred) == 1

    # Precision: 1 hit / (1 hit + 1 false alarm) = 1/2 = 0.5
    prec = precision(y_true, y_pred)
    assert prec == MetricRatio(0.5, 1, 2)
    assert prec.ratio == 0.5
    assert prec.numerator == 1
    assert prec.denominator == 2

    # Recall: 1 hit / (1 hit + 1 miss) = 1/2 = 0.5
    rec = recall(y_true, y_pred)
    assert rec == MetricRatio(0.5, 1, 2)

    # F1: 2*1 / (2*1 + 1 + 1) = 2/4 = 0.5
    f1_res = f1(y_true, y_pred)
    assert f1_res == MetricRatio(0.5, 2, 4)

    # False-alarm rate: 1 false alarm / (1 false alarm + 1 true negative) = 1/2 = 0.5
    far = false_alarm_rate(y_true, y_pred)
    assert far == MetricRatio(0.5, 1, 2)


def test_edge_case_empty_list():
    y_true: list[int] = []
    y_pred: list[int] = []

    assert hits(y_true, y_pred) == 0
    assert misses(y_true, y_pred) == 0
    assert false_alarms(y_true, y_pred) == 0
    assert true_negatives(y_true, y_pred) == 0

    assert precision(y_true, y_pred) == MetricRatio(None, 0, 0)
    assert recall(y_true, y_pred) == MetricRatio(None, 0, 0)
    assert f1(y_true, y_pred) == MetricRatio(None, 0, 0)
    assert false_alarm_rate(y_true, y_pred) == MetricRatio(None, 0, 0)
    assert roc_points(y_true, []) == []
    assert auc(y_true, []) is None


def test_edge_case_all_hits():
    y_true = [1, 1, 1]
    y_pred = [1, 1, 1]

    assert hits(y_true, y_pred) == 3
    assert misses(y_true, y_pred) == 0
    assert false_alarms(y_true, y_pred) == 0
    assert true_negatives(y_true, y_pred) == 0

    assert precision(y_true, y_pred) == MetricRatio(1.0, 3, 3)
    assert recall(y_true, y_pred) == MetricRatio(1.0, 3, 3)
    assert f1(y_true, y_pred) == MetricRatio(1.0, 6, 6)
    # No negatives exist, so FAR denominator is 0
    assert false_alarm_rate(y_true, y_pred) == MetricRatio(None, 0, 0)


def test_edge_case_all_misses():
    y_true = [1, 1]
    y_pred = [0, 0]

    assert hits(y_true, y_pred) == 0
    assert misses(y_true, y_pred) == 2
    assert false_alarms(y_true, y_pred) == 0
    assert true_negatives(y_true, y_pred) == 0

    # Denominator for precision is 0
    assert precision(y_true, y_pred) == MetricRatio(None, 0, 0)
    assert recall(y_true, y_pred) == MetricRatio(0.0, 0, 2)
    assert f1(y_true, y_pred) == MetricRatio(0.0, 0, 2)
    assert false_alarm_rate(y_true, y_pred) == MetricRatio(None, 0, 0)


def test_edge_case_one_class_only_auc_is_undefined_not_zero():
    # Only positive class
    assert auc([1, 1, 1], [0.9, 0.8, 0.7]) is None
    # Only negative class
    assert auc([0, 0, 0], [0.1, 0.2, 0.3]) is None


def test_auc_and_roc_points_hand_computed():
    # 2 positive, 2 negative
    y_true = [1, 0, 1, 0]
    scores = [0.9, 0.8, 0.7, 0.1]
    # Points at cutoffs:
    # >= 0.9: TP=1, FP=0 -> TPR=0.5, FPR=0.0
    # >= 0.8: TP=1, FP=1 -> TPR=0.5, FPR=0.5
    # >= 0.7: TP=2, FP=1 -> TPR=1.0, FPR=0.5
    # >= 0.1: TP=2, FP=2 -> TPR=1.0, FPR=1.0
    # ROC points: (0, 0), (0.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0)
    # Area:
    # (0 to 0.5): rectangle 0.5 * 0.5 = 0.25
    # (0.5 to 1.0): rectangle 0.5 * 1.0 = 0.50
    # Total AUC = 0.75
    val = auc(y_true, scores)
    assert val is not None
    assert round(val, 2) == 0.75
