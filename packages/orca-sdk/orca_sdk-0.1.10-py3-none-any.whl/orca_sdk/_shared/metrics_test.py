"""
IMPORTANT:
- This is a shared file between OrcaLib and the OrcaSDK.
- Please ensure that it does not have any dependencies on the OrcaLib code.
- Make sure to edit this file in orcalib/shared and NOT in orca_sdk, since it will be overwritten there.
"""

from typing import Literal

import numpy as np
import pytest
import sklearn.metrics

from .metrics import (
    calculate_classification_metrics,
    calculate_pr_curve,
    calculate_regression_metrics,
    calculate_roc_curve,
    softmax,
)


def test_binary_metrics():
    y_true = np.array([0, 1, 1, 0, 1])
    y_score = np.array([0.1, 0.9, 0.8, 0.3, 0.2])

    metrics = calculate_classification_metrics(y_true, y_score)

    assert metrics.accuracy == 0.8
    assert metrics.f1_score == 0.8
    assert metrics.roc_auc is not None
    assert metrics.roc_auc > 0.8
    assert metrics.roc_auc < 1.0
    assert metrics.pr_auc is not None
    assert metrics.pr_auc > 0.8
    assert metrics.pr_auc < 1.0
    assert metrics.loss is not None
    assert metrics.loss > 0.0


def test_multiclass_metrics_with_2_classes():
    y_true = np.array([0, 1, 1, 0, 1])
    y_score = np.array([[0.9, 0.1], [0.1, 0.9], [0.2, 0.8], [0.7, 0.3], [0.8, 0.2]])

    metrics = calculate_classification_metrics(y_true, y_score)

    assert metrics.accuracy == 0.8
    assert metrics.f1_score == 0.8
    assert metrics.roc_auc is not None
    assert metrics.roc_auc > 0.8
    assert metrics.roc_auc < 1.0
    assert metrics.pr_auc is not None
    assert metrics.pr_auc > 0.8
    assert metrics.pr_auc < 1.0
    assert metrics.loss is not None
    assert metrics.loss > 0.0


@pytest.mark.parametrize(
    "average, multiclass",
    [("micro", "ovr"), ("macro", "ovr"), ("weighted", "ovr"), ("micro", "ovo"), ("macro", "ovo"), ("weighted", "ovo")],
)
def test_multiclass_metrics_with_3_classes(
    average: Literal["micro", "macro", "weighted"], multiclass: Literal["ovr", "ovo"]
):
    y_true = np.array([0, 1, 1, 0, 2])
    y_score = np.array([[0.9, 0.1, 0.0], [0.1, 0.9, 0.0], [0.2, 0.8, 0.0], [0.7, 0.3, 0.0], [0.0, 0.0, 1.0]])

    metrics = calculate_classification_metrics(y_true, y_score, average=average, multi_class=multiclass)

    assert metrics.accuracy == 1.0
    assert metrics.f1_score == 1.0
    assert metrics.roc_auc is not None
    assert metrics.roc_auc > 0.8
    assert metrics.pr_auc is None
    assert metrics.loss is not None
    assert metrics.loss > 0.0


def test_does_not_modify_logits_unless_necessary():
    logits = np.array([[0.1, 0.9], [0.2, 0.8], [0.7, 0.3], [0.8, 0.2]])
    expected_labels = [0, 1, 0, 1]
    loss = calculate_classification_metrics(expected_labels, logits).loss
    assert loss is not None
    assert np.allclose(
        loss,
        sklearn.metrics.log_loss(expected_labels, logits),
        atol=1e-6,
    )


def test_normalizes_logits_if_necessary():
    logits = np.array([[1.2, 3.9], [1.2, 5.8], [1.2, 2.7], [1.2, 1.3]])
    expected_labels = [0, 1, 0, 1]
    loss = calculate_classification_metrics(expected_labels, logits).loss
    assert loss is not None
    assert np.allclose(
        loss,
        sklearn.metrics.log_loss(expected_labels, logits / logits.sum(axis=1, keepdims=True)),
        atol=1e-6,
    )


