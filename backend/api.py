# To run this file, you need to install Flask, Flask-CORS, yfinance, and pandas:
# pip install Flask Flask-CORS yfinance pandas
import os
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from model import create_dataset, estimate_week, try_today, estimate_new, good_model
from news_fetcher import get_general_news
from ensemble_model import ensemble_predict, calculate_metrics
from professional_evaluation import rolling_window_backtest
from forex_fetcher import get_exchange_rate, get_currency_list

# Initialize the Flask application
app = Flask(__name__)
CORS(app)


# --- NEW: In-memory storage for the watchlist ---
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

@app.route('/predict/<string:ticker>')
def predict_stock(ticker):
    """
    Predicts the next day's closing price for a given stock ticker.
    """
    try:
        # Create dataset for the last 15 days - predicting today's close using past 14
        stock = yf.Ticker(ticker)
        info = stock.info
        df = create_dataset(ticker, period="15d")
        if df.empty:
            return jsonify({"error": "No historical data available."}), 404

        # Predict today's closing price
        current_df = estimate_week(df)
        prediction_df = current_df.tail(6)
        
        # Get the most recent actual close price (not NaN)
        recent_close_df = df[df["Close"].notna()].tail(1)
        recent_close = recent_close_df["Close"].iloc[0] if not recent_close_df.empty else 0
        recent_date = recent_close_df.index[0] if not recent_close_df.empty else current_df.index[0]
        
        # Get the first prediction
        recent_predicted = current_df["Predicted"].iloc[0]

        response = {
            "symbol": info.get('symbol', ticker.upper()),
            "companyName": info.get('longName', 'N/A'),
            "recentDate": recent_date.strftime('%Y-%m-%d'),
            "recentClose": round(float(recent_close), 2),
            "recentPredicted": round(float(recent_predicted), 2),
            "predictions": [
                {"date": date.strftime('%Y-%m-%d'), "predictedClose": round(float(pred), 2)}
                for date, pred in zip(prediction_df.index, prediction_df["Predicted"])
            ]
        }

        return jsonify(response)

    except Exception as e:
        print(f"Error predicting stock {ticker}: {e}")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@app.route('/predict/ensemble/<string:ticker>')
def predict_ensemble(ticker):
    """
    Enhanced prediction using ensemble of multiple ML models (Linear Regression, Random Forest, XGBoost)
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get more data for ML models (1 year)
        df = create_dataset(ticker, period="1y")
        if df.empty or len(df) < 30:
            return jsonify({"error": "Insufficient historical data for ensemble prediction."}), 404
        
        # Get ensemble predictions
        ensemble_preds, individual_preds = ensemble_predict(df, days_ahead=6)
        
        if ensemble_preds is None:
            return jsonify({"error": "Ensemble prediction failed."}), 500
        
        # Get recent data
        recent_close = float(df["Close"].iloc[-1])
        recent_date = df.index[-1]
        
        # Generate future dates
        future_dates = []
        current_date = recent_date
        for i in range(6):
            current_date = current_date + pd.Timedelta(days=1)
            future_dates.append(current_date)
        
        # Format response
        response = {
            "symbol": info.get('symbol', ticker.upper()),
            "companyName": info.get('longName', 'N/A'),
            "recentDate": recent_date.strftime('%Y-%m-%d'),
            "recentClose": round(recent_close, 2),
            "recentPredicted": round(float(ensemble_preds[0]), 2),
            "predictions": [
                {"date": date.strftime('%Y-%m-%d'), "predictedClose": round(float(pred), 2)}
                for date, pred in zip(future_dates, ensemble_preds)
            ],
            "modelBreakdown": {
                model_name: [round(float(p), 2) for p in preds]
                for model_name, preds in individual_preds.items()
            },
            "modelsUsed": list(individual_preds.keys()),
            "ensembleMethod": "weighted_average",
            "confidence": round(95.0 - (np.std(list(individual_preds.values())) * 2), 1) if len(individual_preds) > 1 else 85.0
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in ensemble prediction for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Ensemble prediction failed: {str(e)}"}), 500


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
        "14d": {"period": "14d", "interval": "1d"},
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
        predictions = predict_stock(ticker).get_json()['predictions']
        for pred in predictions:
            chart_data.append({
            "date": pred["date"] + " 00:00:00",
            "open": None,
            "high": None,
            "low": None,
            "close": pred["predictedClose"],
            "volume": None
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

# --- News Endpoint ---

@app.route('/api/news', methods=['GET'])
def news_api():
    """
    API endpoint to fetch general market news.
    """
    try:
        articles = get_general_news()
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch news: {str(e)}"}), 500


@app.route('/evaluate/<string:ticker>')
def evaluate_models(ticker):
    """
    Professional-grade evaluation with rolling window backtesting
    
    Uses 42 fixed features, multiple ML models, and comprehensive metrics
    Returns predictions vs actuals, all metrics, and trading performance
    """
    try:
        test_days = int(request.args.get('test_days', 60))
        retrain_frequency = int(request.args.get('retrain_frequency', 5))
        
        print(f"Running professional evaluation for {ticker}...")
        result = rolling_window_backtest(ticker, test_days=test_days, retrain_frequency=retrain_frequency)
        
        if result is None:
            return jsonify({"error": "Insufficient data for evaluation"}), 404
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Evaluation error for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Evaluation failed: {str(e)}"}), 500


@app.route('/forex/convert')
def forex_convert():
    """
    Convert between two currencies using real-time exchange rates
    Query params: from_currency, to_currency
    """
    try:
        from_currency = request.args.get('from', 'USD').upper()
        to_currency = request.args.get('to', 'EUR').upper()
        
        rate_data = get_exchange_rate(from_currency, to_currency)
        
        if rate_data is None:
            return jsonify({"error": "Could not fetch exchange rate"}), 404
        
        return jsonify(rate_data)
    
    except Exception as e:
        print(f"Forex convert error: {e}")
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500


@app.route('/forex/currencies')
def forex_currencies():
    """
    Get list of available currencies
    """
    try:
        currencies = get_currency_list()
        return jsonify(currencies)
    
    except Exception as e:
        print(f"Forex currencies error: {e}")
        return jsonify({"error": f"Failed to fetch currencies: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)

