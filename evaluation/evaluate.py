"""
Evaluation utilities for MarketMind.

This module defines common metrics so all models (baselines + ML models)
are evaluated consistently.

Key metrics:
- MAE
- RMSE
- Directional Accuracy
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


@dataclass
class EvalResults:
    mae: float
    rmse: float
    directional_accuracy: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "mae": self.mae,
            "rmse": self.rmse,
            "directional_accuracy": self.directional_accuracy,
        }


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_pred - y_true)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_pred - y_true) ** 2)))


def directional_accuracy(
    y_true_next: np.ndarray,
    y_pred_next: np.ndarray,
    y_current: np.ndarray,
) -> float:
    """
    Directional accuracy measures whether the model correctly predicts up/down movement.

    y_current: the price at the current time (before prediction)
    y_true_next: the actual next price
    y_pred_next: the predicted next price
    """
    y_true_next = np.asarray(y_true_next, dtype=float)
    y_pred_next = np.asarray(y_pred_next, dtype=float)
    y_current = np.asarray(y_current, dtype=float)

    actual_change = y_true_next - y_current
    pred_change = y_pred_next - y_current
    return float(np.mean((actual_change >= 0) == (pred_change >= 0)))


def evaluate_next_step(
    y_true_next: np.ndarray,
    y_pred_next: np.ndarray,
    y_current: np.ndarray,
) -> EvalResults:
    return EvalResults(
        mae=mae(y_true_next, y_pred_next),
        rmse=rmse(y_true_next, y_pred_next),
        directional_accuracy=directional_accuracy(y_true_next, y_pred_next, y_current),
    )


if __name__ == "__main__":
    # Tiny self-test / demo
    y_current = np.array([100, 100, 100, 100], dtype=float)
    y_true = np.array([101, 99, 102, 98], dtype=float)
    y_pred = np.array([100.5, 100.2, 101.0, 97.0], dtype=float)

    results = evaluate_next_step(y_true, y_pred, y_current)
    print("Evaluation Demo:", results.as_dict())