def test_softmaxes_logits_if_necessary():
    logits = np.array([[-1.2, 3.9], [1.2, -5.8], [1.2, 2.7], [1.2, 1.3]])
    expected_labels = [0, 1, 0, 1]
    loss = calculate_classification_metrics(expected_labels, logits).loss
    assert loss is not None
    assert np.allclose(
        loss,
        sklearn.metrics.log_loss(expected_labels, softmax(logits)),
        atol=1e-6,
    )


def test_handles_nan_logits():
    logits = np.array([[np.nan, np.nan], [np.nan, np.nan], [0.1, 0.9], [0.2, 0.8]])
    expected_labels = [0, 1, 0, 1]
    metrics = calculate_classification_metrics(expected_labels, logits)
    assert metrics.loss is None
    assert metrics.accuracy == 0.25
    assert metrics.f1_score == 0.25
    assert metrics.roc_auc is None
    assert metrics.pr_auc is None
    assert metrics.pr_curve is None
    assert metrics.roc_curve is None
    assert metrics.coverage == 0.5


def test_precision_recall_curve():
    y_true = np.array([0, 1, 1, 0, 1])
    y_score = np.array([0.1, 0.9, 0.8, 0.6, 0.2])

    pr_curve = calculate_pr_curve(y_true, y_score)

    assert len(pr_curve["precisions"]) == len(pr_curve["recalls"]) == len(pr_curve["thresholds"]) == 6
    assert np.allclose(pr_curve["precisions"][0], 0.6)
    assert np.allclose(pr_curve["recalls"][0], 1.0)
    assert np.allclose(pr_curve["precisions"][-1], 1.0)
    assert np.allclose(pr_curve["recalls"][-1], 0.0)

    # test that thresholds are sorted
    assert np.all(np.diff(pr_curve["thresholds"]) >= 0)


def test_roc_curve():
    y_true = np.array([0, 1, 1, 0, 1])
    y_score = np.array([0.1, 0.9, 0.8, 0.6, 0.2])

    roc_curve = calculate_roc_curve(y_true, y_score)

    assert (
        len(roc_curve["false_positive_rates"])
        == len(roc_curve["true_positive_rates"])
        == len(roc_curve["thresholds"])
        == 6
    )
    assert roc_curve["false_positive_rates"][0] == 1.0
    assert roc_curve["true_positive_rates"][0] == 1.0
    assert roc_curve["false_positive_rates"][-1] == 0.0
    assert roc_curve["true_positive_rates"][-1] == 0.0

    # test that thresholds are sorted
    assert np.all(np.diff(roc_curve["thresholds"]) >= 0)


def test_log_loss_handles_missing_classes_in_y_true():
    # y_true contains only a subset of classes, but predictions include an extra class column
    y_true = np.array([0, 1, 0, 1])
    y_score = np.array(
        [
            [0.7, 0.2, 0.1],
            [0.1, 0.8, 0.1],
            [0.6, 0.3, 0.1],
            [0.2, 0.7, 0.1],
        ]
    )

    metrics = calculate_classification_metrics(y_true, y_score)
    expected_loss = sklearn.metrics.log_loss(y_true, y_score, labels=[0, 1, 2])

    assert metrics.loss is not None
    assert np.allclose(metrics.loss, expected_loss)


def test_precision_recall_curve_max_length():
    y_true = np.array([0, 1, 1, 0, 1])
    y_score = np.array([0.1, 0.9, 0.8, 0.6, 0.2])

    pr_curve = calculate_pr_curve(y_true, y_score, max_length=5)
    assert len(pr_curve["precisions"]) == len(pr_curve["recalls"]) == len(pr_curve["thresholds"]) == 5

    assert np.allclose(pr_curve["precisions"][0], 0.6)
    assert np.allclose(pr_curve["recalls"][0], 1.0)
    assert np.allclose(pr_curve["precisions"][-1], 1.0)
    assert np.allclose(pr_curve["recalls"][-1], 0.0)

    # test that thresholds are sorted
    assert np.all(np.diff(pr_curve["thresholds"]) >= 0)


