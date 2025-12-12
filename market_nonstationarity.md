# Market Non-Stationarity and Model Degradation

Financial markets are non-stationary, meaning their statistical properties change over time. Relationships between variables that hold in one period may break down in another due to economic shifts, policy changes, or unexpected events.

---

## What Is Non-Stationarity?

A stationary process has constant mean, variance, and autocorrelation over time. Stock prices violate these assumptions due to:
- Regime changes
- Market shocks
- Behavioral shifts
- Technological and regulatory changes

This makes long-term prediction especially challenging.

---

## Impact on Linear Regression

Linear regression assumes a fixed relationship between inputs and outputs. In non-stationary environments, this assumption causes models to degrade rapidly as conditions change.

As a result, linear regression often:
- Overfits historical regimes
- Lags during turning points
- Requires frequent retraining

---

## MarketMind’s Approach

MarketMind is designed with non-stationarity in mind. By incorporating richer features and machine learning models capable of adaptation, the system aims to remain robust across changing market conditions.

This design choice prioritizes long-term usefulness over short-lived performance on historical data.
