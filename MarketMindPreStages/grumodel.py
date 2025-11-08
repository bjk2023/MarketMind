# ===== GRU MODEL - MARKET MIND =====
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt
import tensorflow as tf
from tensorflow import keras
from keras.models import Sequential
from keras.layers import GRU, Dense, Dropout

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Download Apple stock data
print("Downloading stock data...")
data = yf.download("AAPL", start="2022-01-01", end="2025-01-01", auto_adjust=True)
close_prices = data['Close'].values.reshape(-1, 1)

# Split into train/test (80/20)
train_size = int(len(close_prices) * 0.8)
train, test = close_prices[:train_size], close_prices[train_size:]

print(f"Train size: {len(train)}, Test size: {len(test)}")

# Scale the data
scaler = MinMaxScaler(feature_range=(0, 1))
train_scaled = scaler.fit_transform(train)
test_scaled = scaler.transform(test)

# Create sequences
def create_sequences(data, seq_length=60):
    X, y = [], []
    for i in range(seq_length, len(data)):
        X.append(data[i-seq_length:i, 0])
        y.append(data[i, 0])
    return np.array(X), np.array(y)

seq_length = 60
X_train, y_train = create_sequences(train_scaled, seq_length)
X_test, y_test = create_sequences(test_scaled, seq_length)

# Reshape for GRU [samples, time steps, features]
X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

print(f"\nX_train shape: {X_train.shape}")
print(f"X_test shape: {X_test.shape}")

# Build GRU model
print("\n--- Building GRU Model ---")
model = Sequential([
    GRU(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)),
    Dropout(0.2),
    GRU(units=50, return_sequences=False),
    Dropout(0.2),
    Dense(units=25),
    Dense(units=1)
])

model.compile(optimizer='adam', loss='mean_squared_error')

print(model.summary())

# Train the model
print("\n--- Training GRU ---")
history = model.fit(
    X_train, y_train,
    batch_size=32,
    epochs=50,
    validation_split=0.1,
    verbose=1
)

# Make predictions
print("\n--- Making Predictions ---")
predictions_scaled = model.predict(X_test)
predictions = scaler.inverse_transform(predictions_scaled)

# Get actual test values
test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

# Evaluate
rmse = sqrt(mean_squared_error(test_actual, predictions))
mae = mean_absolute_error(test_actual, predictions)
mape = np.mean(np.abs((test_actual - predictions) / test_actual)) * 100

# Calculate directional accuracy
actual_direction = np.diff(test_actual.flatten()) > 0
pred_direction = np.diff(predictions.flatten()) > 0
directional_accuracy = np.mean(actual_direction == pred_direction) * 100

print("\n=== GRU Results ===")
print(f"RMSE: {rmse:.4f}")
print(f"MAE: {mae:.4f}")
print(f"MAPE: {mape:.2f}%")
print(f"Directional Accuracy: {directional_accuracy:.2f}%")

# Plot results
fig, axes = plt.subplots(2, 1, figsize=(12, 10))

# Forecast plot
test_dates = data.index[train_size + seq_length:]
axes[0].plot(test_dates, test_actual, label='Actual', linewidth=2)
axes[0].plot(test_dates, predictions, color='red', label='GRU Predicted', linewidth=2)
axes[0].set_title("Apple Stock Forecast - GRU Model", fontsize=14, fontweight='bold')
axes[0].set_xlabel("Date")
axes[0].set_ylabel("Price ($)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Training history
axes[1].plot(history.history['loss'], label='Training Loss', linewidth=2)
axes[1].plot(history.history['val_loss'], label='Validation Loss', linewidth=2)
axes[1].set_title("Model Training History", fontsize=14, fontweight='bold')
axes[1].set_xlabel("Epoch")
axes[1].set_ylabel("Loss")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('gru_forecast.png', dpi=300, bbox_inches='tight')
plt.show()

# Save predictions to CSV
results_df = pd.DataFrame({
    'Date': test_dates,
    'Actual': test_actual.flatten(),
    'Predicted': predictions.flatten()
})
results_df.to_csv('gru_predictions.csv', index=False)

# Save the model
model.save('gru_model.h5')

print("\nPredictions saved to 'gru_predictions.csv'")
print("Model saved to 'gru_model.h5'")
print("Plot saved to 'gru_forecast.png'")