def test_roc_curve_max_length():
    y_true = np.array([0, 1, 1, 0, 1])
    y_score = np.array([0.1, 0.9, 0.8, 0.6, 0.2])

    roc_curve = calculate_roc_curve(y_true, y_score, max_length=5)
    assert (
        len(roc_curve["false_positive_rates"])
        == len(roc_curve["true_positive_rates"])
        == len(roc_curve["thresholds"])
        == 5
    )
    assert np.allclose(roc_curve["false_positive_rates"][0], 1.0)
    assert np.allclose(roc_curve["true_positive_rates"][0], 1.0)
    assert np.allclose(roc_curve["false_positive_rates"][-1], 0.0)
    assert np.allclose(roc_curve["true_positive_rates"][-1], 0.0)

    # test that thresholds are sorted
    assert np.all(np.diff(roc_curve["thresholds"]) >= 0)


# Regression Metrics Tests
def test_perfect_regression_predictions():
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
    y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)

    metrics = calculate_regression_metrics(y_true, y_pred)

    assert metrics.mse == 0.0
    assert metrics.rmse == 0.0
    assert metrics.mae == 0.0
    assert metrics.r2 == 1.0
    assert metrics.explained_variance == 1.0
    assert metrics.loss == 0.0
    assert metrics.anomaly_score_mean is None
    assert metrics.anomaly_score_median is None
    assert metrics.anomaly_score_variance is None


def test_basic_regression_metrics():
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
    y_pred = np.array([1.1, 1.9, 3.2, 3.8, 5.1], dtype=np.float32)

    metrics = calculate_regression_metrics(y_true, y_pred)

    # Check that all metrics are reasonable
    assert metrics.mse > 0.0
    assert metrics.rmse == pytest.approx(np.sqrt(metrics.mse))
    assert metrics.mae > 0.0
    assert 0.0 <= metrics.r2 <= 1.0
    assert 0.0 <= metrics.explained_variance <= 1.0
    assert metrics.loss == metrics.mse

    # Check specific values based on the data
    expected_mse = np.mean((y_true - y_pred) ** 2)
    assert metrics.mse == pytest.approx(expected_mse)

    expected_mae = np.mean(np.abs(y_true - y_pred))
    assert metrics.mae == pytest.approx(expected_mae)


def test_regression_metrics_with_anomaly_scores():
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
    y_pred = np.array([1.1, 1.9, 3.2, 3.8, 5.1], dtype=np.float32)
    anomaly_scores = [0.1, 0.2, 0.15, 0.3, 0.25]

    metrics = calculate_regression_metrics(y_true, y_pred, anomaly_scores)

    assert metrics.anomaly_score_mean == pytest.approx(np.mean(anomaly_scores))
    assert metrics.anomaly_score_median == pytest.approx(np.median(anomaly_scores))
    assert metrics.anomaly_score_variance == pytest.approx(np.var(anomaly_scores))


def test_regression_metrics_handles_nans():
    y_true = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    y_pred = np.array([1.1, 1.9, np.nan], dtype=np.float32)

    metrics = calculate_regression_metrics(y_true, y_pred)

    assert np.allclose(metrics.coverage, 0.6666666666666666)
    assert metrics.mse > 0.0
    assert metrics.rmse > 0.0
    assert metrics.mae > 0.0
    assert 0.0 <= metrics.r2 <= 1.0
    assert 0.0 <= metrics.explained_variance <= 1.0


