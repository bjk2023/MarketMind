# Evaluation Metrics for Stock Price Prediction

Accurately evaluating stock prediction models requires more than a single error metric. Financial time series are noisy, non-stationary, and often evaluated based on decision quality rather than exact price accuracy. This document outlines the evaluation metrics used to compare MarketMind against traditional baselines such as linear regression.

---

## Root Mean Squared Error (RMSE)

RMSE measures the average magnitude of prediction error by penalizing large deviations more heavily than small ones. It is defined as:

RMSE = sqrt( (1 / n) * Σ (y_pred - y_true)² )

RMSE is useful for understanding overall numerical accuracy but has limitations in financial settings, as small absolute errors may still result in poor trading decisions.

---

## Mean Absolute Error (MAE)

MAE computes the average absolute difference between predicted and true values. Unlike RMSE, it does not disproportionately penalize outliers.

MAE provides a more interpretable measure of typical error but still fails to capture whether predictions correctly anticipate market direction.

---

## Directional Accuracy

Directional accuracy measures how often a model correctly predicts the direction of price movement (up or down), regardless of magnitude.

This metric is especially important for stock prediction systems like MarketMind, where anticipating trend direction is often more valuable than predicting exact prices.

---

## Why Multiple Metrics Matter

A model with low RMSE but poor directional accuracy may still be ineffective in practice. MarketMind emphasizes a multi-metric evaluation approach to ensure models are both numerically accurate and decision-relevant.

Linear regression often performs acceptably on RMSE during stable periods but struggles with directional accuracy during volatile markets. This motivates the use of machine learning models that can adapt to nonlinear patterns.
