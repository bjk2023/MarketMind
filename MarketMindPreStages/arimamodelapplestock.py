# ---- ARIMA MODEL ----
import pandas as pd
import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from math import sqrt

# Download Apple stock data
data = yf.download("AAPL", start="2022-01-01", end="2025-01-01", auto_adjust=True)
close_prices = data['Close']

# Split into train/test
train_size = int(len(close_prices) * 0.8)
train, test = close_prices[:train_size], close_prices[train_size:]

# Fit ARIMA(p,d,q)
model = ARIMA(train, order=(5, 1, 0))  # You can tune (p,d,q)
model_fit = model.fit()

# Forecast for test set length
forecast = model_fit.forecast(steps=len(test))

# Evaluate
rmse = sqrt(mean_squared_error(test, forecast))
print("ARIMA RMSE:", rmse)

# Plot
plt.figure(figsize=(10,5))
plt.plot(test.index, test, label='Actual')
plt.plot(test.index, forecast, color='red', label='Predicted')
plt.title("Apple Stock Forecast (ARIMA)")
plt.legend()
plt.show()