def test_regression_metrics_handles_none_values():
    # Test with lists containing None values
    y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_pred = [1.1, 1.9, None, 3.8, np.nan]

    metrics = calculate_regression_metrics(y_true, y_pred)

    # Coverage should be 0.6 (3 out of 5 predictions are valid)
    # Positions with None/NaN predictions (indices 2 and 4) are filtered out
    assert np.allclose(metrics.coverage, 0.6)

    # Metrics should be calculated only on valid pairs (indices 0, 1, 3)
    # Valid pairs: (1.0, 1.1), (2.0, 1.9), and (4.0, 3.8)
    expected_mse = np.mean([(1.0 - 1.1) ** 2, (2.0 - 1.9) ** 2, (4.0 - 3.8) ** 2])
    expected_mae = np.mean([abs(1.0 - 1.1), abs(2.0 - 1.9), abs(4.0 - 3.8)])

    assert metrics.mse == pytest.approx(expected_mse)
    assert metrics.mae == pytest.approx(expected_mae)
    assert metrics.rmse == pytest.approx(np.sqrt(expected_mse))
    assert 0.0 <= metrics.r2 <= 1.0
    assert 0.0 <= metrics.explained_variance <= 1.0


def test_regression_metrics_rejects_none_expected_scores():
    # Test that None values in expected_scores are rejected
    y_true = [1.0, 2.0, None, 4.0, 5.0]
    y_pred = [1.1, 1.9, 3.2, 3.8, 5.1]

    with pytest.raises(ValueError, match="expected_scores must not contain None or NaN values"):
        calculate_regression_metrics(y_true, y_pred)


def test_regression_metrics_rejects_nan_expected_scores():
    # Test that NaN values in expected_scores are rejected
    y_true = np.array([1.0, 2.0, np.nan, 4.0, 5.0], dtype=np.float32)
    y_pred = np.array([1.1, 1.9, 3.2, 3.8, 5.1], dtype=np.float32)

    with pytest.raises(ValueError, match="expected_scores must not contain None or NaN values"):
        calculate_regression_metrics(y_true, y_pred)


def test_regression_metrics_all_predictions_none():
    # Test with all predictions being None
    y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_pred = [None, None, None, None, None]

    metrics = calculate_regression_metrics(y_true, y_pred)

    # When all predictions are None, coverage should be 0.0 and all metrics should be 0.0
    assert metrics.coverage == 0.0
    assert metrics.mse == 0.0
    assert metrics.rmse == 0.0
    assert metrics.mae == 0.0
    assert metrics.r2 == 0.0
    assert metrics.explained_variance == 0.0
    assert metrics.loss == 0.0
    assert metrics.anomaly_score_mean is None
    assert metrics.anomaly_score_median is None
    assert metrics.anomaly_score_variance is None


def test_regression_metrics_all_predictions_nan():
    # Test with all predictions being NaN
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
    y_pred = np.array([np.nan, np.nan, np.nan, np.nan, np.nan], dtype=np.float32)

    metrics = calculate_regression_metrics(y_true, y_pred)

    # When all predictions are NaN, coverage should be 0.0 and all metrics should be 0.0
    assert metrics.coverage == 0.0
    assert metrics.mse == 0.0
    assert metrics.rmse == 0.0
    assert metrics.mae == 0.0
    assert metrics.r2 == 0.0
    assert metrics.explained_variance == 0.0
    assert metrics.loss == 0.0
    assert metrics.anomaly_score_mean is None
    assert metrics.anomaly_score_median is None
    assert metrics.anomaly_score_variance is None


def test_roc_auc_handles_missing_classes_in_y_true():
    """Test that ROC AUC is calculated with filtering when test set has fewer classes than model predictions."""
    # Model trained on classes [0, 1, 2], but test set only has [0, 1]
    y_true = np.array([0, 1, 0, 1])
    y_score = np.array(
        [
            [0.7, 0.2, 0.1],  # Predicts class 0
            [0.1, 0.8, 0.1],  # Predicts class 1
            [0.6, 0.3, 0.1],  # Predicts class 0
            [0.2, 0.7, 0.1],  # Predicts class 1
        ]
    )

    metrics = calculate_classification_metrics(y_true, y_score)

    # Should calculate ROC AUC by filtering to classes [0, 1]
    assert metrics.roc_auc is not None
    assert metrics.roc_auc == 1.0
    assert any("computed only on classes present" in w for w in metrics.warnings)
    # Other metrics should still work
    assert metrics.accuracy == 1.0
    assert metrics.f1_score == 1.0
    assert metrics.loss is not None


