# ===== ARIMA MODEL - APPLE STOCK =====
import pandas as pd
import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
import matplotlib
matplotlib.use('Agg')  # disable GUI pop-up
import matplotlib.pyplot as plt
from math import sqrt
import os

# ----- File paths -----
save_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(save_dir, "arima_predictions.csv")
plot_path = os.path.join(save_dir, "arima_plot.png")

# ----- Download Apple stock data -----
data = yf.download("AAPL", start="2022-01-01", end="2025-01-01", auto_adjust=True)
close_prices = data['Close']
close_prices.index = pd.to_datetime(close_prices.index)

# ----- Handle missing data -----
close_prices = close_prices.asfreq('B')  # business day frequency
close_prices = close_prices.ffill()      # forward-fill NaNs

# ----- Split train/test -----
train_size = int(len(close_prices) * 0.8)
train, test = close_prices[:train_size], close_prices[train_size:]

# ----- Fit ARIMA -----
model = ARIMA(train, order=(5, 1, 0))
model_fit = model.fit()

# ----- Forecast -----
forecast_result = model_fit.get_forecast(steps=len(test))
forecast = forecast_result.predicted_mean
conf_int = forecast_result.conf_int()

# ----- Align forecast/test -----
forecast = forecast.loc[test.index].dropna()
test = test.loc[forecast.index].dropna()

# ----- Evaluate -----
rmse = sqrt(mean_squared_error(test.values, forecast.values))
print(f"ARIMA RMSE: {rmse:.4f}")

# ----- Plot -----
plt.figure(figsize=(10,5))
plt.plot(train.index, train, label='Train')
plt.plot(test.index, test, label='Actual')
plt.plot(test.index, forecast, color='red', label='Predicted')
plt.fill_between(test.index, conf_int.iloc[:,0], conf_int.iloc[:,1], color='pink', alpha=0.3)
plt.title("Apple Stock Forecast (ARIMA)")
plt.legend()
plt.tight_layout()
plt.savefig(plot_path)
print(f"📊 Plot saved to: {plot_path}")

# ----- Save CSV with proper columns -----
forecast_df = pd.DataFrame({
    "Actual": test.values.ravel(),
    "Predicted": forecast.values.ravel()
})
forecast_df.to_csv(csv_path, index=False)
print(f"✅ ARIMA predictions saved to: {csv_path}")
print(f"📁 Does it exist? {os.path.exists(csv_path)}")
