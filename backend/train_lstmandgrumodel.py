import yfinance as yf
import numpy as np
import pandas as pd
import os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, GRU, Dense
from sklearn.preprocessing import MinMaxScaler

def train_model_for_ticker(ticker):
    ticker = ticker.upper()
    print(f"Training model for {ticker}...")

    # Download 5 years of closing price
    data = yf.download(ticker, period="5y")
    if data.empty:
        raise ValueError("No data found for ticker.")

    close_prices = data["Close"].values.reshape(-1, 1)

    # Scale data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(close_prices)

    # Create sequences
    X, y = [], []
    sequence_length = 60

    for i in range(sequence_length, len(scaled)):
        X.append(scaled[i-sequence_length:i, 0])
        y.append(scaled[i, 0])

    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    # Build model (LSTM + GRU hybrid)
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(X.shape[1], 1)),
        GRU(32),
        Dense(1)
    ])

    model.compile(optimizer="adam", loss="mse")
    model.fit(X, y, epochs=10, batch_size=32, verbose=1)

    # Save model
    os.makedirs("models", exist_ok=True)
    model.save(f"models/{ticker}.keras")

    # Save scaler
    np.save(f"models/{ticker}_scaler.npy", scaler.min_)
    np.save(f"models/{ticker}_scale.npy", scaler.scale_)

    return True


def predict_next_day_price(ticker):
    import tensorflow as tf

    ticker = ticker.upper()
    model_path = f"models/{ticker}.keras"  # updated to .keras
    scaler_min_path = f"models/{ticker}_scaler.npy"
    scaler_scale_path = f"models/{ticker}_scale.npy"

    if not os.path.exists(model_path):
        # Train if model doesn't exist
        train_model_for_ticker(ticker)

    # Load the Keras model
    model = tf.keras.models.load_model(model_path)

    # Load scaler parameters
    scaler_min = np.load(scaler_min_path)
    scaler_scale = np.load(scaler_scale_path)

    scaler = MinMaxScaler()
    scaler.min_ = scaler_min
    scaler.scale_ = scaler_scale

    # Download most recent data for prediction
    data = yf.download(ticker, period="2y")["Close"].values.reshape(-1, 1)
    scaled = scaler.transform(data)

    # Take last 60 days for input
    last_60 = scaled[-60:].reshape(1, 60, 1)
    prediction_scaled = model.predict(last_60)
    prediction = scaler.inverse_transform(prediction_scaled)[0][0]

    return float(prediction)