def test_roc_auc_with_all_classes_present():
    """Test that ROC AUC works when all classes are present in test set."""
    # Model trained on classes [0, 1, 2], test set has all three
    y_true = np.array([0, 1, 2, 0, 1, 2])
    y_score = np.array(
        [
            [0.9, 0.05, 0.05],  # Predicts class 0
            [0.1, 0.8, 0.1],  # Predicts class 1
            [0.1, 0.1, 0.8],  # Predicts class 2
            [0.7, 0.2, 0.1],  # Predicts class 0
            [0.2, 0.7, 0.1],  # Predicts class 1
            [0.1, 0.2, 0.7],  # Predicts class 2
        ]
    )

    metrics = calculate_classification_metrics(y_true, y_score, multi_class="ovr")

    # ROC AUC should be calculated when all classes present
    assert metrics.roc_auc is not None
    assert metrics.accuracy == 1.0
    assert metrics.f1_score == 1.0


def test_roc_auc_handles_subset_of_many_classes():
    """Test ROC AUC where model knows 15 classes, test has 10."""
    # Simulate the actual error scenario from the bug report
    num_model_classes = 15
    num_test_classes = 10
    num_samples = 50

    # Test set only uses classes 0-9
    y_true = np.random.randint(0, num_test_classes, size=num_samples)

    # Model produces predictions for all 15 classes
    y_score = np.random.rand(num_samples, num_model_classes)
    y_score = y_score / y_score.sum(axis=1, keepdims=True)  # Normalize to probabilities

    metrics = calculate_classification_metrics(y_true, y_score, multi_class="ovr")

    # Should calculate ROC AUC by filtering to classes 0-9
    assert metrics.roc_auc is not None
    assert 0.0 <= metrics.roc_auc <= 1.0
    assert any("computed only on classes present" in w for w in metrics.warnings)
    # Other metrics should still work
    assert metrics.accuracy is not None
    assert metrics.f1_score is not None
    assert metrics.loss is not None


def test_roc_auc_handles_unknown_classes_in_y_true():
    """Test that metrics handle when y_true contains classes not in y_score."""
    # Model trained on classes [0, 1, 2], but test set has class 3
    y_true = np.array([0, 1, 2, 3])
    y_score = np.array(
        [
            [0.7, 0.2, 0.1],
            [0.1, 0.8, 0.1],
            [0.1, 0.1, 0.8],
            [0.3, 0.4, 0.3],  # Unknown class 3
        ]
    )

    metrics = calculate_classification_metrics(y_true, y_score)

    # Should skip ROC AUC and loss when unknown classes present
    assert metrics.roc_auc is None
    assert metrics.loss is None  # Loss also skipped to avoid ValueError
    assert any("unknown" in w for w in metrics.warnings)
    # Other metrics should still work (they handle extra classes)
    assert metrics.accuracy is not None
    assert metrics.f1_score is not None


def test_roc_auc_handles_zero_probability_on_present_classes():
    """Test ROC AUC when a sample has zero probability on all present classes (edge case for renormalization)."""
    # Model trained on classes [0, 1, 2, 3], test set only has [0, 1, 2]
    # One sample has ALL probability mass on excluded class 3 (zero on [0, 1, 2])
    y_true = np.array([0, 1, 2, 0, 1, 2])
    y_score = np.array(
        [
            [0.7, 0.2, 0.08, 0.02],
            [0.1, 0.8, 0.08, 0.02],
            [0.1, 0.1, 0.78, 0.02],
            [0.6, 0.3, 0.08, 0.02],
            [0.0, 0.0, 0.0, 1.0],  # zero denominator
            [0.1, 0.1, 0.78, 0.02],
        ]
    )

    metrics = calculate_classification_metrics(y_true, y_score, multi_class="ovr")

    # Should still calculate ROC AUC despite zero-denominator case
    # The safe renormalization should prevent NaN/inf
    assert metrics.roc_auc is not None
    assert not np.isnan(metrics.roc_auc)
    assert not np.isinf(metrics.roc_auc)
    assert any("computed only on classes present" in w for w in metrics.warnings)
    assert metrics.accuracy is not None
    assert metrics.f1_score is not None
    assert metrics.loss is not None


