# To run this file, you need to install Flask, Flask-CORS, yfinance, and pandas:
# pip install Flask Flask-CORS yfinance pandas

import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model


# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# --- In-memory storage for the watchlist ---
# Using a set to automatically prevent duplicate tickers
watchlist = set()

# --- Watchlist Endpoints ---

@app.route('/watchlist', methods=['GET'])
def get_watchlist():
    """Returns the list of tickers in the watchlist."""
    return jsonify(list(watchlist))

@app.route('/watchlist/<string:ticker>', methods=['POST'])
def add_to_watchlist(ticker):
    """Adds a ticker to the watchlist."""
    ticker = ticker.upper()
    watchlist.add(ticker)
    return jsonify({"message": f"{ticker} added to watchlist.", "watchlist": list(watchlist)}), 201

@app.route('/watchlist/<string:ticker>', methods=['DELETE'])
def remove_from_watchlist(ticker):
    """Removes a ticker from the watchlist."""
    ticker = ticker.upper()
    watchlist.discard(ticker) # Use discard to avoid errors if ticker not found
    return jsonify({"message": f"{ticker} removed from watchlist.", "watchlist": list(watchlist)})

# --- Stock Data Endpoints ---

@app.route('/stock/<string:ticker>')
def get_stock_data(ticker):
    """
    This function handles requests for a specific stock ticker using yfinance.
    It fetches company info and formats it for the frontend data card.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if info.get('regularMarketPrice') is None:
            return jsonify({"error": f"Invalid ticker symbol '{ticker}' or no data available."}), 404

        price = info.get('regularMarketPrice', 0)
        previous_close = info.get('previousClose', price)
        change = price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close else 0

        market_cap_int = info.get('marketCap', 0)
        if market_cap_int >= 1_000_000_000_000:
            market_cap_formatted = f"{market_cap_int / 1_000_000_000_000:.2f}T"
        elif market_cap_int > 0:
            market_cap_formatted = f"{market_cap_int / 1_000_000_000:.2f}B"
        else:
            market_cap_formatted = "N/A"

        formatted_data = {
            "symbol": info.get('symbol', ticker.upper()),
            "companyName": info.get('longName', 'N/A'),
            "price": price,
            "change": change,
            "changePercent": change_percent,
            "marketCap": market_cap_formatted,
            "peRatio": info.get('trailingPE') or "N/A",
            "week52High": info.get('fiftyTwoWeekHigh', 0),
            "week52Low": info.get('fiftyTwoWeekLow', 0),
        }
        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/chart/<string:ticker>')
def get_chart_data(ticker):
    """
    This function gets historical data for the chart using yfinance.
    It now accepts a 'period' query parameter to fetch different time frames.
    """
    period = request.args.get('period', '6mo')

    period_interval_map = {
        "1d": {"period": "1d", "interval": "5m"},
        "5d": {"period": "5d", "interval": "15m"},
        "1mo": {"period": "1mo", "interval": "1d"},
        "6mo": {"period": "6mo", "interval": "1d"},
        "1y": {"period": "1y", "interval": "1d"},
    }

    params = period_interval_map.get(period)
    if not params:
        return jsonify({"error": "Invalid time frame specified."}), 400

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=params["period"], interval=params["interval"])

        if hist.empty:
            return jsonify({"error": "Could not retrieve time series data for the selected period."}), 404

        chart_data = []
        for index, row in hist.iterrows():
            chart_data.append({
                "date": index.strftime('%Y-%m-%d %H:%M:%S'),
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
                "volume": row['Volume']
            })

        return jsonify(chart_data)

    except Exception as e:
        return jsonify({"error": f"An error occurred while fetching chart data: {str(e)}"}), 500

# --- Paper Trading Endpoints ---

paper_portfolio = {
    "cash": 100000.0,
    "positions": {}  # {ticker: {"shares": 0, "avg_cost": 0}}
}


@app.route('/paper/portfolio', methods=['GET'])
def get_paper_portfolio():
    """Return the current state of the paper trading portfolio."""
    data = {"cash": paper_portfolio["cash"], "positions": []}

    for ticker, pos in paper_portfolio["positions"].items():
        stock = yf.Ticker(ticker)
        price = stock.info.get('regularMarketPrice', 0)
        prev_close = stock.info.get('previousClose', price)

        current_value = pos["shares"] * price
        cost_basis = pos["shares"] * pos["avg_cost"]
        daily_pl = pos["shares"] * (price - prev_close)
        total_pl = current_value - cost_basis

        data["positions"].append({
            "ticker": ticker,
            "shares": pos["shares"],
            "avg_cost": pos["avg_cost"],
            "current_price": price,
            "daily_pl": daily_pl,
            "total_pl": total_pl
        })

    return jsonify(data)


@app.route('/paper/buy', methods=['POST'])
def buy_stock():
    """Simulate buying shares in the paper trading account."""
    data = request.get_json()
    ticker = data.get('ticker', '').upper()
    shares = int(data.get('shares', 0))
    if shares <= 0:
        return jsonify({"error": "Shares must be positive"}), 400

    stock = yf.Ticker(ticker)
    price = stock.info.get('regularMarketPrice')
    if price is None:
        return jsonify({"error": f"Invalid ticker: {ticker}"}), 404

    total_cost = shares * price
    if total_cost > paper_portfolio["cash"]:
        return jsonify({"error": "Insufficient cash"}), 400

    pos = paper_portfolio["positions"].get(ticker, {"shares": 0, "avg_cost": 0})
    new_total_shares = pos["shares"] + shares
    new_avg_cost = ((pos["avg_cost"] * pos["shares"]) + total_cost) / new_total_shares

    paper_portfolio["positions"][ticker] = {"shares": new_total_shares, "avg_cost": new_avg_cost}
    paper_portfolio["cash"] -= total_cost

    return jsonify({"message": f"Bought {shares} {ticker} at ${price:.2f}"}), 200


@app.route('/paper/sell', methods=['POST'])
def sell_stock():
    """Simulate selling shares."""
    data = request.get_json()
    ticker = data.get('ticker', '').upper()
    shares = int(data.get('shares', 0))
    if shares <= 0:
        return jsonify({"error": "Shares must be positive"}), 400

    pos = paper_portfolio["positions"].get(ticker)
    if not pos or pos["shares"] < shares:
        return jsonify({"error": "Not enough shares"}), 400

    stock = yf.Ticker(ticker)
    price = stock.info.get('regularMarketPrice', 0)

    proceeds = shares * price
    pos["shares"] -= shares
    if pos["shares"] == 0:
        del paper_portfolio["positions"][ticker]
    paper_portfolio["cash"] += proceeds

    return jsonify({"message": f"Sold {shares} {ticker} at ${price:.2f}"}), 200

# --- LSTM/GRU Prediction Endpoint ---

from train_lstmandgrumodel import predict_next_day_price
import yfinance as yf
from flask import jsonify

@app.route('/predict/<string:ticker>', methods=['GET'])
def predict_stock(ticker):
    """
    Predict next-day closing price using pre-trained LSTM/GRU model.
    If the model for the ticker doesn't exist, it will be trained automatically.
    """
    try:
        ticker = ticker.upper()

        # Get predicted next-day price
        prediction = predict_next_day_price(ticker)

        # Get last close price for reference
        data = yf.download(ticker, period="1mo")["Close"].values
        if len(data) == 0:
            return jsonify({"error": f"No recent data found for ticker '{ticker}'"}), 404

        last_close = float(data[-1])

        return jsonify({
            "ticker": ticker,
            "last_close": last_close,
            "predicted_next_close": prediction
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)

