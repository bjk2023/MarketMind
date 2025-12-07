from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

# Import your LSTM model prediction function
# (You confirmed the name is predict_next_day_price)
from model import predict_next_day_price

app = Flask(__name__)
CORS(app)


# -----------------------------
# Helpers
# -----------------------------

def clean_value(val):
    """Convert numpy values into pure Python floats."""
    try:
        return float(val)
    except:
        return val


# -----------------------------
# Linear Regression Endpoint
# -----------------------------

@app.route('/predict/lr/<string:ticker>')
def predict_stock_lr(ticker):
    """
    Predicts a stock price 7 days into the future using Linear Regression.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")

        if hist.empty or len(hist) < 10:
            return jsonify({"error": "Not enough historical data to predict."}), 404

        hist = hist.reset_index()
        hist["Date"] = pd.to_datetime(hist["Date"].dt.date)
        hist["Date_ordinal"] = hist["Date"].apply(lambda x: x.toordinal())

        X = np.array(hist["Date_ordinal"]).reshape(-1, 1)
        y = np.array(hist["Close"]).reshape(-1, 1)

        model = LinearRegression()
        model.fit(X, y)

        last_date = hist["Date"].iloc[-1]
        future_date = last_date + timedelta(days=7)
        future_date_ordinal = future_date.toordinal()

        prediction = model.predict(np.array([[future_date_ordinal]]))

        return jsonify({
            "ticker": ticker.upper(),
            "model": "Linear Regression",
            "prediction_for_date": future_date.strftime('%Y-%m-%d'),
            "predicted_price": clean_value(prediction[0][0])
        })

    except Exception as e:
        return jsonify({"error": f"Linear Regression model failed: {str(e)}"}), 500


# -----------------------------
# LSTM / GRU Endpoint
# -----------------------------

@app.route('/predict/lstm/<string:ticker>', methods=['GET'])
def predict_stock_lstm(ticker):
    """
    Predicts the next day's stock price using the LSTM/GRU model.
    """
    try:
        ticker = ticker.upper()

        # Call your LSTM model
        prediction = predict_next_day_price(ticker)

        # Fetch recent close to compare
        data = yf.download(ticker, period="1mo")["Close"].values
        if len(data) == 0:
            return jsonify({"error": f"No recent data found for '{ticker}'"}), 404

        last_close = float(data[-1])

        return jsonify({
            "ticker": ticker,
            "model": "LSTM",
            "last_close": last_close,
            "predicted_next_close": prediction,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Stock Price Endpoint
# -----------------------------

@app.route('/stock/<string:ticker>', methods=['GET'])
def get_stock_price(ticker):
    """
    Fetches the most recent closing price.
    """
    try:
        ticker = ticker.upper()
        data = yf.download(ticker, period="1d")["Close"].values

        if len(data) == 0:
            return jsonify({"error": f"No data found for '{ticker}'"}), 404

        return jsonify({
            "ticker": ticker,
            "latest_close_price": float(data[-1])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Run App
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)