def test_roc_auc_skipped_for_single_class():
    """Test that ROC AUC is skipped when only one class is present in y_true."""
    # Model trained on classes [0, 1, 2], but test set only has class 0
    y_true = np.array([0, 0, 0, 0])
    y_score = np.array(
        [
            [0.9, 0.05, 0.05],
            [0.8, 0.1, 0.1],
            [0.85, 0.1, 0.05],
            [0.9, 0.05, 0.05],
        ]
    )

    metrics = calculate_classification_metrics(y_true, y_score)

    # ROC AUC requires at least 2 classes
    assert metrics.roc_auc is None
    assert metrics.accuracy == 1.0
    assert metrics.loss is not None
    assert any("requires at least 2 classes" in w for w in metrics.warnings)


# Confusion Matrix Tests
def test_confusion_matrix_binary_classification():
    y_true = np.array([0, 1, 1, 0, 1])
    y_score = np.array([0.1, 0.9, 0.8, 0.3, 0.2])

    metrics = calculate_classification_metrics(y_true, y_score, include_confusion_matrix=True)

    assert metrics.confusion_matrix is not None
    expected_cm = sklearn.metrics.confusion_matrix(y_true, [0, 1, 1, 0, 0], labels=[0, 1])
    assert metrics.confusion_matrix == expected_cm.tolist()


def test_confusion_matrix_multiclass():
    y_true = np.array([0, 1, 2, 0, 1, 2])
    y_score = np.array(
        [[0.9, 0.1, 0.0], [0.1, 0.8, 0.1], [0.0, 0.1, 0.9], [0.7, 0.2, 0.1], [0.2, 0.7, 0.1], [0.1, 0.1, 0.8]]
    )

    metrics = calculate_classification_metrics(y_true, y_score, include_confusion_matrix=True)

    assert metrics.confusion_matrix is not None
    # All predictions correct
    assert metrics.confusion_matrix == [[2, 0, 0], [0, 2, 0], [0, 0, 2]]


def test_confusion_matrix_with_misclassifications():
    y_true = np.array([0, 1, 2, 0, 1, 2])
    y_score = np.array(
        [[0.9, 0.1, 0.0], [0.1, 0.8, 0.1], [0.1, 0.8, 0.1], [0.2, 0.7, 0.1], [0.2, 0.7, 0.1], [0.1, 0.1, 0.8]]
    )

    metrics = calculate_classification_metrics(y_true, y_score, include_confusion_matrix=True)

    assert metrics.confusion_matrix is not None
    # Class 0: 1 correct (index 0), 1 predicted as class 1 (index 3)
    # Class 1: 2 correct (indices 1, 4)
    # Class 2: 1 predicted as class 1 (index 2), 1 correct (index 5)
    assert metrics.confusion_matrix == [[1, 1, 0], [0, 2, 0], [0, 1, 1]]


def test_confusion_matrix_handles_nan_logits():
    logits = np.array([[np.nan, np.nan], [np.nan, np.nan], [0.1, 0.9], [0.2, 0.8]])
    expected_labels = [0, 1, 0, 1]
    metrics = calculate_classification_metrics(expected_labels, logits, include_confusion_matrix=True)

    # NaN predictions are set to -1, so they won't match any true label
    # Only the last 2 predictions are valid: pred=[1, 1], true=[0, 1]
    assert metrics.confusion_matrix is not None
    # With NaN handling, predictions become [-1, -1, 1, 1]
    # Only position 3 is correct (true=1, pred=1)
    # Position 2 is wrong (true=0, pred=1)
    assert len(metrics.confusion_matrix) == 2  # 2 classes
    assert len(metrics.confusion_matrix[0]) == 2
