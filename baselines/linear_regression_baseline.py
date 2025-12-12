"""
Linear Regression Baseline for MarketMind

Purpose:
- Provide a simple, interpretable baseline for stock prediction.
- Compare against MarketMind models using the same evaluation metrics.

Notes:
- This script is intentionally minimal and uses a toy dataset generator by default.
- Replace the toy data with real OHLCV or returns data when available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

try:
    from sklearn.linear_model import LinearRegression
except ImportError as e:
    raise SystemExit(
        "Missing dependency: scikit-learn. Install with:\n"
        "  pip install scikit-learn\n"
    ) from e


@dataclass
class ToyDataConfig:
    n_points: int = 300
    lookback: int = 10
    noise_std: float = 0.5
    seed: int = 42


def make_toy_price_series(cfg: ToyDataConfig) -> np.ndarray:
    """
    Generates a toy price series with trend + seasonality + noise.
    This is only for proving the pipeline works end-to-end.
    """
    rng = np.random.default_rng(cfg.seed)
    t = np.arange(cfg.n_points)

    trend = 0.03 * t
    seasonality = 2.0 * np.sin(2 * np.pi * t / 30.0)
    noise = rng.normal(0, cfg.noise_std, size=cfg.n_points)

    price = 100 + trend + seasonality + noise
    return price


def make_supervised_windows(prices: np.ndarray, lookback: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Converts a 1D price series into supervised learning windows:
      X[i] = prices[i : i+lookback]
      y[i] = prices[i+lookback]
    """
    if lookback < 1:
        raise ValueError("lookback must be >= 1")
    if len(prices) <= lookback:
        raise ValueError("prices length must be > lookback")

    X, y = [], []
    for i in range(len(prices) - lookback):
        X.append(prices[i : i + lookback])
        y.append(prices[i + lookback])

    return np.asarray(X, dtype=float), np.asarray(y, dtype=float)


def train_test_split_time_series(X: np.ndarray, y: np.ndarray, train_frac: float = 0.8):
    """
    Time-series split (no shuffling).
    """
    if not (0.1 < train_frac < 0.95):
        raise ValueError("train_frac should be between 0.1 and 0.95")

    n = len(X)
    split = int(n * train_frac)
    return X[:split], X[split:], y[:split], y[split:]


def main() -> None:
    cfg = ToyDataConfig()
    prices = make_toy_price_series(cfg)
    X, y = make_supervised_windows(prices, lookback=cfg.lookback)
    X_train, X_test, y_train, y_test = train_test_split_time_series(X, y, train_frac=0.8)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    # Minimal evaluation (full metrics live in evaluation/evaluate.py)
    mae = float(np.mean(np.abs(y_pred - y_test)))
    rmse = float(np.sqrt(np.mean((y_pred - y_test) ** 2)))

    # Directional accuracy: compare predicted change vs actual change
    # Use last value of each input window as "current" price
    current = X_test[:, -1]
    actual_change = y_test - current
    pred_change = y_pred - current
    directional_acc = float(np.mean((actual_change >= 0) == (pred_change >= 0)))

    print("=== Linear Regression Baseline (Toy Data) ===")
    print(f"Lookback window: {cfg.lookback}")
    print(f"Test points:     {len(y_test)}")
    print(f"MAE:             {mae:.4f}")
    print(f"RMSE:            {rmse:.4f}")
    print(f"Directional Acc: {directional_acc:.4f}")


if __name__ == "__main__":
    main()
