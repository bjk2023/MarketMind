# ===== PROPHET MODEL - APPLE STOCK =====
import pandas as pd
import yfinance as yf
from prophet import Prophet
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# ----- File paths -----
save_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(save_dir, "prophet_predictions.csv")
plot_path_forecast = os.path.join(save_dir, "prophet_forecast.png")
plot_path_components = os.path.join(save_dir, "prophet_components.png")

# ----- Download Apple stock data -----
data = yf.download("AAPL", start="2022-01-01", end="2025-01-01", group_by="ticker", auto_adjust=True)

# ----- Flatten MultiIndex columns -----
if isinstance(data.columns, pd.MultiIndex):
    data.columns = ['_'.join(col).strip() for col in data.columns.values]

# ----- Detect Close column dynamically -----
close_cols = [c for c in data.columns if 'Close' in c]
if not close_cols:
    raise ValueError(f"No Close column found in data: {data.columns}")
close_col = close_cols[0]  # e.g., 'Close_AAPL'

# ----- Prepare dataframe for Prophet -----
df = data.reset_index()[['Date', close_col]].copy()
df.rename(columns={'Date':'ds', close_col:'y'}, inplace=True)

# ----- Ensure correct types -----
df['ds'] = pd.to_datetime(df['ds'])
df['y'] = pd.to_numeric(df['y'].values.ravel(), errors='coerce')  # ensure 1D
df = df[['ds','y']].dropna()  # remove NaN rows

# ----- Fit Prophet -----
model = Prophet(daily_seasonality=True)
model.fit(df)

# ----- Forecast existing dates -----
future = df[['ds']].copy()
forecast = model.predict(future)

# ----- Save CSV with Actual + Predicted -----
results_df = pd.DataFrame({
    "Actual": df['y'].values.ravel(),
    "Predicted": forecast['yhat'].values.ravel()
})
results_df.to_csv(csv_path, index=False)
print(f"✅ Prophet predictions saved to: {csv_path}")

# ----- Plot forecast and components -----
model.plot(forecast).savefig(plot_path_forecast)
model.plot_components(forecast).savefig(plot_path_components)
print(f"📊 Forecast plot saved to: {plot_path_forecast}")
print(f"📊 Components plot saved to: {plot_path_components}")
