# Copyright (c) 2024–2025, Daily. BSD-2-Clause.
# Extracted without algorithm changes from the pinned Pipecat benchmark.py.
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def compute_metrics_with_confusion(probs: np.ndarray, labels: np.ndarray):
    """Compute metrics including false positive and false negative rates."""
    preds = (probs > 0.5).astype(int)
    false_positives = np.sum((preds == 1) & (labels == 0))
    false_negatives = np.sum((preds == 0) & (labels == 1))
    total = len(labels)
    return {'sample_count': int(total), 'accuracy': float(accuracy_score(labels, preds)) * 100, 'precision': float(precision_score(labels, preds, zero_division=0)), 'recall': float(recall_score(labels, preds, zero_division=0)), 'f1': float(f1_score(labels, preds, zero_division=0)), 'false_positive_rate': float(false_positives / total) * 100 if total > 0 else 0.0, 'false_negative_rate': float(false_negatives / total) * 100 if total > 0 else 0.0}
