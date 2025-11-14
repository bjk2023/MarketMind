# ---- LSTM MODEL ----
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # disable GUI plot windows (prevents crash)
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import os

# ----- File paths -----
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "lstm_predictions.csv")
plot_path = os.path.join(base_dir, "lstm_plot.png")

# ----- Download Apple stock data -----
data = yf.download("AAPL", start="2022-01-01", end="2025-01-01", auto_adjust=True)
close_prices = data['Close'].values.reshape(-1, 1)

# ----- Normalize -----
scaler = MinMaxScaler(feature_range=(0,1))
scaled_data = scaler.fit_transform(close_prices)

# ----- Prepare training data (80% train) -----
train_size = int(len(scaled_data) * 0.8)
train_data = scaled_data[:train_size]
test_data = scaled_data[train_size - 60:]  # include lookback window overlap

# ----- Create sequences -----
def create_sequences(dataset, lookback=60):
    X, y = [], []
    for i in range(lookback, len(dataset)):
        X.append(dataset[i-lookback:i, 0])
        y.append(dataset[i, 0])
    return np.array(X), np.array(y)

X_train, y_train = create_sequences(train_data)
X_test, y_test = create_sequences(test_data)

# ----- Reshape for LSTM input -----
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

# ----- Build LSTM model -----
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
model.add(LSTM(50))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mean_squared_error')

# ----- Train model -----
model.fit(X_train, y_train, epochs=20, batch_size=32, verbose=1)

# ----- Predictions -----
predicted = model.predict(X_test)
predicted_prices = scaler.inverse_transform(predicted)
actual_prices = scaler.inverse_transform(y_test.reshape(-1,1))

# ----- Save predictions to CSV -----
df_pred = pd.DataFrame({
    "Actual_Close": actual_prices.flatten(),
    "Predicted_Close": predicted_prices.flatten()
})
df_pred.to_csv(csv_path, index=False)
print(f"✅ LSTM predictions saved to: {csv_path}")

# ----- Plot and save -----
plt.figure(figsize=(10,5))
plt.plot(actual_prices, label='Actual')
plt.plot(predicted_prices, color='red', label='Predicted')
plt.title("Apple Stock Forecast (LSTM)")
plt.legend()
plt.tight_layout()
plt.savefig(plot_path)
print(f"📊 LSTM plot saved to: {plot_path}")
